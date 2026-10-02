# Likson topology root by Zabbix agent

> **Fichero:** `zabbix_templates/likson_topology_root.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** solo el host **Zabbix server**. Es la raíz de la topología: si el servidor pierde su propia red, nada de lo que monitorea por esa red debe avisar.

**Recoge:** el estado del enlace `{$ROOT.IF}` (`enp2s0`) leyendo `/sys/class/net/<interfaz>/operstate` **cada 5 s** a través del agente local. El agente va por la red interna de Docker, así que sigue respondiendo aunque el cable esté desconectado.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Interface {$ROOT.IF}: link not stable in the last 5m (topology root) | Information (no notifica) | El enlace no estuvo `up` en algún momento de los últimos 5 min |

**Dependen de él:** *EDGE 01: Unavailable by ICMP ping*, *server-04: Zabbix agent is not available*, los dos avisos High del túnel y la CPU y memoria de las cámaras y el NVR. Todo lo demás cuelga de EDGE 01, y Zabbix aplica las dependencias en cadena.

**Por qué cada 5 s y durante 5 min** (prueba del 2026-10-02, cable desconectado 8 min):
- Las comprobaciones rápidas, como la lectura HTTP de las cámaras o el ping de 10 s a los proveedores, fallan a los pocos segundos. Con la lectura cada minuto de la plantilla Linux, el trigger raíz se abrió casi un minuto tarde y esos avisos ya habían saltado.
- Tras volver el enlace, los pings y las medias de 5 min tardan unos minutos en normalizarse. El trigger sigue activo 5 min para cubrirlo.

**Efecto a tener en cuenta:** mientras un trigger del que se depende está en problema, Zabbix **tampoco resuelve** los que dependen de él. Si un aviso se abrió antes que el trigger raíz, queda abierto hasta que llegue un dato nuevo. Si no llega porque el valor no cambia, hay que cerrarlo a mano ([solución de problemas](../solucion-de-problemas.md)).

Macro: `{$ROOT.IF}` (`enp2s0`). En un servidor nuevo con otra interfaz, cambiarla en el host.
