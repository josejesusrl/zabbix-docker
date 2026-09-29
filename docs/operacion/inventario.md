# Inventario y topología

Qué se monitorea y de quién depende cada equipo. **Es lo que más cambia:** al dar de alta, mover o retirar un equipo, actualizar este documento en el mismo commit.

### Convenciones

| Elemento | Convención |
|---|---|
| Nombre del host | El nombre de sistema del equipo (`sysName` o *Device Name*), idéntico en *Host name* y *Visible name*. Si el equipo no tiene nombre, se le pone primero en el propio equipo. El *Host name* solo admite letras, dígitos, espacios, `.`, `-` y `_`: si el nombre lleva otros caracteres (p. ej. `[AP]-…`), el *Host name* los omite y el *Visible name* conserva el nombre exacto |
| Grupos de hosts | `Routers & Switches Likson` (MikroTik, switches), `Access Points PPPoE Clients` (APs Ubiquiti), `Enlaces PTP Troncales` y `Enlaces PTP Backhaul` (radios PTP), `Linux servers`, `Zabbix servers`, `Likson KPIs` (host de indicadores) |
| Etiqueta `uplink` | Nombre del equipo del que depende (p. ej. `uplink = EDGE 01`). Sirve para filtrar y como documentación de la dependencia |
| Interfaz SNMP | Comunidad `{$SNMP_COMMUNITY}` (macro global). MikroTik, TP-Link y Mimosa: SNMPv2. **Ubiquiti: SNMPv1**. La macro es de tipo **texto** a propósito: `snmp_probe.py` y `snmp_walk.py` la leen por la API para sondear equipos sin mostrarla. Si se cambia a *Secret text*, esos scripts dejan de funcionar |
| Dependencias | Cada equipo depende del que le da conectividad hacia Zabbix ([Configurar las dependencias de un host](procedimientos/dependencias.md)) |

### Topología y dependencias actuales

```
Zabbix server (192.168.0.191)                 raíz: su trigger "Interface enp2s0: Link down" es el padre de todo
server-04 (192.168.50.254)                    depende del enlace de red del Zabbix server
KPI Likson                                    host sin interfaz: indicadores calculados (dashboard)
EDGE 01 (192.168.200.1)  MikroTik CCR2004  depende del enlace de red del Zabbix server
├── STA-Lk_Trunk_01_A (10.100.0.3)  Mimosa C5C, extremo del troncal conectado a EDGE 01
│   └── AP-Lk_Trunk_01_A (10.100.0.2)  Mimosa C5C, extremo lejano (solo se alcanza a través del enlace)
├── NAS-01 (192.168.200.2)  CCR2004, concentrador PPPoE
│   ├── Switch Main Site #01 (172.16.100.2)  TP-Link
│   │   ├── APs Ubiquiti 172.16.1.2 – 172.16.1.19 (16 APs, uplink = Switch Main Site #01)
│   │   ├── STA-Lk_Hq_Mayolica_1 (10.155.1.3)  NanoStation loco M2 (airOS 6), backhaul
│   │   │   └── AP-Lk_Hq_Mayolica_1 (10.155.1.2)  NanoStation loco M2, extremo lejano
│   │   ├── [STA]Lk_Hq_Caribe_1 (10.155.3.3)  LiteBeam 5AC, backhaul sensible a lluvia (escalation=off)
│   │   │   └── [AP]Lk_Hq_Caribe_1 (10.155.3.2)  LiteBeam 5AC, extremo lejano
│   │   └── [CPE]-Lk_Hq_Pintores_1 (10.155.0.3)  LiteBeam 5AC, extremo cercano del backhaul
│   │       └── [AP]-Lk_Hq_Pintores_1 (10.155.0.2)  LiteBeam 5AC, extremo lejano
│   │           └── [CPE]Lk_Pintores_Canadas_1 (10.155.2.3)  LiteBeam 5AC, backhaul Pintores → Cañadas
│   │               └── [AP]-Lk_Pintores_Canadas_1 (10.155.2.2)  LiteBeam 5AC, extremo lejano
│   └── Sector_3, Sector_4, Sector_5 (172.16.2.x, uplink = NAS-01)
└── NAS-03 (192.168.200.10)  RB2011iL-RM, concentrador PPPoE
    └── LIKSON_CANADAS_A/B/C/D_01 (172.16.3.10 – .13, uplink = NAS-03)
```

