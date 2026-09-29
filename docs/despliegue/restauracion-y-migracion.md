# Restauración y migración

> **Cuándo:** el servidor se perdió y hay respaldos de `server_backup.sh` ([restauración](#restauración)), o hay otro Zabbix cuyos datos se quieren conservar ([migración](#migración-desde-una-implementación-anterior)).
> Las referencias a "sección N" apuntan a [instalación](instalacion.md).

## Migración desde una implementación anterior

Para conservar hosts, plantillas, historial y usuarios de un Zabbix existente.

1. **Respaldar la base de datos anterior** mientras sigue en marcha. Con PostgreSQL:
   ```sh
   docker exec <contenedor-postgres-anterior> sh -c 'pg_dump -U <usuario> -d <bd> -Fc' > zabbix-anterior.dump
   ls -lh zabbix-anterior.dump     # debe pesar más de unos pocos MB
   ```
   - Si la anterior usaba **MySQL/MariaDB**, su dump no se puede restaurar en PostgreSQL. Hay que exportar las plantillas y los hosts desde su interfaz (*Data collection → Hosts/Templates → Export*) e importarlos en la nueva; el historial no se migra.
   - Copiar también lo que la instalación anterior tuviera fuera de la BD (scripts de alertas, scripts externos, MIBs, UserParameters). Según [AGENTS.md](../../AGENTS.md), se incorpora a este repositorio.
2. **Detener y eliminar la instalación anterior:** contenedores, redes y volúmenes, en su directorio con `docker compose down`, o uno a uno. Conservar su carpeta de datos hasta verificar la migración.
3. **Clonar y preparar** este repositorio ([instalación, sección 1](instalacion.md#1-clonar-y-preparar)). La contraseña de PostgreSQL que se introduzca será la de la nueva BD.
4. **Restaurar el dump** en la nueva BD, que tiene que estar vacía:
   ```sh
   sudo ./server_restore.sh --db zabbix-anterior.dump
   ```
   Si el dump es de una versión anterior de Zabbix, el server migra el esquema al arrancar. Seguir el progreso con `zbx logs -f zabbix-server`: la actualización de la BD puede tardar varios minutos.
5. **Revisar en la nueva interfaz** la interfaz del agente del host "Zabbix server" (`172.16.238.1`) y sus macros ([instalación, sección 4](instalacion.md#4-configuración-en-la-interfaz-web)). Importar las plantillas de `zabbix_templates/` que falten y comprobar los hosts.
6. Continuar con las secciones 2 a 5 de [instalación](instalacion.md) (certificado, firewall, tareas programadas).

## Restauración

Para reconstruir este despliegue en un disco o servidor nuevo a partir de los respaldos de `server_backup.sh`. Hacen falta los dos ficheros del mismo momento: `zabbix-db-<fecha>.dump` y `zabbix-config-<fecha>.tar.gz`, copiados fuera del servidor.

1. **Preparar el host:** requisitos, Docker y clonar el repositorio ([instalación, sección 1](instalacion.md#1-clonar-y-preparar), **sin** ejecutar todavía `server_setup.sh`).
2. **Copiar los respaldos** a `~/zabbix-docker/backups/`.
3. **Restaurar configuración y base de datos:**
   ```sh
   cd ~/zabbix-docker
   sudo ./server_restore.sh --config backups/zabbix-config-<fecha>.tar.gz --db backups/zabbix-db-<fecha>.dump
   ```
   - `--config` recupera lo que no está en git: la contraseña de PostgreSQL, el token del túnel de Cloudflare, `server.env`, el certificado, los MIBs y la comunidad de traps. Los ficheros versionados salen de git.
   - `--db` arranca PostgreSQL, restaura el dump y levanta el stack completo.
   - Si `./zabbix-db-data` ya contiene una BD, el script se detiene. Para sobrescribirla, respaldar primero y añadir `--replace-db`.
4. **Completar la preparación del host:**
   ```sh
   ./server_setup.sh
   ```
   No vuelve a pedir los secretos restaurados; crea las exclusiones de git, el cron y lm-sensors.
5. **Certificado y túnel:** el certificado restaurado sirve si no ha caducado; si no, `sudo ./server_certificate.sh selfsigned`. El túnel conecta solo con el token restaurado. Si el servidor viejo sigue encendido, parar antes su `cloudflared` ([acceso externo](acceso-externo.md#rotar-el-token-o-mover-el-túnel-a-otro-servidor)).
   - Respaldos anteriores al túnel: traen `letsencrypt/`, que ya no se usa, y no traen el token. `./server_setup.sh` lo pedirá.
6. **Firewall** ([instalación, sección 3](instalacion.md#3-firewall-del-host)) y comprobación: `zbx ps`, acceso web, disponibilidad de los hosts y llegada de traps.

**Si no hay respaldo de la BD**, se recupera todo lo que está en git (stack, plantillas propias, UserParameters, scripts), pero **los hosts, macros de host, acciones, usuarios e historial se pierden**. Por eso los respaldos deben copiarse fuera del servidor. Para reconstruir:

1. Importar `zabbix_templates/*.yaml` (*Data collection → Templates → Import*, o `zbx_import_template.py`).
2. Rehacer lo descrito en [configuración base](configuracion-base.md): medios Telegram y Gmail (con `zbx_mediatype_update.py` se cargan el script y las plantillas de `zabbix_media/`), usuarios, acciones, macro global y ajustes.
3. Volver a dar de alta los equipos según el [inventario](../operacion/inventario.md) y los [procedimientos](../README.md#añadir-o-cambiar-equipos).
4. Crear el dashboard con `zbx_dashboard_apply.py` desde `zabbix_dashboards/likson_noc.json`.
