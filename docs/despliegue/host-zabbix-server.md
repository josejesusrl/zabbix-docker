# Configurar el host "Zabbix server"

> **Cuándo:** en una instalación nueva, o al reconstruir sin respaldo de la base de datos. Con respaldo, todo esto ya viene en la BD.
> **Requisitos:** stack arrancado ([instalación](instalacion.md)) y respaldo reciente antes de cada cambio ([AGENTS.md](../../AGENTS.md), regla 1).

El host "Zabbix server" monitorea el propio servidor: el Agent 2 en red de host (`compose_server.yaml`), el proceso de Zabbix, las temperaturas, el certificado del origen y el túnel de Cloudflare. Es además la **raíz de la topología**: los equipos raíz dependen de su enlace de red.

| Plantilla | Aporta | Cómo se enlaza |
|---|---|---|
| *Linux by Zabbix agent* | CPU, memoria, discos, red del host | Viene enlazada |
| *Zabbix server health* | Procesos internos, cachés, colas ([ajustes de rendimiento](mantenimiento.md#ajustes-de-rendimiento)) | Viene enlazada |
| [*Linux hwmon temperature by Zabbix agent 2*](../operacion/plantillas/linux-hwmon-temperature.md) | Temperaturas de CPU, NVMe, placa | Importar `zabbix_templates/linux_hwmon_temperature.yaml` |
| *Website certificate by Zabbix agent 2* | Caducidad del certificado autofirmado del origen | Oficial |
| [*Cloudflare Tunnel by HTTP*](../operacion/plantillas/cloudflare-tunnel.md) | Conexiones del túnel ([acceso externo](acceso-externo.md)) | Importar `zabbix_templates/cloudflared_tunnel.yaml` |
| [*Likson topology root by Zabbix agent*](../operacion/plantillas/likson-topology-root.md) | Raíz de la topología: enlace del servidor cada 5 s | Importar `zabbix_templates/likson_topology_root.yaml` |

## Pasos (en la interfaz web)

1. *Data collection → Hosts → Zabbix server* → *Interfaces*: la interfaz **Agent** con IP `172.16.238.1`, puerto `10050`. El agente usa la red del host y el server lo alcanza por el gateway de la red `frontend` (el firewall del host debe permitirlo, [instalación, sección 3](instalacion.md#3-firewall-del-host)).
2. **Sistemas de archivos:** el agente ve los discos del host bajo `/rootfs`. En la pestaña *Macros*, añadir estas dos macros. Si no, se descubren también los montajes internos del contenedor (`/etc/hosts`, `/var/lib/zabbix/*`…) como discos duplicados:
   ```
   {$VFS.FS.FSNAME.MATCHES}     = ^/rootfs(/|$)
   {$VFS.FS.FSNAME.NOT_MATCHES} = ^/rootfs/(dev|proc|sys|run|var/lib/docker)(/|$)|/shm$
   ```
3. **Items que leen el contenedor y no el host:** desactivar `Checksum of /etc/passwd` (y su trigger, que nunca se dispararía) y `Number of logged in users` (siempre 0).
4. **Temperaturas:**
   - *Data collection → Templates → Import* → `zabbix_templates/linux_hwmon_temperature.yaml`, y enlazarla al host.
   - Los UserParameters ya están en `zabbix_agentd.d/` y lm-sensors lo instala `server_setup.sh`.
   - Prueba: `zbx exec zabbix-agent zabbix_agent2 -t hwmon.temp.discovery`.
5. **Certificado:** enlazar *Website certificate by Zabbix agent 2* con estas macros de host:
   ```
   {$CERT.WEBSITE.HOSTNAME} = zabbix.likson.com
   {$CERT.WEBSITE.IP}       = 127.0.0.1
   {$CERT.EXPIRY.WARN}      = 14
   ```
   El agente se conecta a `127.0.0.1:443` con el nombre `zabbix.likson.com`, sin depender del DNS ni del túnel. Con el certificado autofirmado el resultado es `valid-but-self-signed`, sin alerta, y avisa 14 días antes de que caduque (dura 10 años). El certificado público lo renueva Cloudflare.
6. **Túnel:** importar `zabbix_templates/cloudflared_tunnel.yaml` y enlazar *Cloudflare Tunnel by HTTP*.
7. **Raíz de la topología:** importar `zabbix_templates/likson_topology_root.yaml` y enlazar *Likson topology root by Zabbix agent* ([ficha](../operacion/plantillas/likson-topology-root.md)). Si la interfaz no es `enp2s0`, poner la macro de host `{$ROOT.IF}`. Después, añadir como dependencia su trigger *link not stable in the last 5m* a:
   - *EDGE 01: Unavailable by ICMP ping* y *server-04: Zabbix agent is not available* (equipos raíz, [dependencias](../operacion/procedimientos/dependencias.md), paso 6), además de *Interface enp2s0: Link down*.
   - *Cloudflared: Tunnel connector not responding* y *Tunnel down* de este host.
   - *High CPU utilization* y *High memory utilization* de las cámaras y el NVR.

   Así, si cae la red del propio servidor, no se reporta toda la red como caída, ni durante el corte ni justo al volver.

## Verificar

- Icono **ZBX** en verde en *Data collection → Hosts*.
- *Latest data*: los discos son solo `/rootfs…`, hay temperaturas, `Cloudflared: Tunnel connections` vale 4 y el certificado está en `valid-but-self-signed`.

## Con scripts

```sh
S=agents/scripts/run_remote.sh
printf '%s\n' "$TOKEN" | $S -f zabbix_templates/linux_hwmon_temperature.yaml zbx_import_template.py linux_hwmon_temperature.yaml
printf '%s\n' "$TOKEN" | $S -f zabbix_templates/cloudflared_tunnel.yaml zbx_import_template.py cloudflared_tunnel.yaml
printf '%s\n' "$TOKEN" | $S -f zabbix_templates/likson_topology_root.yaml zbx_import_template.py likson_topology_root.yaml
printf '%s\n' "$TOKEN" | $S zbx_link_template.py --host "Zabbix server" --template "Linux hwmon temperature by Zabbix agent 2" "Cloudflare Tunnel by HTTP" "Website certificate by Zabbix agent 2" "Likson topology root by Zabbix agent"
printf '%s\n' "$TOKEN" | $S zbx_set_macro.py --host "Zabbix server" --macro '{$CERT.WEBSITE.HOSTNAME}=zabbix.likson.com' '{$CERT.WEBSITE.IP}=127.0.0.1' '{$CERT.EXPIRY.WARN}=14'
printf '%s\n' "$TOKEN" | $S zbx_set_status.py --host "Zabbix server" --item "Checksum of /etc/passwd" "Number of logged in users" --disable
printf '%s\n' "$TOKEN" | $S zbx_add_dependency.py --host "EDGE 01" --trigger "Unavailable by ICMP ping" --parent-host "Zabbix server" --parent-trigger "enp2s0: Link down" --dry-run
printf '%s\n' "$TOKEN" | $S zbx_add_dependency.py --host "EDGE 01" --trigger "Unavailable by ICMP ping" --parent-host "Zabbix server" --parent-trigger "link not stable" --dry-run
printf '%s\n' "$TOKEN" | $S zbx_add_dependency.py --host server-04 --trigger "Zabbix agent is not available" --parent-host "Zabbix server" --parent-trigger "enp2s0: Link down" --dry-run
printf '%s\n' "$TOKEN" | $S zbx_add_dependency.py --host server-04 --trigger "Zabbix agent is not available" --parent-host "Zabbix server" --parent-trigger "link not stable" --dry-run
```
