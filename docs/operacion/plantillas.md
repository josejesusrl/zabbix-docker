# Catálogo de plantillas

## Plantillas propias (en `zabbix_templates/`)

Una ficha por plantilla en [`plantillas/`](plantillas/), con sus items, triggers, macros y requisitos. Se importan con `zbx_import_template.py` ([crear o modificar una plantilla propia](procedimientos/plantilla-propia.md)).

| Plantilla | Fichero | Para |
|---|---|---|
| [Mimosa C5C by SNMP](plantillas/mimosa-c5c.md) | `mimosa_c5c.yaml` | radios Mimosa C5C (y familia B5/C5) en enlaces PTP, con SNMPv2 |
| [Ubiquiti AirOS 8 wireless by SNMPv1](plantillas/ubiquiti-airos8.md) | `ubiquiti_airos8_wireless.yaml` | APs Ubiquiti airMAX AC con airOS 8 (LAP-GPS, LiteAP, Rocket AC, Prism…) |
| [Ubiquiti airMAX M (airOS 6) wireless by SNMPv1](plantillas/ubiquiti-airmax-m-airos6.md) | `ubiquiti_airmax_m_airos6_wireless.yaml` | equipos airMAX M con airOS 6 (Rocket M5, NanoStation M…) |
| [MikroTik link traps by SNMP](plantillas/mikrotik-link-traps.md) | `mikrotik_link_traps.yaml` | routers MikroTik, junto con su plantilla oficial de modelo |
| [Switch port changes by SNMP](plantillas/switch-port-changes.md) | `switch_port_changes.yaml` | switches cuyos puertos son críticos, de cualquier fabricante |
| [Linux hwmon temperature by Zabbix agent 2](plantillas/linux-hwmon-temperature.md) | `linux_hwmon_temperature.yaml` | servidores Linux físicos con Agent 2 |
| [Likson KPIs](plantillas/likson-kpis.md) | `likson_kpis.yaml` | el host **KPI Likson** (sin interfaz, grupo *Likson KPIs*) |
| [Cloudflare Tunnel by HTTP](plantillas/cloudflare-tunnel.md) | `cloudflared_tunnel.yaml` | el host **Zabbix server** |
| [ISP gateway fast ping](plantillas/isp-gateway-fast-ping.md) | `isp_gateway_fast_ping.yaml` | los gateways de los proveedores de internet (grupo *Proveedores de internet*), **junto con** *ICMP Ping* |
| [ISP internet fast ping](plantillas/isp-internet-fast-ping.md) | `isp_internet_fast_ping.yaml` | comprobar la **salida a Internet** de un proveedor, más allá de su gateway |
| [Likson topology root by Zabbix agent](plantillas/likson-topology-root.md) | `likson_topology_root.yaml` | Raíz de la topología: estado del enlace del Zabbix server cada 5 s |

## Plantillas oficiales en uso y ajustes necesarios

| Plantilla | Para | Ajustes |
|---|---|---|
| *MikroTik \<modelo\> by SNMP* | Routers MikroTik. Usar la del modelo exacto; si no existe, *Mikrotik by SNMP* | En concentradores PPPoE, excluir sesiones ([Añadir un router MikroTik](procedimientos/anadir-router-mikrotik.md)) |
| *TP-LINK by SNMP* | Switches TP-Link | Con *Switch port changes*: `{$IFCONTROL}=0` |
| *Ubiquiti AirOS by SNMP* | APs Ubiquiti (sistema: CPU, memoria, ping) | En airOS 8, *Firmware version* y *Hardware model name* quedan como no soportados (airOS 8 no publica esos datos). Es normal |
| *Linux by Zabbix agent* | Servidores Linux | Si el agente corre en un contenedor con `/rootfs`: macros de sistemas de archivos ([Añadir un servidor Linux](procedimientos/anadir-servidor-linux.md)) |
| *Docker by Zabbix agent 2* | Servidores con Docker | El agente necesita acceso a `/var/run/docker.sock`. Solo descubre los contenedores en ejecución |
| *Hikvision camera by HTTP* | Cámaras y NVR Hikvision (API ISAPI) | `{$HIKVISION_ISAPI_HOST}`, `{$PASSWORD}` (Secret text), `{$USER}` si no es `admin`, resolución del canal principal. Siempre junto con *ICMP Ping* ([añadir una cámara](procedimientos/anadir-camara-hikvision.md)) |
| *ICMP Ping* | Equipos sin SNMP ni agente: cámaras, NVR, gateways de proveedores | Necesita una interfaz (tipo *Agent*) con la IP. Aporta *Unavailable by ICMP ping* para dependencias y mapas |
| *Website certificate by Zabbix agent 2* | Caducidad del certificado autofirmado del origen (host Zabbix server); el público lo renueva Cloudflare | `{$CERT.WEBSITE.HOSTNAME}`, `{$CERT.WEBSITE.IP}=127.0.0.1`, `{$CERT.EXPIRY.WARN}=14` |