Los sectores `172.16.2.x` están conectados físicamente a NAS-02, que se va a retirar y no está dado de alta en Zabbix. Por eso dependen de NAS-01.

### Inventario (generado desde Zabbix)

Tablas generadas con `agents/scripts/zbx_inventory.py --markdown` y pegadas aquí; no editarlas a mano. Para regenerarlas, ver [agents/scripts/README.md](../../agents/scripts/README.md). Las macros con regex largas se muestran solo por nombre.

#### Access Points PPPoE Clients

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| LIKSON_BETA01 | snmpv1 172.16.1.14 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_CANADAS_A_01 | snmpv1 172.16.3.12 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=NAS-03 | NAS-03 |
| LIKSON_CANADAS_B_01 | snmpv1 172.16.3.13 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=NAS-03 | NAS-03 |
| LIKSON_CANADAS_C_01 | snmpv1 172.16.3.10 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=NAS-03 | NAS-03 |
| LIKSON_CANADAS_D_01 | snmpv1 172.16.3.11 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=NAS-03 | NAS-03 |
| LIKSON_HQ_DELTA_01 | snmpv1 172.16.1.18 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_HQ_EPSILON_01 | snmpv1 172.16.1.19 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_1 | snmpv1 172.16.1.2 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_10 | snmpv1 172.16.1.9 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_2 | snmpv1 172.16.1.3 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_3 | snmpv1 172.16.1.4 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_4 | snmpv1 172.16.1.5 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_5 | snmpv1 172.16.1.6 | Ubiquiti airMAX M airOS6 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_6 | snmpv1 172.16.1.7 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_7 | snmpv1 172.16.1.15 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LIKSON_PDV_9 | snmpv1 172.16.1.8 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LKON_SGAMMA01 | snmpv1 172.16.1.10 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LK_C2 | snmpv1 172.16.1.16 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LK_C3 | snmpv1 172.16.1.11 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| LK_C4 | snmpv1 172.16.1.17 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| Sector_3 | snmpv1 172.16.2.3 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0 | uplink=NAS-01 | NAS-01 |
| Sector_4 | snmpv1 172.16.2.10 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=NAS-01 | NAS-01 |
| Sector_5 | snmpv1 172.16.2.4 | Ubiquiti airMAX M airOS6 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=NAS-01 | NAS-01 |

#### Enlaces PTP Backhaul

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| AP-Lk_Hq_Mayolica_1 | snmpv1 10.155.1.2 | Ubiquiti airMAX M airOS6 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=STA-Lk_Hq_Mayolica_1 | STA-Lk_Hq_Mayolica_1 |
| STA-Lk_Hq_Mayolica_1 | snmpv1 10.155.1.3 | Ubiquiti airMAX M airOS6 wireless by SNMPv1, Ubiquiti AirOS by SNMP | — | uplink=Switch Main Site #01 | Switch Main Site #01 |
| [AP]-Lk_Hq_Pintores_1 | snmpv1 10.155.0.2 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-57, {$UBNT.STA.TXCAP.MIN}=50 | uplink=[CPE]-Lk_Hq_Pintores_1 | [CPE]-Lk_Hq_Pintores_1 |
| [AP]-Lk_Pintores_Canadas_1 | snmpv1 10.155.2.2 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-59, {$UBNT.STA.TXCAP.MIN}=50 | uplink=[CPE]Lk_Pintores_Canadas_1 | [CPE]Lk_Pintores_Canadas_1 |
| [AP]Lk_Hq_Caribe_1 | snmpv1 10.155.3.2 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-64, {$UBNT.STA.SIGNAL.MIN.CRIT}=-70, {$UBNT.STA.TXCAP.MIN}=37 | escalation=off, uplink=[STA]Lk_Hq_Caribe_1 | [STA]Lk_Hq_Caribe_1 |
| [CPE]-Lk_Hq_Pintores_1 | snmpv1 10.155.0.3 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-57, {$UBNT.STA.RXCAP.MIN}=30 | uplink=Switch Main Site #01 | Switch Main Site #01 |
| [CPE]Lk_Pintores_Canadas_1 | snmpv1 10.155.2.3 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-60, {$UBNT.STA.RXCAP.MIN}=50 | uplink=[AP]-Lk_Hq_Pintores_1 | [AP]-Lk_Hq_Pintores_1 |
| [STA]Lk_Hq_Caribe_1 | snmpv1 10.155.3.3 | Ubiquiti AirOS 8 wireless by SNMPv1, Ubiquiti AirOS by SNMP | {$UBNT.GPS.SATS.MIN}=0, {$UBNT.STA.SIGNAL.MIN.WARN}=-67, {$UBNT.STA.SIGNAL.MIN.CRIT}=-73, {$UBNT.STA.RXCAP.MIN}=13 | escalation=off, uplink=Switch Main Site #01 | Switch Main Site #01 |

