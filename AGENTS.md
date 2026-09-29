# AGENTS.md — Reglas para trabajar en este proyecto

Despliegue de producción de Zabbix 7.4 (Docker) para `zabbix.likson.com`, basado en el repositorio oficial `zabbix-docker`.
Estas reglas aplican a cualquier persona o agente (IA) que modifique el proyecto o el servidor de producción.

## Contexto

| Elemento | Valor |
|---|---|
| Servidor de producción | `jjrl@192.168.0.191` (Ubuntu 24.04), repositorio en `~/zabbix-docker` |
| Rama del despliegue | `server-deploy`. `7.4` se mantiene igual que la rama oficial |
| Stack | `docker-compose.yml` + `compose_server.yaml`, variables en `.env` + `server.env` |
| Comando base | `docker compose --env-file .env --env-file server.env <acción>` |
| Guía de despliegue y restauración | `SERVER_DEPLOY.md` |
| Guía de operación (equipos, plantillas, alertas, procedimientos) | `OPERACION.md` |

## Regla 1 — Respaldo antes de modificar producción

**Antes de cualquier cambio en el Zabbix de producción se crea un respaldo nuevo.** Se considera cambio:

- Escrituras por la API o la interfaz web: hosts, plantillas, macros, acciones, usuarios, ajustes.
- Importar o actualizar plantillas.
- `git pull` en el servidor, `up`, `pull`, recrear o reiniciar contenedores, o cambiar `server.env` o `env_vars/`.
- Actualizar la versión de Zabbix o de PostgreSQL.

Las consultas de solo lectura (API `*.get`, logs, `ps`) no requieren respaldo.

Procedimiento:

1. En el servidor, ejecutar `sudo ./server_backup.sh`. Requiere sudo, así que un agente sin la contraseña se lo pide a la persona.
2. Verificar que existe un respaldo de los últimos 60 minutos antes de continuar:
   ```sh
   find ~/zabbix-docker/backups -name 'zabbix-db-*.dump' -mmin -60 -size +1M | grep -q . && echo "respaldo reciente OK"
   ```
3. Si no hay respaldo reciente, **no se hace el cambio**.

Los respaldos se deben copiar fuera del servidor. Una copia local no protege si falla el disco.

## Regla 2 — Lo que no está en la base de datos vive en el repositorio

El respaldo de la base de datos (`pg_dump`) contiene hosts, plantillas importadas, macros, acciones, usuarios, medios, historial y tendencias.
**Todo lo demás debe estar en este repositorio** (o poder regenerarse desde él), para reconstruir el servidor completo si falla el disco o la máquina.

| Qué | Dónde | Cómo se restaura |
|---|---|---|
| Definición del stack | `docker-compose.yml`, `compose_server.yaml`, `server.env.example` | `git clone` |
| Variables de Zabbix | `env_vars/.env_*_override` | `git clone` |
| Configuración de Nginx (HTTP → HTTPS, ACME) | `nginx/zabbix_http.conf` | `git clone` |
| UserParameters del Agent 2 (temperaturas) | `zabbix_agentd.d/` | `git clone` |
| Plantillas propias | `zabbix_templates/*.yaml` | Están también en la BD; si la BD se pierde, se importan desde aquí |
| Scripts de alertas y externos | `alertscripts/`, `externalscripts/` | `git clone` |
| Preparación del host: directorios, cron, lm-sensors | `server_setup.sh` | `./server_setup.sh` |
| Respaldo, restauración y certificados | `server_backup.sh`, `server_restore.sh`, `server_letsencrypt.sh` | `git clone` |
| Scripts de agentes para la API | `agents/scripts/` | `git clone` |
| **Secretos**: contraseña de PostgreSQL, comunidad de traps, `server.env` | **Nunca en git.** En el archivo `zabbix-config-*.tar.gz` del respaldo | `server_restore.sh` o `server_setup.sh` |
| Certificados TLS y `dhparam` | `zbx_env/etc/ssl/nginx`, `letsencrypt/` (en el respaldo) | `server_restore.sh` o `server_letsencrypt.sh issue` |
| MIBs de fabricantes | `zbx_env/var/lib/zabbix/mibs` (en el respaldo) | `server_restore.sh` |

Al añadir cualquier configuración nueva fuera de la base de datos (un script, un MIB, un fichero montado en un contenedor, una tarea de cron, un paquete del host):

