# Añadir un servidor Linux

> **Cuándo:** al monitorear un servidor Linux con Zabbix Agent 2, en la LAN o remoto.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. **Instalar Zabbix Agent 2** en el servidor, o en contenedor como `server-04`. En su configuración:
   ```ini
   Server=192.168.0.191          # checks pasivos (IP con la que llega el Zabbix server)
   ServerActive=192.168.0.191    # no zabbix.likson.com: apunta a Cloudflare, que solo lleva la web
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

El puerto `10051/tcp` **no** se publica en Internet: el túnel de Cloudflare solo lleva la web ([acceso externo](../../despliegue/acceso-externo.md)). Hay dos opciones para un servidor remoto:

- **Checks pasivos** (recomendado): el Zabbix server conecta al `10050/tcp` del agente. En el equipo remoto, abrir ese puerto solo para la IP pública de salida de la red de Likson. En el agente, `Server=<esa IP pública>` y sin `ServerActive`.
- **Checks activos o alta automática:** requieren que el agente llegue al `10051/tcp` del servidor, a través de una VPN hacia la LAN (en el agente, `ServerActive=192.168.0.191`). Antes de abrir el 10051 en el NAT, registrar la decisión en el [registro](../registro.md).

En cualquier caso, usar cifrado **PSK**: en el agente `TLSConnect=psk`, `TLSAccept=psk`, `TLSPSKIdentity` y `TLSPSKFile`, y la misma PSK en *Host → Encryption*. Así los agentes sin PSK son rechazados.
- **Alta automática:** con *Alerts → Actions → Autoregistration actions* y `HostMetadata` en el agente, los hosts nuevos se dan de alta solos. Configurar PSK para autoregistro en *Administration → General → Autoregistration*.
