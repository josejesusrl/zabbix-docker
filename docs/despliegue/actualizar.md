# Actualizar Zabbix, PostgreSQL o cloudflared

> **Cuándo:** al aplicar una versión nueva de Zabbix (incluido el salto a **8.0 LTS**, pendiente antes del 2026-12-31, ver [registro](../operacion/registro.md)), de PostgreSQL o del conector `cloudflared`.
> **Requisitos:** respaldo nuevo y **copiado fuera del servidor** ([AGENTS.md](../../AGENTS.md), regla 1). Los comandos usan el alias `zbx` ([instalación](instalacion.md#2-arrancar-y-crear-el-certificado)).

Las versiones están fijadas en `server.env` (`ZBX_IMAGE_TAG`, `CLOUDFLARED_IMAGE_TAG`): nada se actualiza solo.

## Zabbix: versión menor (p. ej. 7.4.15 → 7.4.16)

1. `sudo ./server_backup.sh`
2. `git pull` (por si el repositorio trae cambios para esa versión).
3. Subir `ZBX_IMAGE_TAG` en `server.env`.
4. `zbx pull && zbx up -d`. El esquema de la BD se migra automáticamente.
5. Verificar: `zbx ps`, `zbx logs zabbix-server | grep -i -E "error|upgrade"` y la interfaz web.

## Zabbix: versión mayor (p. ej. 7.4 → 8.0 LTS)

1. Leer las notas de actualización oficiales (*Upgrade notes*) de la versión nueva: cambios de API, de plantillas y de requisitos de PostgreSQL.
2. **Probar primero en una copia:** restaurar el último respaldo en otra máquina ([restauración](restauracion-y-migracion.md#restauración)), cambiar allí `ZBX_IMAGE_TAG` y arrancar. Comprobar:
   - Que la migración del esquema termina.
   - Que las plantillas propias se importan (`zbx_import_template.py` avisa si se pierde algún trigger).
   - Que los scripts de `agents/scripts/` funcionan con la API nueva.
   - Que los avisos se envían (`zbx_test_notification.py`).
3. Unir en `server-deploy` la rama oficial nueva ([AGENTS.md](../../AGENTS.md), regla 3) y ajustar `compose_server.yaml` y `server.env.example` si cambian.
4. En producción: respaldo, `git pull`, subir `ZBX_IMAGE_TAG`, `zbx pull && zbx up -d`. La migración de una versión mayor puede tardar varios minutos: seguirla con `zbx logs -f zabbix-server`.
5. Verificar como en una versión menor, más los items no soportados y problemas nuevos (`zbx_host_status.py`).

## PostgreSQL

Una versión mayor de PostgreSQL no puede usar los datos de la anterior. Se hace con volcado y restauración: respaldo, cambiar la imagen y restaurar el volcado en una BD vacía ([restauración](restauracion-y-migracion.md#restauración)). Probarlo antes en una copia.

## cloudflared

1. Respaldo.
2. Subir `CLOUDFLARED_IMAGE_TAG` en `server.env` (versiones en [GitHub](https://github.com/cloudflare/cloudflared/releases)). Cloudflare avisa en el panel cuando una versión queda sin soporte.
3. `zbx pull cloudflared && zbx up -d cloudflared`.
4. Verificar: `zbx ps` con `cloudflared` en `healthy` y *Cloudflared: Tunnel connections* = 4 en *Latest data* ([acceso externo](acceso-externo.md#4-verificar)).
