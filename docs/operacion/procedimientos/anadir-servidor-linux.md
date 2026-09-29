# Añadir un servidor Linux

> **Cuándo:** al monitorear un servidor Linux con Zabbix Agent 2, en la LAN o remoto.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. **Instalar Zabbix Agent 2** en el servidor, o en contenedor como `server-04`. En su configuración:
   ```ini
   Server=192.168.0.191          # checks pasivos (IP con la que llega el Zabbix server)
   ServerActive=zabbix.likson.com
   Hostname=<nombre-del-servidor>
   ```
   El puerto 10050/tcp del servidor debe aceptar conexiones desde 192.168.0.191.
2. *Create host*: **Host name** = el `Hostname` del agente (exacto), grupo `Linux servers`, interfaz **Agent** (IP, 10050).
3. **Templates:** `Linux by Zabbix agent`. Si tiene Docker: `Docker by Zabbix agent 2`. Si es físico y tiene los UserParameters de temperatura: `Linux hwmon temperature by Zabbix agent 2`.
4. **Si el agente corre en un contenedor** con el disco del host montado en `/rootfs`:
   - Macros `{$VFS.FS.FSNAME.MATCHES}` = `^/rootfs(/|$)` y `{$VFS.FS.FSNAME.NOT_MATCHES}` = `^/rootfs/(dev|proc|sys|run|var/lib/docker)(/|$)|/shm$`.
   - En *Items*, desactivar `Checksum of /etc/passwd` y `Number of logged in users` (leen el contenedor, no el host).
5. **Verificar:** icono **ZBX** en verde, y en *Latest data* CPU, memoria y sistemas de archivos del host (solo `/rootfs…` si está en contenedor).

## Servidores remotos (fuera de la LAN)

Configuración en cada servidor monitoreado (`zabbix_agentd.conf` o `zabbix_agent2.conf`):

```ini
# Checks pasivos: la IP desde la que llega el Zabbix server. En la LAN, 192.168.0.191; desde internet, la IP pública del NAT de Zabbix
Server=<ip-servidor-zabbix>
# Checks activos
ServerActive=zabbix.likson.com
Hostname=<nombre-unico-del-host>
```

- **Pasivos:** el server conecta al `10050/tcp` del agente. Abrir ese puerto en el equipo remoto solo para la IP del servidor Zabbix.
- **Activos:** el agente conecta al `10051/tcp` de `zabbix.likson.com`.
- **Cifrado recomendado:** el 10051 queda expuesto a Internet. Usar PSK en cada agente (`TLSConnect=psk`, `TLSAccept=psk`, `TLSPSKIdentity`, `TLSPSKFile`) y la misma PSK en *Host → Encryption*. Así los agentes sin PSK son rechazados.
- **Alta automática:** con *Alerts → Actions → Autoregistration actions* y `HostMetadata` en el agente, los hosts nuevos se dan de alta solos. Configurar PSK para autoregistro en *Administration → General → Autoregistration*.
