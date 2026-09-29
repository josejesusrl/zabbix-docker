# Despliegue de Zabbix 7.4 en servidor (zabbix.likson.com)

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
| `zabbix_templates/*.yaml` | Plantillas propias: temperaturas, traps de enlace MikroTik, puertos de switch, Ubiquiti airOS 8/airOS 6 |
| `AGENTS.md` | Reglas para modificar el proyecto y la producción (respaldo previo, qué debe estar en git) |
| `OPERACION.md` | Uso diario de Zabbix: topología, plantillas, alertas y procedimientos para añadir equipos |

## Requisitos

- Linux con Docker Engine y `docker compose` >= 2.24, `openssl` y `sudo`.
- Registro DNS A `zabbix.likson.com` apuntando a la IP pública del servidor.
- Puertos abiertos: `80/tcp` (reto ACME y redirección), `443/tcp` (web), `162/udp` (traps desde cualquier red) y `10051/tcp` (agentes remotos).
- Salida desde el servidor hacia `10050/tcp` de los agentes remotos (checks pasivos) y `161/udp` de los equipos SNMP.
- En el host no debe haber otro agente de Zabbix usando el puerto 10050.

## 0. Antes de empezar: elegir el camino

| Situación | Camino |
|---|---|
| Servidor nuevo, sin datos previos que conservar | Secciones 1 a 5 |
| Este despliegue se perdió (disco, servidor) y hay respaldos de `server_backup.sh` | [Restauración](#restauración) |
| Ya existe **otra implementación de Zabbix** (en este servidor o en otro) y se quieren conservar sus datos | [Migración desde una implementación anterior](#migración-desde-una-implementación-anterior), luego secciones 2 a 5 |

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

## 4. Configuración en la interfaz web (`https://zabbix.likson.com`)

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
4. **Equipos a monitorear** (routers, switches, APs, servidores), plantillas propias, dependencias, alertas y umbrales: ver **`OPERACION.md`**.
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

Copiar `./backups` fuera del servidor (rsync, almacenamiento externo). El procedimiento de restauración está en la cabecera de `server_backup.sh`.

## Migración desde una implementación anterior

Para conservar hosts, plantillas, historial y usuarios de un Zabbix existente.

1. **Respaldar la base de datos anterior** mientras sigue en marcha. Con PostgreSQL:
   ```sh
   docker exec <contenedor-postgres-anterior> sh -c 'pg_dump -U <usuario> -d <bd> -Fc' > zabbix-anterior.dump
   ls -lh zabbix-anterior.dump     # debe pesar más de unos pocos MB
   ```
   - Si la anterior usaba **MySQL/MariaDB**, su dump no se puede restaurar en PostgreSQL. Hay que exportar las plantillas y los hosts desde su interfaz (*Data collection → Hosts/Templates → Export*) e importarlos en la nueva; el historial no se migra.
   - Copiar también lo que la instalación anterior tuviera fuera de la BD (scripts de alertas, scripts externos, MIBs, UserParameters). Según `AGENTS.md`, se incorpora a este repositorio.
2. **Detener y eliminar la instalación anterior:** contenedores, redes y volúmenes, en su directorio con `docker compose down`, o uno a uno. Conservar su carpeta de datos hasta verificar la migración.
3. **Clonar y preparar** este repositorio (sección 1). La contraseña de PostgreSQL que se introduzca será la de la nueva BD.
4. **Restaurar el dump** en la nueva BD, que tiene que estar vacía:
   ```sh
   sudo ./server_restore.sh --db zabbix-anterior.dump
   ```
   Si el dump es de una versión anterior de Zabbix, el server migra el esquema al arrancar. Seguir el progreso con `zbx logs -f zabbix-server`: la actualización de la BD puede tardar varios minutos.
5. **Revisar en la nueva interfaz** la interfaz del agente del host "Zabbix server" (`172.16.238.1`) y sus macros (sección 4). Importar las plantillas de `zabbix_templates/` que falten y comprobar los hosts.
6. Continuar con las secciones 2 a 5 (certificado, firewall, tareas programadas).

## Restauración

Para reconstruir este despliegue en un disco o servidor nuevo a partir de los respaldos de `server_backup.sh`. Hacen falta los dos ficheros del mismo momento: `zabbix-db-<fecha>.dump` y `zabbix-config-<fecha>.tar.gz`, copiados fuera del servidor.

1. **Preparar el host:** requisitos, Docker y clonar el repositorio (sección 1, **sin** ejecutar todavía `server_setup.sh`).
2. **Copiar los respaldos** a `~/zabbix-docker/backups/`.
3. **Restaurar configuración y base de datos:**
   ```sh
   cd ~/zabbix-docker
   sudo ./server_restore.sh --config backups/zabbix-config-<fecha>.tar.gz --db backups/zabbix-db-<fecha>.dump
   ```
   - `--config` recupera lo que no está en git: la contraseña de PostgreSQL, `server.env`, los certificados, la cuenta de Let's Encrypt, los MIBs y la comunidad de traps. Los ficheros versionados salen de git.
   - `--db` arranca PostgreSQL, restaura el dump y levanta el stack completo.
   - Si `./zabbix-db-data` ya contiene una BD, el script se detiene. Para sobrescribirla, respaldar primero y añadir `--replace-db`.
4. **Completar la preparación del host:**
   ```sh
   ./server_setup.sh
   ```
   No vuelve a pedir los secretos restaurados; crea las exclusiones de git, el cron y lm-sensors.
5. **Certificado:** el restaurado sirve si no ha caducado. Si no, `sudo ./server_letsencrypt.sh issue` (o `selfsigned` sin acceso público).
6. **Firewall** (sección 3) y comprobación: `zbx ps`, acceso web, disponibilidad de los hosts y llegada de traps.

**Si no hay respaldo de la BD**, se recupera todo lo que está en git (stack, plantillas propias, UserParameters, scripts), pero **los hosts, macros de host, acciones, usuarios e historial se pierden**. Hay que importar `zabbix_templates/*.yaml` y volver a dar de alta los equipos según esta guía. Por eso los respaldos deben copiarse fuera del servidor.

## Operación

- **Estado:** `zbx ps`. Todos deben estar `running`/`healthy` y `server-db-init` en `exited (0)`.
- **Logs:** `zbx logs -f zabbix-server`.
- **Antes de cualquier cambio en producción:** `sudo ./server_backup.sh` (ver `AGENTS.md`).
- **Actualizar Zabbix:**
  1. `sudo ./server_backup.sh`
  2. `git pull`
  3. Subir `ZBX_IMAGE_TAG` en `server.env`.
  4. `zbx pull && zbx up -d`. El esquema de la BD se migra automáticamente.
- **Probar traps:** envía un trap de prueba con la comunidad configurada, sin mostrarla, y revisa el log. La IP de origen debe ser la del equipo emisor; desde el propio servidor aparece `172.16.238.1`.
  ```sh
  C="docker compose --env-file .env --env-file server.env"
  export COM=$($C exec -T zabbix-snmptraps awk '/^authCommunity/{print $3}' /etc/snmp/snmptrapd.conf)
  docker run --rm -e COM alpine:3.22 sh -c 'apk add -q --no-cache net-snmp-tools >/dev/null && snmptrap -v 2c -c "$COM" 192.168.0.191:162 "" 1.3.6.1.6.3.1.1.5.3 1.3.6.1.2.1.2.2.1.1.1 i 1'
  unset COM
  $C exec zabbix-snmptraps tail -5 /var/lib/zabbix/snmptraps/snmptraps.log
  ```
- **Cambiar la comunidad de traps:** borrar `snmptraps/snmptrapd.conf`, ejecutar `./server_setup.sh` y luego `zbx up -d --force-recreate zabbix-snmptraps`.
- **Solo agente local:** poner `ZABBIX_SERVER_BIND_IP=127.0.0.1` en `server.env` y ejecutar `zbx up -d`.

## Agentes remotos (agent / agent2)

Configuración en cada servidor monitoreado (`zabbix_agentd.conf` o `zabbix_agent2.conf`):

```ini
# Checks pasivos: IP pública del servidor Zabbix (o la IP con la que sale hacia el agente)
Server=<ip-servidor-zabbix>
# Checks activos
ServerActive=zabbix.likson.com
Hostname=<nombre-unico-del-host>
```

- **Pasivos:** el server conecta al `10050/tcp` del agente. Abrir ese puerto en el equipo remoto solo para la IP del servidor Zabbix.
- **Activos:** el agente conecta al `10051/tcp` de `zabbix.likson.com`.
- **Cifrado recomendado:** el 10051 queda expuesto a Internet. Usar PSK en cada agente (`TLSConnect=psk`, `TLSAccept=psk`, `TLSPSKIdentity`, `TLSPSKFile`) y la misma PSK en *Host → Encryption*. Así los agentes sin PSK son rechazados.
- **Alta automática:** con *Alerts → Actions → Autoregistration actions* y `HostMetadata` en el agente, los hosts nuevos se dan de alta solos. Configurar PSK para autoregistro en *Administration → General → Autoregistration*.