#### Enlaces PTP Troncales

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| AP-Lk_Trunk_01_A | snmpv2 10.100.0.2 | Mimosa C5C by SNMP, Switch port changes by SNMP, Network Generic Device by SNMP | {$IFCONTROL}=0, {$MIMOSA.RX.POWER.MIN.WARN}=-71, {$MIMOSA.RX.POWER.MIN.CRIT}=-76 | uplink=STA-Lk_Trunk_01_A | STA-Lk_Trunk_01_A |
| STA-Lk_Trunk_01_A | snmpv2 10.100.0.3 | Mimosa C5C by SNMP, Switch port changes by SNMP, Network Generic Device by SNMP | {$IFCONTROL}=0, {$MIMOSA.RX.POWER.MIN.WARN}=-71, {$MIMOSA.RX.POWER.MIN.CRIT}=-76 | uplink=EDGE 01 | EDGE 01 |

#### Likson KPIs

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| KPI Likson |  | Likson KPIs | — | — | — |

#### Linux servers

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| server-04 | agent 192.168.50.254 | Linux by Zabbix agent, Docker by Zabbix agent 2 | {$VFS.FS.FSNAME.MATCHES}=^/rootfs(/\|$), {$VFS.FS.FSNAME.NOT_MATCHES} (regex) | os=linux | — |

#### Routers & Switches Likson

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| EDGE 01 | snmpv2 192.168.200.1 | MikroTik link traps by SNMP, MikroTik CCR2004-16G-2S by SNMP | — | — | Zabbix server |
| NAS-01 | snmpv2 192.168.200.2 | MikroTik link traps by SNMP, MikroTik CCR2004-16G-2S by SNMP | {$NET.IF.IFNAME.NOT_MATCHES} (regex) | — | EDGE 01 |
| NAS-03 | snmpv2 192.168.200.10 | MikroTik link traps by SNMP, MikroTik RB2011iL-RM by SNMP | {$NET.IF.IFNAME.NOT_MATCHES} (regex) | — | EDGE 01 |
| Switch Main Site #01 | snmpv2 172.16.100.2 | Switch port changes by SNMP, TP-LINK by SNMP | {$IFCONTROL}=0, {$PORT.IFNAME.NOT_MATCHES}=^(<\|Vlan-interface) | — | NAS-01 |

#### Zabbix servers

| Host | Interfaz | Plantillas | Macros de host | Etiquetas | Depende de |
|---|---|---|---|---|---|
| Zabbix server | agent 172.16.238.1 | Linux hwmon temperature by Zabbix agent 2, Cloudflare Tunnel by HTTP, Linux by Zabbix agent, Zabbix server health, Website certificate by Zabbix agent 2 | {$VFS.FS.FSNAME.MATCHES}=^/rootfs(/\|$), {$CERT.WEBSITE.HOSTNAME}=zabbix.likson.com, {$CERT.WEBSITE.IP}=127.0.0.1, {$CERT.EXPIRY.WARN}=14, {$VFS.FS.FSNAME.NOT_MATCHES} (regex) | — | — |

IPs de APs: `172.16.1.x` (las `.12` y `.13` no responden y no están dadas de alta), `172.16.2.x` y `172.16.3.x` (la `.14` no responde y no está dada de alta). Las IPs pueden cambiar: [Cambiar la IP de un equipo](procedimientos/cambiar-ip.md).