1. Añadirla al repositorio. Si es un secreto, añadir la ruta a `server_backup.sh` y a `server_restore.sh`.
2. Actualizar la tabla anterior y `SERVER_DEPLOY.md`.
3. Si hace falta en el host, que `server_setup.sh` la instale de forma idempotente.

## Regla 3 — Flujo de cambios

1. Editar en la copia local, hacer commit en `server-deploy` y hacer push.
2. En el servidor: respaldo (regla 1) → `git pull` → aplicar (`up -d`, importar la plantilla…).
3. **No editar ficheros versionados directamente en el servidor.** `git status` en el servidor debe quedar limpio. Las rutas locales están excluidas en `.git/info/exclude`, y `env_vars/.POSTGRES_PASSWORD` está marcada con `skip-worktree`.
4. Las actualizaciones oficiales se incorporan uniendo `7.4` en `server-deploy`, nunca editando los ficheros originales de Zabbix. Las personalizaciones van en overrides (`compose_server.yaml`, `*_override`).
5. Cada commit termina con las líneas de atribución que correspondan.

## Regla 4 — Secretos

- No imprimir ni escribir en la conversación, en los logs ni en commits: contraseñas, comunidades SNMP, tokens de la API ni claves privadas.
- El token de la API se pasa al script por la entrada estándar y en una llamada SSH aparte: los `docker compose exec` consumen la entrada estándar.
- Para probar SNMP, la comunidad se lee de Zabbix (`{$SNMP_COMMUNITY}`) dentro del script y se pasa por variable de entorno, sin mostrarla.
- Los secretos nuevos los introduce la persona: con `server_setup.sh` (entrada oculta) o en la interfaz como macro de tipo *Secret text*.
- Los tokens de la API deben tener fecha de caducidad y revocarse al terminar cada sesión de trabajo.

## Regla 5 — Límites de actuación

- No ejecutar Docker en el equipo local. Los comandos de Docker se ejecutan solo en el servidor.
- No escanear la red. Se pide la IP del equipo y solo se consulta ese objetivo.
- No borrar contenedores, volúmenes, datos ni hosts de Zabbix sin confirmación explícita.
- Si aparece un estado inesperado (restos de otra instalación, cambios que no son propios), se informa y se pregunta antes de actuar.

## Regla 6 — Plantillas y configuración de Zabbix

- Las plantillas propias se guardan en `zabbix_templates/` y se importan por la API (`configuration.import`) o la interfaz.
- UUID en formato **v4**. El nombre técnico, sin paréntesis (el nombre visible sí puede llevarlos).
- Los triggers de items normales van en la sección `triggers` de primer nivel del export. Los de prototipos van dentro del prototipo.
- En `opdata` y `event_name` de una plantilla, las macros de expresión usan `/{HOST.HOST}/clave`.
- Los ajustes de host hechos por la API (macros, dependencias, items desactivados) quedan en la base de datos. Si son un patrón repetible, se documentan en `SERVER_DEPLOY.md`.
- Cada equipo nuevo se da de alta con su dependencia topológica (quién le da conectividad). Las dependencias se **añaden** a las que ya existen, nunca se sustituyen: las plantillas oficiales traen dependencias internas (pérdida, latencia y SNMP dependen del ping del propio host) que evitan alertas duplicadas.

Particularidades ya conocidas (detalle en `OPERACION.md`):

| Equipo | Particularidad |
|---|---|
| Agent 2 en contenedor (Zabbix server, server-04) | Macros `{$VFS.FS.FSNAME.*}` para ver solo `/rootfs`. Desactivar el checksum de `/etc/passwd` y los usuarios conectados |
| MikroTik | `/snmp src-address` igual a la IP del host en Zabbix, para que los traps se asocien |
| MikroTik concentrador PPPoE | Añadir `\|^<pppoe-` a `{$NET.IF.IFNAME.NOT_MATCHES}` |
| Ubiquiti airOS 8 / airOS 6 | Solo **SNMPv1**. AC sin GPS: `{$UBNT.GPS.SATS.MIN}=0`. airOS 6 usa la variante airMAX M |
| TP-Link | `{$PORT.IFNAME.NOT_MATCHES}=^(<\|Vlan-interface)` y `{$IFCONTROL}=0` con la plantilla de puertos |
| Mimosa C5C (PTP) | SNMPv2. `Network Generic Device by SNMP` + `Mimosa C5C by SNMP` + `Switch port changes by SNMP`. Umbrales de RX según la señal de diseño. El extremo lejano depende del cercano a Zabbix |
| Ubiquiti en enlaces PTP | Umbrales propios de cada enlace como macros de host: `{$UBNT.STA.TXCAP.MIN}` en el AP y `{$UBNT.STA.RXCAP.MIN}` en la estación (Mbps, 0 = desactivado), y la señal. Nombres con `[ ]`: *Host name* sin ellos y `--visible-name` con el nombre exacto |
| *Switch port changes* | Requiere SNMPv2 (`ifXTable`): no usar en airOS (SNMPv1), cuyas plantillas ya vigilan la velocidad de `eth0` |
| Cualquier radio con *Switch port changes* | Nunca vigilar interfaces inalámbricas (`wifi*`, `wlan*`, `ath*`): su velocidad es adaptativa. La plantilla ya las excluye por defecto |