## Particularidades por tipo de equipo

Resumen de lo que hay que recordar al dar de alta cada tipo de equipo. El detalle está en las fichas de cada plantilla y en los [procedimientos](../README.md#añadir-o-cambiar-equipos).

| Equipo | Particularidad |
|---|---|
| Agent 2 en contenedor (Zabbix server, server-04) | Macros `{$VFS.FS.FSNAME.*}` para ver solo `/rootfs`. Desactivar el checksum de `/etc/passwd` y los usuarios conectados |
| MikroTik | `/snmp src-address` igual a la IP del host en Zabbix, para que los traps se asocien |
| MikroTik concentrador PPPoE | Añadir `\|^<pppoe-` a `{$NET.IF.IFNAME.NOT_MATCHES}` |
| Ubiquiti airOS 8 / airOS 6 | Solo **SNMPv1**. AC sin GPS: `{$UBNT.GPS.SATS.MIN}=0`. airOS 6 usa la variante airMAX M |
| TP-Link | `{$PORT.IFNAME.NOT_MATCHES}=^(<\|Vlan-interface)` y `{$IFCONTROL}=0` con la plantilla de puertos |
| Mimosa C5C (PTP) | SNMPv2. `Network Generic Device by SNMP` + `Mimosa C5C by SNMP` + `Switch port changes by SNMP`. Umbrales de RX según la señal de diseño. El extremo lejano depende del cercano a Zabbix |
| Ubiquiti en enlaces PTP | Umbrales propios de cada enlace como macros de host: `{$UBNT.STA.TXCAP.MIN}` en el AP y `{$UBNT.STA.RXCAP.MIN}` en la estación (Mbps, 0 = desactivado), y la señal. Nombres con `[ ]`: *Host name* sin ellos y `--visible-name` con el nombre exacto |
| Equipos raíz de la topología | Su trigger de disponibilidad depende de *Zabbix server: Interface enp2s0: Link down* y del trigger raíz de [Likson topology root](plantillas/likson-topology-root.md), para que una caída de red del servidor no se reporte como caída de toda la red ([dependencias](procedimientos/dependencias.md), paso 6) |
| MikroTik (cualquier modelo) | Sus avisos de disco usan `{$VFS.FS.FREE.MIN.WARN}` y `{$VFS.FS.FREE.MIN.CRIT}` sin definirlos en la plantilla oficial: los definen las macros globales ([configuración base](../despliegue/configuracion-base.md#macros-globales-administration--macros)). Sin ellas, los avisos quedan en error y nunca saltan |
| MikroTik NAS con muchas sesiones PPPoE | *Max repetition count* 50 en la interfaz SNMP; desactivar *SNMP walk wireless interfaces* en routers sin radios |
| Problemas de objetos ya no descubiertos o desactivados | Zabbix no los cierra: cerrarlos con comentario (`zbx_close_problems.py`). Cada objeto desactivado a propósito se registra en el [registro](registro.md) |
| Enlaces con problemas largos y conocidos (lluvia) | Etiqueta de host `escalation=off`: la acción de escalada no repite sus *High*. Señal crítica con `{$UBNT.STA.SIGNAL.MIN.CRIT}` y la histéresis `{$UBNT.STA.SIGNAL.HYST}` de la plantilla |
| Hikvision (cámaras, NVR) | Sin SNMP: plantilla HTTP + *ICMP Ping* con interfaz *Agent* solo para el ping. Contraseña en `{$PASSWORD}` como *Secret text*. Etiqueta `notificar=no` mientras se completa el alta. *Error receiving data* depende del ping propio |
| Gateway de proveedor | *ICMP Ping* + *ISP gateway fast ping* (cortes breves), *ISP internet fast ping* (salida a Internet), trigger de bajada degradada en EDGE 01 y una ruta *blackhole* de distancia 254 en EDGE 01 para que el ping solo salga por la interfaz de ese proveedor ([procedimiento](procedimientos/anadir-gateway-proveedor.md)) |
| *Switch port changes* | Requiere SNMPv2 (`ifXTable`): no usar en airOS (SNMPv1), cuyas plantillas ya vigilan la velocidad de `eth0` |
| Cualquier radio con *Switch port changes* | Nunca vigilar interfaces inalámbricas (`wifi*`, `wlan*`, `ath*`): su velocidad es adaptativa. La plantilla ya las excluye por defecto |
