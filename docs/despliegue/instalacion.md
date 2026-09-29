# Instalación de Zabbix 7.4 en el servidor (zabbix.likson.com)

> **Cuándo:** para instalar desde cero. Para recuperar un servidor perdido o migrar otro Zabbix, ver [restauración y migración](restauracion-y-migracion.md). Para el día a día del servidor, [mantenimiento](mantenimiento.md).

Stack: PostgreSQL + Zabbix server + frontend Nginx con HTTPS (Let's Encrypt) + Agent 2 (automonitoreo) + SNMP traps + web service (informes).

| Fichero | Función |
|---|---|
| `docker-compose.yml` | Servicios del stack; los complementarios usan el perfil `postgres-nginx` |
| `compose_server.yaml` | Personalizaciones: puertos, volúmenes, agente en red host, HTTPS, traps |
| `server.env.example` | Variables del despliegue (versión, dominio, puertos, retención) |
| `env_vars/.env_*_override` | Variables de Zabbix: zona horaria, traps, agente, informes |
| `nginx/zabbix_http.conf` | HTTP: solo el reto ACME y la redirección a HTTPS |
| `server_setup.sh` | Preparación inicial y captura segura de secretos |
| `server_letsencrypt.sh` | Emisión y renovación del certificado |
| `server_backup.sh` | Respaldo de la BD y de la configuración que no está en git |
| `server_restore.sh` | Restauración desde un respaldo o migración de la BD de una implementación anterior |
| `zabbix_agentd.d/sensors_hwmon.*` | UserParameters del Agent 2 para las temperaturas del host |
| `zabbix_templates/*.yaml` | Plantillas propias (ver [catálogo](../operacion/plantillas.md)) |
| `zabbix_media/` | Script del webhook de Telegram y plantillas de mensaje de Telegram y Gmail ([alertas](../operacion/alertas.md)) |
| `zabbix_dashboards/*.json` | Definición del dashboard "Likson NOC" ([dashboard](../operacion/dashboard.md)) |
| `agents/scripts/` | Scripts de la API de Zabbix para operar sin la interfaz ([README](../../agents/scripts/README.md)) |
| `AGENTS.md`, `CLAUDE.md` | Reglas para agentes que modifican el proyecto o la producción |
| `docs/` | Esta documentación ([índice](../README.md)) |

## Requisitos

- Linux con Docker Engine y `docker compose` >= 2.24, `openssl` y `sudo`.
- Registro DNS A `zabbix.likson.com` apuntando a la IP pública del servidor.
- Puertos abiertos: `80/tcp` (reto ACME y redirección), `443/tcp` (web), `162/udp` (traps desde cualquier red) y `10051/tcp` (agentes remotos).
- Salida desde el servidor hacia `10050/tcp` de los agentes remotos (checks pasivos) y `161/udp` de los equipos SNMP.
- En el host no debe haber otro agente de Zabbix usando el puerto 10050.

## 0. Antes de empezar: elegir el camino

| Situación | Camino |
|---|---|
| Servidor nuevo, sin datos previos que conservar | Secciones 1 a 5 de este documento, y después la [configuración base](configuracion-base.md) |
| Este despliegue se perdió (disco, servidor) y hay respaldos de `server_backup.sh` | [Restauración](restauracion-y-migracion.md#restauración) |
| Ya existe **otra implementación de Zabbix** (en este servidor o en otro) y se quieren conservar sus datos | [Migración desde una implementación anterior](restauracion-y-migracion.md#migración-desde-una-implementación-anterior), luego secciones 2 a 5 |

Antes de instalar en un servidor que ya tuvo Zabbix, revisar qué queda:

```sh
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker network ls
docker volume ls
```

Las redes `*_frontend`, `*_backend` y `*_tools_frontend` de otra instalación usan las mismas subredes (`172.16.238-240.0/24`), y otro contenedor web puede estar ocupando los puertos 80 y 443. El nuevo stack no arranca hasta que se eliminen, **después** de respaldar sus datos si se van a conservar.

## 1. Clonar y preparar

Como usuario normal con sudo (no como root):

```sh
git clone -b server-deploy git@github.com:josejesusrl/zabbix-docker.git zabbix-docker
cd zabbix-docker
./server_setup.sh
```

El script pide, sin mostrarlos en pantalla:
- **Contraseña de PostgreSQL.** Si se deja vacía, se genera una aleatoria. Solo se aplica antes de que se cree la base de datos.
- **E-mail para la cuenta de Let's Encrypt.** Es el contacto de la cuenta. Let's Encrypt ya **no** envía avisos de caducidad; la caducidad la vigila Zabbix (sección 4).
- **Comunidad SNMP de traps.** Si se deja vacía, se genera una y se muestra **una sola vez**. Solo se aceptan caracteres `A-Z a-z 0-9 . _ -`.

También ofrece instalar **lm-sensors** (apt, dnf o yum) y ejecuta `sensors-detect --auto`. Si los módulos de sensores recién detectados no aparecen en `sensors`, reiniciar el host. En una máquina virtual normalmente no hay sensores.

## 2. Arrancar y emitir el certificado

```sh
docker compose --env-file .env --env-file server.env up -d
sudo ./server_letsencrypt.sh issue
```

Hasta emitir el certificado, todo lo que llega por HTTP se redirige a HTTPS, que todavía no responde. Es normal.

Si Let's Encrypt todavía no puede validar (puertos 80/443 sin redirigir en el NAT), instalar un certificado autofirmado temporal para usar la web en la LAN:

```sh
sudo ./server_letsencrypt.sh selfsigned
```

El navegador mostrará un aviso. Cuando los puertos estén redirigidos, `sudo ./server_letsencrypt.sh issue` lo reemplaza.

Alias recomendado:
```sh
alias zbx='docker compose --env-file .env --env-file server.env'
```

## 3. Firewall del host

Docker publica los puertos saltándose ufw/firewalld; los puertos 80, 443, 162/udp y 10051 quedan abiertos a propósito.

El Agent 2 usa la red del host, así que el firewall del host **sí** le afecta. Hay que permitir los checks pasivos desde el contenedor del server:

```sh
sudo ufw allow from 172.16.238.0/24 to any port 10050 proto tcp
```

## 4. Configuración en la interfaz web

En `https://zabbix.likson.com` (en la LAN, `https://192.168.0.191`).

1. Entrar con `Admin` / `zabbix` y **cambiar la contraseña** de inmediato.
2. *Data collection → Hosts → Zabbix server*: cambiar la interfaz Agent a IP `172.16.238.1`, puerto `10050`.
   - Plantillas: `Linux by Zabbix agent` y `Zabbix server health` (vienen enlazadas). Opcional: `Docker by Zabbix agent 2` para ver los contenedores del stack.
   - **Sistemas de archivos:** el agente ve los discos del host bajo `/rootfs`. Hay que añadir estas macros en el host (pestaña *Macros*); si no, también se descubren los montajes internos del contenedor (`/etc/hosts`, `/var/lib/zabbix/*`…) como discos duplicados:
     ```
     {$VFS.FS.FSNAME.MATCHES}     = ^/rootfs(/|$)
     {$VFS.FS.FSNAME.NOT_MATCHES} = ^/rootfs/(dev|proc|sys|run|var/lib/docker)(/|$)|/shm$
     ```
   - Estos items leen datos del contenedor y no del host. Se recomienda desactivarlos:
     - `Checksum of /etc/passwd` y su trigger, que nunca se dispararía.
     - `Number of logged in users`, que siempre valdrá 0.
   - **Temperaturas:** importar `zabbix_templates/linux_hwmon_temperature.yaml` en *Data collection → Templates → Import* y enlazarla al host.
     - Descubre cada sensor de `/sys/class/hwmon` (CPU, NVMe, placa…) cada hora.
     - Crea un item por sensor cada minuto, en °C.
     - Triggers: aviso con `{$TEMP.WARN}` (75) y crítico con `{$TEMP.CRIT}` (85). Se pueden ajustar por chip, por ejemplo `{$TEMP.CRIT:"nvme"}=70`.
     - Prueba desde el host: `zbx exec zabbix-agent zabbix_agent2 -t hwmon.temp.discovery`.
3. *Administration → General → Other*: poner `Frontend URL` en `https://zabbix.likson.com/`. Es necesario para los informes PDF.
   - **Caducidad del certificado:** enlazar al host "Zabbix server" la plantilla `Website certificate by Zabbix agent 2` con estas macros de host:
     ```
     {$CERT.WEBSITE.HOSTNAME} = zabbix.likson.com
     {$CERT.WEBSITE.IP}       = 127.0.0.1
     {$CERT.EXPIRY.WARN}      = 14
     ```
     El agente se conecta a `127.0.0.1:443` usando el nombre `zabbix.likson.com`, sin depender del DNS público ni del NAT. Avisa si faltan menos de 14 días, es decir, si `renew` lleva más de 2 semanas fallando. Con el certificado autofirmado el resultado es `valid-but-self-signed` y no genera alerta. Cuando `issue` lo sustituya, cambiará la huella del certificado, algo esperado.
4. **Equipos a monitorear** (routers, switches, APs, servidores), plantillas propias, dependencias, alertas y umbrales: ver la [documentación de operación](../README.md). La configuración que vive solo en la BD (medios, acciones, usuarios, ajustes) está en [configuración base](configuracion-base.md).
   - Los MIBs de fabricantes van en `./zbx_env/var/lib/zabbix/mibs/` (incluidos en el respaldo) y se aplican reiniciando `zabbix-server` y `zabbix-snmptraps`.

## 5. Tareas programadas

`server_setup.sh` instala `/etc/cron.d/zabbix` si no existe: respaldo diario a las 02:30 y renovación del certificado a las 04:00, como root. Se instalan en `/etc/cron.d`, **no** con `crontab -e`, porque en un crontab de usuario no existe el campo `root` y los scripts necesitan root. Equivalente manual:

```sh
sudo tee /etc/cron.d/zabbix > /dev/null <<EOF
# Zabbix backups and certificate renewal (times in host time zone)
30 2 * * * root $(pwd)/server_backup.sh >> /var/log/zabbix-backup.log 2>&1
0 4 * * * root $(pwd)/server_letsencrypt.sh renew >> /var/log/zabbix-letsencrypt.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/zabbix
```

Verificación:
- `cat /etc/cron.d/zabbix` muestra las rutas absolutas del repo.
- Tras la hora programada: `grep zabbix /var/log/syslog` muestra `CMD (... server_backup.sh ...)` y aparece un respaldo nuevo en `./backups`.
- `/var/log/zabbix-backup.log` y `/var/log/zabbix-letsencrypt.log` no contienen errores. `renew` no escribe nada mientras no haya un certificado de Let's Encrypt.

Copiar `./backups` fuera del servidor (rsync, almacenamiento externo). Ver [mantenimiento](mantenimiento.md#copiar-los-respaldos-fuera-del-servidor). La restauración está en [restauración y migración](restauracion-y-migracion.md#restauración).
