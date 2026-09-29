# Mantenimiento del servidor

> **Cuándo:** tareas del servidor y del stack Docker: estado, logs, actualización, traps, respaldos. Los comandos se ejecutan en `~/zabbix-docker` con el alias `zbx` ([instalación](instalacion.md#2-arrancar-y-emitir-el-certificado)).

## Operación

- **Estado:** `zbx ps`. Todos deben estar `running`/`healthy` y `server-db-init` en `exited (0)`.
- **Logs:** `zbx logs -f zabbix-server`.
- **Antes de cualquier cambio en producción:** `sudo ./server_backup.sh` (ver [AGENTS.md](../../AGENTS.md), regla 1).
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

## Copiar los respaldos fuera del servidor

`server_backup.sh` guarda en `~/zabbix-docker/backups/` los dos ficheros de cada respaldo: `zabbix-db-<fecha>.dump` y `zabbix-config-<fecha>.tar.gz`. Si el disco del servidor falla, se pierden con él. Desde otro equipo:

```sh
scp 'jjrl@192.168.0.191:zabbix-docker/backups/zabbix-*' /ruta/de/respaldos/
```

`zabbix-config-*.tar.gz` contiene secretos (contraseña de PostgreSQL, clave del certificado, comunidad de traps): guardarlo en un lugar protegido.
