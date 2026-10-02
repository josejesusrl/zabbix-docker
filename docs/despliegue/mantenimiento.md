# Mantenimiento del servidor

> **Cuándo:** tareas del servidor y del stack Docker: estado, logs, ajustes de rendimiento y respaldos. Para **actualizar** Zabbix, PostgreSQL o `cloudflared`: [actualizar](actualizar.md). Traps: [configurar traps](../operacion/procedimientos/configurar-traps.md). Los comandos se ejecutan en `~/zabbix-docker` con el alias `zbx` ([instalación](instalacion.md#2-arrancar-y-crear-el-certificado)).

## Operación

- **Estado:** `zbx ps`. Todos deben estar `running`/`healthy` y `server-db-init` en `exited (0)`.
- **Logs:** `zbx logs -f zabbix-server`.
- **Antes de cualquier cambio en producción:** `sudo ./server_backup.sh` (ver [AGENTS.md](../../AGENTS.md), regla 1).
- **Actualizar** Zabbix, PostgreSQL o `cloudflared`: [actualizar](actualizar.md).
- **Túnel:** `zbx logs cloudflared`. Configuración y Access: [acceso externo](acceso-externo.md).
- **Solo agente local:** poner `ZABBIX_SERVER_BIND_IP=127.0.0.1` en `server.env` y ejecutar `zbx up -d`.

## Ajustes de rendimiento

Valores aplicados el 2026-09-29 con 40 hosts, unos 6700 items y 90 valores por segundo, en un host de 4 CPU y 3,3 GB de RAM:

| Ajuste | Dónde | Valor (por defecto) | Indicador que lo motivó |
|---|---|---|---|
| Caché de configuración | `env_vars/.env_srv_override`: `ZBX_CACHESIZE` | `128M` (`32M`) | `zabbix[rcache,buffer,pused]` al 73 % |
| Procesos de ping ICMP | `env_vars/.env_srv_override`: `ZBX_STARTPINGERS` | `3` (`1`) | `zabbix[process,icmp pinger,avg,busy]` al 63 % |
| Memoria de PostgreSQL | `compose_server.yaml`, `command` de `postgres-server` | `shared_buffers=512MB`, `effective_cache_size=2GB`, `work_mem=8MB`, `maintenance_work_mem=128MB` (`128MB`, `4GB`, `4MB`, `64MB`) | Valores por defecto sin ajustar a la RAM |

- **Cuándo revisarlos:** si la plantilla *Zabbix server health* avisa de un proceso ocupado más del 75 % o de una caché llena más del 75 %. Se ven en el dashboard *Zabbix server health* o en *Latest data* del host Zabbix server.
- **Cómo cambiarlos:** editar el fichero del repositorio, commit y, en el servidor, respaldo, `git pull` y `zbx up -d`. Solo se recrean los servicios afectados; `postgres-server` se reinicia unos segundos.
- **Comprobar:** `zbx exec postgres-server psql -U zabbix -d zabbix -Atc 'show shared_buffers'` y los items `zabbix[rcache,buffer,pused]` y `zabbix[process,icmp pinger,avg,busy]` tras unos minutos.
- Si se amplía la RAM del host, subir `shared_buffers` a ~25 % de la RAM y `effective_cache_size` a ~60 %.

## Copiar los respaldos fuera del servidor

`server_backup.sh` guarda en `~/zabbix-docker/backups/` los dos ficheros de cada respaldo: `zabbix-db-<fecha>.dump` y `zabbix-config-<fecha>.tar.gz`. Si el disco del servidor falla, se pierden con él. Desde otro equipo:

```sh
scp 'jjrl@192.168.0.191:zabbix-docker/backups/zabbix-*' /ruta/de/respaldos/
```

`zabbix-config-*.tar.gz` contiene secretos (contraseña de PostgreSQL, clave del certificado, comunidad de traps): guardarlo en un lugar protegido.