## Regla 7 — Documentar para que una persona pueda hacerlo

Todo lo que se configure o se haga en el proyecto debe poder repetirlo una persona sin ayuda y sin la API. Hay dos documentos, cada uno con su alcance:

| Documento | Contenido |
|---|---|
| `SERVER_DEPLOY.md` | Instalar, migrar, restaurar y actualizar el **servidor** |
| `OPERACION.md` | Usar y ampliar **Zabbix** en el día a día: topología y dependencias, catálogo de plantillas (propias y oficiales) con sus macros y triggers, alertas, procedimientos paso a paso (añadir un AP, un router, un switch o un servidor; ajustar umbrales; mantenimientos; actualizar plantillas; dar de baja equipos) y solución de problemas |

Cada procedimiento de `OPERACION.md` indica:

1. **Cuándo** se usa y los requisitos previos (incluido el respaldo, regla 1).
2. Los **pasos en la interfaz web** de Zabbix y en el equipo (airOS, RouterOS…), con los menús exactos. La API es opcional; la interfaz es obligatoria.
3. Qué **plantillas, macros, dependencias y etiquetas** aplicar y por qué.
4. Cómo **verificar** que funciona.

Cualquier cambio que añada o modifique una plantilla, un trigger, una macro, un tipo de equipo, una dependencia o un procedimiento se documenta en `OPERACION.md` **en el mismo commit**. Esto incluye el inventario de equipos y la topología.

## Regla 8 — Scripts reutilizables para la API

Los scripts que se usan para consultar o modificar Zabbix por la API **no se escriben de un solo uso**. Se guardan en **`agents/scripts/`** para reutilizarlos. Guía y catálogo: `agents/scripts/README.md`.

1. **Antes de escribir un script, se busca en `agents/scripts/`** uno que ya lo haga, o una función de `zbx_api.py` que se pueda reutilizar o ampliar.
2. **Genéricos:** todo lo variable (hosts, grupos, IPs, plantillas, macros, umbrales) llega por argumentos. Nada de valores de producción fijos en el código.
3. **SOLID, KISS y DRY:**
   - Un script, una responsabilidad.
   - La lógica común (cliente de la API, búsquedas, reglas de dependencias, macros, etiquetas, importación) vive solo en `zbx_api.py`.
   - Solución lo más simple posible, sin dependencias fuera de la biblioteca estándar de Python.
4. **Documentados:** docstring con propósito y uso (visible con `--help`) y una fila en la tabla del README.
5. **Seguros:**
   - El token se pasa por la entrada estándar con `run_remote.sh` (regla 4).
   - Los scripts que escriben tienen `--dry-run` y exigen el respaldo previo (regla 1).
   - Ninguno imprime secretos.
6. **Validados** con `python3 -m py_compile` y una ejecución de solo lectura o `--dry-run` antes de usarlos en producción.
7. **Commits:** los cambios en `agents/scripts/` no necesitan un commit por script. Se agrupan en un commit **al final de la sesión de trabajo**, antes de terminarla. El resto de cambios siguen la regla 3.

Las tareas únicas que no justifican un script (una consulta de diagnóstico puntual) pueden hacerse con un script temporal, que se borra al terminar. Si una tarea se repite, se convierte en script de `agents/scripts/`.

## Regla 9 — Verificación

Después de cada cambio se comprueba el resultado real. No basta con que el comando haya terminado sin error:

- `docker compose … ps`: todos los servicios en `running`/`healthy` y `server-db-init` en `exited (0)`.
- En la API: disponibilidad de las interfaces, items no soportados inesperados y problemas activos nuevos.
- Se informa con honestidad de lo que no se pudo verificar.
