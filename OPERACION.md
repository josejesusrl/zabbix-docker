# Operación de Zabbix — zabbix.likson.com

Guía para usar y ampliar Zabbix día a día: qué se monitorea, cómo está organizado, qué plantillas usar y cómo añadir o cambiar equipos.
Todos los procedimientos se pueden hacer desde la interfaz web (`https://zabbix.likson.com`). La instalación, la restauración y las actualizaciones del servidor están en `SERVER_DEPLOY.md`; las reglas del proyecto, en `AGENTS.md`.

> Para automatizar estos procedimientos por la API (alta masiva, cambio de padre, inventario, estado), ver `agents/scripts/README.md`. La interfaz web sigue siendo el método de referencia.

> **Antes de cualquier cambio en Zabbix:** en el servidor, `cd ~/zabbix-docker && sudo ./server_backup.sh`. Esto incluye dar de alta equipos, importar plantillas o cambiar macros (`AGENTS.md`, regla 1).

---

## 1. Organización

### Convenciones

| Elemento | Convención |
|---|---|
| Nombre del host | El nombre de sistema del equipo (`sysName` o *Device Name*), idéntico en *Host name* y *Visible name*. Si el equipo no tiene nombre, se le pone primero en el propio equipo. El *Host name* solo admite letras, dígitos, espacios, `.`, `-` y `_`: si el nombre lleva otros caracteres (p. ej. `[AP]-…`), el *Host name* los omite y el *Visible name* conserva el nombre exacto |
| Grupos de hosts | `Routers & Switches Likson` (MikroTik, switches), `Access Points PPPoE Clients` (APs Ubiquiti), `Enlaces PTP Troncales` y `Enlaces PTP Backhaul` (radios PTP), `Linux servers`, `Zabbix servers` |
| Etiqueta `uplink` | Nombre del equipo del que depende (p. ej. `uplink = EDGE 01`). Sirve para filtrar y como documentación de la dependencia |
| Interfaz SNMP | Comunidad `{$SNMP_COMMUNITY}` (macro global de tipo secreto). MikroTik, TP-Link y Mimosa: SNMPv2. **Ubiquiti: SNMPv1** |
| Dependencias | Cada equipo depende del que le da conectividad hacia Zabbix (sección 4.1) |

### Topología y dependencias actuales

```
Zabbix server (192.168.0.191)                 raíz: su trigger "Interface enp2s0: Link down" es el padre de todo
server-04 (192.168.50.254)                    depende del enlace de red del Zabbix server
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

### Inventario

| Host | IP | Grupo | Plantillas | Macros de host | Depende de |
|---|---|---|---|---|---|
| Zabbix server | 172.16.238.1 (agente) | Zabbix servers | Linux by Zabbix agent, Zabbix server health, Website certificate by Zabbix agent 2, Linux hwmon temperature by Zabbix agent 2 | `{$VFS.FS.FSNAME.*}`, `{$CERT.*}` | — |
| server-04 | 192.168.50.254 | Linux servers | Linux by Zabbix agent, Docker by Zabbix agent 2 | `{$VFS.FS.FSNAME.*}` | — |
| EDGE 01 | 192.168.200.1 | Routers & Switches Likson | MikroTik CCR2004-16G-2S by SNMP, MikroTik link traps by SNMP | — | — |
| NAS-01 | 192.168.200.2 | Routers & Switches Likson | MikroTik CCR2004-16G-2S by SNMP, MikroTik link traps by SNMP | `{$NET.IF.IFNAME.NOT_MATCHES}` (+PPPoE) | EDGE 01 |
| NAS-03 | 192.168.200.10 | Routers & Switches Likson | MikroTik RB2011iL-RM by SNMP, MikroTik link traps by SNMP | `{$NET.IF.IFNAME.NOT_MATCHES}` (+PPPoE) | EDGE 01 |
| Switch Main Site #01 | 172.16.100.2 | Routers & Switches Likson | TP-LINK by SNMP, Switch port changes by SNMP | `{$IFCONTROL}=0`, `{$PORT.IFNAME.NOT_MATCHES}` | NAS-01 |
| LIKSON_HQ_EPSILON_01 | 172.16.1.19 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | — (tiene GPS) | Switch Main Site #01 |
| LIKSON_PDV_3, LK_C3, LIKSON_BETA01, LIKSON_PDV_7, LIKSON_HQ_DELTA_01 | .4, .11, .14, .15, .18 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | — (tienen GPS) | Switch Main Site #01 |
| LIKSON_PDV_1, _2, _4, _6, _9, _10, LKON_SGAMMA01, LK_C2, LK_C4 | .2, .3, .5, .7, .8, .9, .10, .16, .17 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0` (sin GPS) | Switch Main Site #01 |
| LIKSON_PDV_5 (Rocket M5) | 172.16.1.6 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 | — | Switch Main Site #01 |
| Sector_4 (airOS 8, con GPS) | 172.16.2.10 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | — | NAS-01 |
| Sector_3 (airOS 8, sin GPS) | 172.16.2.3 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0` | NAS-01 |
| Sector_5 (NanoStation loco M, airOS 6) | 172.16.2.4 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 | — | NAS-01 |
| LIKSON_CANADAS_A_01, LIKSON_CANADAS_B_01 (airOS 8, con GPS) | 172.16.3.12, .13 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | — | NAS-03 |
| LIKSON_CANADAS_C_01, LIKSON_CANADAS_D_01 (airOS 8, sin GPS) | 172.16.3.10, .11 | Access Points PPPoE Clients | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0` | NAS-03 |
| STA-Lk_Trunk_01_A (Mimosa C5C, estación) | 10.100.0.3 | Enlaces PTP Troncales | Network Generic Device by SNMP, Mimosa C5C by SNMP, Switch port changes by SNMP | `{$IFCONTROL}=0`, `{$MIMOSA.RX.POWER.MIN.WARN}=-71`, `{$MIMOSA.RX.POWER.MIN.CRIT}=-76` | EDGE 01 |
| [CPE]-Lk_Hq_Pintores_1 (LiteBeam 5AC, estación) | 10.155.0.3 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-57`, `{$UBNT.STA.RXCAP.MIN}=30` | Switch Main Site #01 |
| [AP]-Lk_Hq_Pintores_1 (LiteBeam 5AC, AP) | 10.155.0.2 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-57`, `{$UBNT.STA.TXCAP.MIN}=50` | [CPE]-Lk_Hq_Pintores_1 |
| [CPE]Lk_Pintores_Canadas_1 (LiteBeam 5AC, estación) | 10.155.2.3 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-60`, `{$UBNT.STA.RXCAP.MIN}=50` | [AP]-Lk_Hq_Pintores_1 |
| [AP]-Lk_Pintores_Canadas_1 (LiteBeam 5AC, AP) | 10.155.2.2 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-59`, `{$UBNT.STA.TXCAP.MIN}=50` | [CPE]Lk_Pintores_Canadas_1 |
| STA-Lk_Hq_Mayolica_1 (loco M2, estación) | 10.155.1.3 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 | — (umbrales por defecto) | Switch Main Site #01 |
| AP-Lk_Hq_Mayolica_1 (loco M2, AP) | 10.155.1.2 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 | — (umbrales por defecto) | STA-Lk_Hq_Mayolica_1 |
| [STA]Lk_Hq_Caribe_1 (LiteBeam 5AC, estación) | 10.155.3.3 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-67`, `{$UBNT.STA.SIGNAL.MIN.CRIT}=-73`, `{$UBNT.STA.RXCAP.MIN}=13`. Etiqueta `escalation=off` | Switch Main Site #01 |
| [AP]Lk_Hq_Caribe_1 (LiteBeam 5AC, AP) | 10.155.3.2 | Enlaces PTP Backhaul | Ubiquiti AirOS by SNMP, Ubiquiti AirOS 8 wireless by SNMPv1 | `{$UBNT.GPS.SATS.MIN}=0`, `{$UBNT.STA.SIGNAL.MIN.WARN}=-64`, `{$UBNT.STA.SIGNAL.MIN.CRIT}=-70`, `{$UBNT.STA.TXCAP.MIN}=37`. Etiqueta `escalation=off` | [STA]Lk_Hq_Caribe_1 |
| AP-Lk_Trunk_01_A (Mimosa C5C, AP) | 10.100.0.2 | Enlaces PTP Troncales | Network Generic Device by SNMP, Mimosa C5C by SNMP, Switch port changes by SNMP | `{$IFCONTROL}=0`, `{$MIMOSA.RX.POWER.MIN.WARN}=-71`, `{$MIMOSA.RX.POWER.MIN.CRIT}=-76` | STA-Lk_Trunk_01_A |

IPs de APs: `172.16.1.x` (las `.12` y `.13` no responden y no están dadas de alta), `172.16.2.x` y `172.16.3.x` (la `.14` no responde y no está dada de alta). Las IPs pueden cambiar: ver 4.10.

---

## 2. Alertas

### A quién y cómo llegan

| Severidad | Gmail | Telegram | Repetición |
|---|---|---|---|
| Information / Not classified | — | — | — |
| Warning / Average | ✅ | — | Un aviso |
| High / Disaster | ✅ | ✅ | Cada 30 min hasta que se reconozca o se resuelva |

Acciones (*Alerts → Actions → Trigger actions*):

- **Alert by severity:** severidad ≥ Warning. Primer aviso, aviso de "Resuelto" y avisos de reconocimientos y comentarios.
- **Escalate unacknowledged High/Disaster:** repite los *High/Disaster* no reconocidos cada 30 min, **excepto** los problemas con la etiqueta `escalation` (condición *Tag name does not equal escalation*).
- *Report problems to Zabbix administrators:* **desactivada** a propósito (duplicaba los avisos).

El reparto por canal se hace en el usuario: *User settings → Profile → Media*, severidades de cada medio.

Los medios (Gmail y Telegram) reintentan **10 veces cada 30 s** (*Alerts → Media types → Options*): un corte de red del servidor de hasta 5 min no pierde notificaciones.

### Avisar una sola vez: etiqueta `escalation=off`

En equipos cuyos problemas duran horas por causas conocidas (p. ej. un enlace que se degrada con la lluvia), añadir al host la etiqueta **`escalation` = `off`** (*Host → Tags*). Sus problemas *High* avisan al empezar y al resolverse, pero no se repiten cada 30 min. Las etiquetas del host se heredan en todos sus problemas.

### Qué hacer con un problema

En *Monitoring → Problems* → *Update* sobre el problema:

- **Acknowledge:** indica que se está atendiendo y detiene la repetición cada 30 min. Se puede añadir un comentario, que se notifica.
- **Close problem:** solo en los triggers que lo permiten. Se usa en los que no se resuelven solos: cambio de velocidad de un puerto, o un *linkDown* por trap cuyo *linkUp* se perdió.

### Silenciar durante trabajos programados

*Data collection → Maintenance → Create maintenance period*: tipo *With data collection*, hosts o grupos afectados y horario. Durante el mantenimiento no se envían avisos, pero se siguen recogiendo datos.

---

## 3. Catálogo de plantillas

### 3.1 Plantillas propias (en `zabbix_templates/`)

#### Mimosa C5C by SNMP — `mimosa_c5c.yaml`
**Para:** radios Mimosa C5C (y familia B5/C5) en enlaces PTP, con SNMPv2. Se usa **junto con** la oficial *Network Generic Device by SNMP*, que aporta interfaces con tráfico de 64 bits, ping, disponibilidad SNMP y reinicios, y con *Switch port changes by SNMP* para el puerto Ethernet del radio.
**Recoge:** estado y uptime del enlace, modo (AP/estación), potencia RX/TX total, potencia RX, ruido y SNR por polarización (H/V), velocidad PHY, MCS y EVM por stream, tasa de errores de paquete (PER) TX/RX, frecuencia, ancho de canal, temperatura, firmware y número de serie.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Wireless link is disconnected | High | El enlace radio cae | Al reconectar |
| Wireless link was re-established | Warning | El enlace lleva menos de `{$MIMOSA.LINK.UPTIME.MIN}` s (600) conectado: hubo un corte | Solo, pasados 10 min |
| Very low RX power | High | Potencia RX total < `{$MIMOSA.RX.POWER.MIN.CRIT}` durante 10 min | Solo |
| Low RX power | Warning | < `{$MIMOSA.RX.POWER.MIN.WARN}` durante 10 min. Silenciado si hay crítico | Solo |
| RX chain imbalance | Warning | Diferencia H/V > `{$MIMOSA.CHAIN.DIFF.MAX}` (6 dB) durante 30 min: cable, conector o alineación | Solo |
| Low SNR | Warning | SNR de alguna cadena < `{$MIMOSA.SNR.MIN.WARN}` (12 dB) durante 15 min | Solo |
| High noise | Warning | Ruido > `{$MIMOSA.NOISE.MAX.WARN}` (-85 dBm) durante 15 min: interferencia | Solo |
| High packet error rate | Warning | PER TX o RX > `{$MIMOSA.PER.MAX.WARN}` (10 %) durante 15 min | Solo |
| Low TX PHY rate / Low RX PHY rate | High | Velocidad PHY total (suma de los 2 streams) de ese sentido < `{$MIMOSA.PHY.MIN.WARN}` (200 Mbps) durante 10 min: la modulación cayó y el troncal perdió capacidad | Solo, al recuperarse |
| Temperature is high / critical | Warning / High | > `{$MIMOSA.TEMP.MAX.WARN}` (70 °C) / `{$MIMOSA.TEMP.MAX.CRIT}` (80 °C) durante 5 min | Solo |
| Firmware version has changed | Information | Cambio de firmware (solo registro, no notifica) | Sola |

Los triggers de potencia, SNR, ruido, desequilibrio, PER y velocidad PHY se silencian mientras el enlace está caído. Cada extremo vigila su TX y su RX, así que con los dos hosts se cubren ambos sentidos del enlace desde el emisor y desde el receptor. Se usa la velocidad PHY por sentido y no la velocidad de `wifi0`, que es una sola cifra sin dirección.
**Umbrales de potencia por enlace:** `{$MIMOSA.RX.POWER.MIN.WARN}` ≈ señal de diseño − 6 dB y `CRIT` ≈ diseño − 11 dB. Para `Lk_Trunk_01_A` (diseño -65 dBm): -71 / -76.

#### Ubiquiti AirOS 8 wireless by SNMPv1 — `ubiquiti_airos8_wireless.yaml`
**Para:** APs Ubiquiti airMAX AC con airOS 8 (LAP-GPS, LiteAP, Rocket AC, Prism…). Se usa **junto con** la oficial *Ubiquiti AirOS by SNMP*, que aporta CPU, memoria, uptime y ping.
**Recoge:** clientes conectados, señal, ruido, CCQ, velocidades, ancho de canal, frecuencia, potencia, airMAX, GPS (fix, satélites, HDOP), tráfico de `eth0` y `ath0` y, por cada cliente, señal, distancia, CCQ, CINR, capacidad, velocidades y tiempo conectado.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| AP has no connected clients | Average | Tenía clientes en la última hora y ahora tiene 0 | Al volver a tener clientes |
| High noise floor | Warning | Ruido > `{$UBNT.NOISE.MAX.WARN}` (-80 dBm) durante 15 min | Solo |
| GPS: Weak or lost signal | Warning | < `{$UBNT.GPS.SATS.MIN}` (4) satélites durante 10 min | Solo |
| Client …: Very weak signal | High | Señal del cliente < `{$UBNT.STA.SIGNAL.MIN.CRIT}` durante 5 min (p. ej. lluvia). **Desactivado con 0** (defecto) | Cuando la señal se mantiene 30 min al menos `{$UBNT.STA.SIGNAL.HYST}` (3 dB) por encima del umbral |
| Client …: Weak signal | Warning | Señal del cliente < `{$UBNT.STA.SIGNAL.MIN.WARN}` (-75 dBm) durante 15 min. Silenciado si hay *Very weak signal* | Cuando la señal se mantiene 15 min 3 dB por encima del umbral |
| Client …: Low TX / RX capacity | High | Capacidad airMAX de TX o RX con ese cliente < `{$UBNT.STA.TXCAP.MIN}` / `{$UBNT.STA.RXCAP.MIN}` (Mbps) durante 10 min. **Desactivado con 0** (defecto); se activa por host o por cliente, normalmente en enlaces PTP | Cuando la capacidad se mantiene 10 min por encima del mínimo |
| Interface eth…: Speed changed | High | Cambia la velocidad Ethernet negociada de `eth0` (p. ej. 1000 → 100 Mbps: cable, conector o PoE). Solo se crea para interfaces `eth*` (regla *override* del descubrimiento): en airOS 6 `ath0` reporta una velocidad de radio que no debe vigilarse | Manualmente |

| Macro | Defecto | Uso |
|---|---|---|
| `{$UBNT.NOISE.MAX.WARN}` | -80 | Umbral de ruido |
| `{$UBNT.STA.SIGNAL.MIN.WARN}` | -75 | Umbral de señal de cliente. Por cliente: `{$UBNT.STA.SIGNAL.MIN.WARN:"<nombre del cliente>"}` |
| `{$UBNT.GPS.SATS.MIN}` | 4 | **Poner `0` en APs sin GPS**: devuelven 0 satélites y la alerta saltaría siempre |
| `{$UBNT.IF.MATCHES}` | `^(eth0\|ath0)$` | Interfaces con tráfico |
| `{$UBNT.STA.TXCAP.MIN}` / `{$UBNT.STA.RXCAP.MIN}` | 0 | Capacidad mínima en Mbps (0 = desactivado). Contexto por cliente: `{$UBNT.STA.TXCAP.MIN:"<nombre del cliente>"}` |
| `{$UBNT.STA.SIGNAL.MIN.CRIT}` | 0 | Señal crítica en dBm (0 = desactivado) |
| `{$UBNT.STA.SIGNAL.HYST}` | 3 | dB que la señal debe recuperar por encima del umbral para cerrar el problema. Evita avisos repetidos cuando la señal oscila (lluvia) |

#### Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 — `ubiquiti_airmax_m_airos6_wireless.yaml`
**Para:** equipos airMAX M con airOS 6 (Rocket M5, NanoStation M…). Es la misma plantilla que la de airOS 8, pero **sin** GPS, CINR ni capacidad de cliente, que son exclusivos de AC. Añade **airMAX quality y capacity** del AP y por cliente, que en airMAX M son las mejores medidas de calidad.
Mismos triggers y macros, salvo los de GPS y capacidad (airOS 6 no la publica); incluye el de cambio de velocidad de `eth0`. El CCQ viene en porcentaje directo. No recoge el tiempo de conexión del cliente (limitación de SNMPv1 en airOS 6).

#### MikroTik link traps by SNMP — `mikrotik_link_traps.yaml`
**Para:** routers MikroTik, junto con su plantilla oficial de modelo. Alerta **al instante** cuando cae un enlace, a partir del trap `linkDown`.
**Requisitos en el router:** traps configurados y `src-address` igual a la IP del host en Zabbix (sección 4.3).

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Interface X(comentario): Link down (SNMP trap) | Average | Llega un `linkDown` con la interfaz habilitada. Si se deshabilita a mano, no alerta | Con el trap `linkUp`, o manualmente |

| Macro | Defecto | Uso |
|---|---|---|
| `{$LINKTRAP.IFALIAS.MATCHES}` | `.+` | Solo interfaces **con comentario** en RouterOS. Para quitar una interfaz, borrar su comentario o ajustar la regex (p. ej. `^(?!.*RESERVED)`) |
| `{$LINKTRAP.IFNAME.NOT_MATCHES}` | `^<` | Excluye interfaces dinámicas (PPPoE, túneles) |

Complementa, no sustituye, el *Link down* por consulta de la plantilla oficial (cada pocos minutos). Si el trap se pierde, la consulta lo detecta. Una misma caída puede generar los dos avisos.

#### Switch port changes by SNMP — `switch_port_changes.yaml`
**Para:** switches cuyos puertos son críticos, de cualquier fabricante. Consulta el estado y la velocidad de todos los puertos Ethernet cada 30 s en una sola lectura SNMP.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Port X: Flapping | High | ≥ `{$PORT.FLAP.COUNT}` (4) cambios de estado en `{$PORT.FLAP.PERIOD}` (10 min) | Solo, cuando cesan los cambios |
| Port X: Disconnected | High | El puerto pasa de conectado a desconectado estando habilitado. Silenciado mientras hay *Flapping* | Al reconectar, o manualmente |
| Port X: Negotiated speed changed | High | Cambia la velocidad con el enlace activo (p. ej. 1000 → 100 Mbps). El título indica ambas velocidades | Manualmente, tras revisar |

| Macro | Defecto | Uso |
|---|---|---|
| `{$PORT.POLL.INTERVAL}` | 30s | Frecuencia de consulta |
| `{$PORT.FLAP.COUNT}` / `{$PORT.FLAP.PERIOD}` | 4 / 10m | Sensibilidad del flapping |
| `{$PORT.IFTYPE.MATCHES}` | `^6$` | Solo puertos Ethernet |
| `{$PORT.IFNAME.NOT_MATCHES}` | `^(<\|wifi\|wlan\|ath\|br[0-9])` | Puertos excluidos: interfaces dinámicas, de radio (su velocidad es la capacidad inalámbrica, que cambia continuamente) y bridges virtuales. En TP-Link: `^(<\|Vlan-interface)` |

Requiere **SNMPv2** (lee `ifXTable`): no sirve para Ubiquiti airOS, que solo responde a SNMPv1. En airOS, el cambio de velocidad de `eth0` lo vigilan sus propias plantillas. Al usarla, poner `{$IFCONTROL}=0` en el host para que el *Link down* de la plantilla del fabricante no duplique los avisos de desconexión. Los cortes de menos de 30 s pueden no detectarse; los repetidos, sí (flapping).

#### Linux hwmon temperature by Zabbix agent 2 — `linux_hwmon_temperature.yaml`
**Para:** servidores Linux físicos con Agent 2. Descubre cada sensor de temperatura del kernel (CPU, GPU, NVMe…).
**Requisitos en el servidor:** lm-sensors instalado (`sensors-detect`) y los ficheros `zabbix_agentd.d/sensors_hwmon.conf` y `sensors_hwmon.sh` en el directorio `Include` del agente. En el servidor Zabbix ya están.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Temperature X is critical | High | ≥ `{$TEMP.CRIT}` (85 °C) durante 5 min |
| Temperature X is high | Warning | ≥ `{$TEMP.WARN}` (75 °C) durante 5 min. Silenciado si ya hay crítico |
| Temperature X: no data for 30m | Warning | El sensor deja de reportar |

Umbrales por chip: `{$TEMP.CRIT:"nvme"}=70`.

### 3.2 Plantillas oficiales en uso y ajustes necesarios

| Plantilla | Para | Ajustes |
|---|---|---|
| *MikroTik \<modelo\> by SNMP* | Routers MikroTik. Usar la del modelo exacto; si no existe, *Mikrotik by SNMP* | En concentradores PPPoE, excluir sesiones (4.3) |
| *TP-LINK by SNMP* | Switches TP-Link | Con *Switch port changes*: `{$IFCONTROL}=0` |
| *Ubiquiti AirOS by SNMP* | APs Ubiquiti (sistema: CPU, memoria, ping) | En airOS 8, *Firmware version* y *Hardware model name* quedan como no soportados (airOS 8 no publica esos datos). Es normal |
| *Linux by Zabbix agent* | Servidores Linux | Si el agente corre en un contenedor con `/rootfs`: macros de sistemas de archivos (4.5) |
| *Docker by Zabbix agent 2* | Servidores con Docker | El agente necesita acceso a `/var/run/docker.sock`. Solo descubre los contenedores en ejecución |
| *Website certificate by Zabbix agent 2* | Caducidad del certificado de `zabbix.likson.com` (host Zabbix server) | `{$CERT.WEBSITE.HOSTNAME}`, `{$CERT.WEBSITE.IP}=127.0.0.1`, `{$CERT.EXPIRY.WARN}=14` |

---

## 4. Procedimientos

### 4.1 Configurar las dependencias de un host

Las dependencias evitan recibir decenas de alertas cuando cae un equipo del que dependen otros: solo avisa el equipo de arriba.

1. Identificar el equipo del que depende (su uplink hacia Zabbix) y su trigger **"Unavailable by ICMP ping"**.
2. *Data collection → Hosts* → columna **Triggers** del host nuevo → marcar estos triggers:
   - `Unavailable by ICMP ping`
   - `High ICMP ping loss`
   - `High ICMP ping response time`
   - `No SNMP data collection` (en equipos SNMP)
3. **Mass update** → pestaña **Dependencies** → opción **Add** (no *Replace*) → **Add** → elegir el host padre y su trigger *Unavailable by ICMP ping* → **Update**.
   - ⚠️ **Nunca usar *Replace*.** Las plantillas oficiales traen dependencias internas que evitan alertas duplicadas cuando cae el equipo: *High ICMP ping loss*, *High ICMP ping response time* y *No SNMP data collection* dependen del *Unavailable by ICMP ping* del propio host. *Replace* las borra, y al caer el equipo llegarían 3–4 alertas en lugar de una.
   - Para **cambiar** de padre: *Mass update* → **Remove** con el trigger del padre anterior, y después **Add** con el nuevo.
4. En APs Ubiquiti, además: el trigger **"Wireless: AP has no connected clients"** depende del *Unavailable by ICMP ping* **del propio AP**, para que un AP caído no avise también por "sin clientes".
5. Añadir la etiqueta `uplink = <host padre>` en la pestaña *Tags* del host.
6. **Equipos raíz** (sin padre en la red, p. ej. EDGE 01 o un servidor directo): su trigger de disponibilidad (*Unavailable by ICMP ping* o *Zabbix agent is not available*) depende de **Zabbix server: Interface enp2s0: Link down**. Si cae la red del propio servidor Zabbix, no se reporta toda la red como caída.

Para configurar varios hosts a la vez, filtrar en *Data collection → Triggers* por grupo o etiqueta y por nombre, seleccionarlos todos y usar **Mass update**.

### 4.2 Añadir un AP Ubiquiti

**En el AP (airOS):**
1. *Services* → **SNMP Agent**: activar. Poner la comunidad de lectura (la misma que `{$SNMP_COMMUNITY}`), *Contact* y *Location*. **Save** y **Apply**.
2. *System* → *Device Name*: el nombre con el que aparecerá en Zabbix.
3. Anotar el modelo y si tiene GPS (en la LAP-GPS, *Main* muestra el GPS).

**En Zabbix** (respaldo antes):
1. *Data collection → Hosts → Create host*:
   - **Host name** y **Visible name:** el *Device Name* del AP.
   - **Host groups:** `Access Points PPPoE Clients`.
   - **Interfaces → Add → SNMP:** IP del AP, puerto 161, **SNMP version: SNMPv1**, *SNMP community* `{$SNMP_COMMUNITY}`.
   - **Templates:**
     - airOS 8 (AC): `Ubiquiti AirOS by SNMP` + `Ubiquiti AirOS 8 wireless by SNMPv1`.
     - airOS 6 (M5, series M): `Ubiquiti AirOS by SNMP` + `Ubiquiti airMAX M (airOS 6) wireless by SNMPv1`.
   - **Macros** (solo AC **sin** GPS): `{$UBNT.GPS.SATS.MIN}` = `0`.
   - **Tags:** `uplink` = equipo del que cuelga.
2. **Add**. Configurar las dependencias (4.1), incluida la de "AP has no connected clients".
3. **Verificar** (unos 5 min):
   - En *Data collection → Hosts*, el icono **SNMP** en verde.
   - En *Monitoring → Latest data*, filtrado por el host: *Connected clients* igual al número de clientes que muestra airOS, y un grupo de items *Client …* por cada uno.
   - *Firmware version* y *Hardware model name* no soportados es normal en airOS 8. Cualquier otro item no soportado se revisa en la sección 5.

**Por qué SNMPv1:** airOS ignora las consultas SNMPv2c aunque la comunidad sea correcta, y el host aparece como no disponible.

### 4.3 Añadir un router MikroTik

**En el router (terminal de RouterOS):**
```routeros
# Comunidad de lectura solo desde Zabbix (se reutiliza la entrada "public" por defecto)
/snmp community set [find default=yes] name=<lectura> addresses=192.168.0.191/32 read-access=yes write-access=no
# Comunidad de traps (la de server_setup.sh), sin lectura
/snmp community add name=<traps> addresses=192.168.0.191/32 read-access=no write-access=no
/snmp set enabled=yes contact="..." location="..." trap-version=2 trap-community=<traps> \
    trap-target=192.168.0.191 trap-generators=interfaces,start-trap,temp-exception trap-interfaces=all \
    src-address=<IP del router que se dará de alta en Zabbix>
# Si el firewall de input descarta por defecto:
/ip firewall filter add chain=input protocol=udp dst-port=161 src-address=192.168.0.191 action=accept comment="Zabbix SNMP" place-before=0
```
- `src-address` es imprescindible: si falta, el trap sale con la IP de la interfaz de salida y Zabbix lo descarta como *unmatched trap*.
- Poner **comentario** a las interfaces importantes (*Interfaces → Comment*): son las que reciben alertas inmediatas por trap.

**En Zabbix:**
1. *Create host*: nombre = *Identity* del router, grupo `Routers & Switches Likson`, interfaz **SNMP** (IP, 161, **SNMPv2**, `{$SNMP_COMMUNITY}`).
2. **Templates:** `MikroTik <modelo> by SNMP` (o `Mikrotik by SNMP`) + `MikroTik link traps by SNMP`.
3. **Si el router no tiene radios** (CCR, RB2011…): en *Items*, desactivar *SNMP walk wireless interfaces*. Lee de nuevo toda la tabla de interfaces cada minuto para nada.
   **Si es concentrador PPPoE (NAS):** en la interfaz SNMP, *Max repetition count* = `50` (defecto 10). Con cientos de sesiones, la tabla de interfaces se lee con 5 veces menos peticiones y se evitan los timeouts cuando el router tiene la CPU alta.
   **Además, en un NAS:** en *Macros* → *Inherited and host macros*, copiar `{$NET.IF.IFNAME.NOT_MATCHES}` y añadir `|^<pppoe-` **antes del paréntesis final**. Si no, cada sesión de cliente se descubre como interfaz y los items crecen sin control.
4. Dependencias (4.1) y etiqueta `uplink`.
5. **Verificar:** SNMP en verde. En *Latest data*, interfaces sin `<pppoe-…>` (en un NAS, el filtro tarda hasta 1 h en aplicarse). Prueba de traps: deshabilitar y habilitar una interfaz **sin uso** con comentario:
   ```routeros
   /interface disable etherX; :delay 5s; /interface enable etherX
   ```
   Aparecerá en *Latest data* → *SNMP traps* del host, o en el trigger *Link down (SNMP trap)*.

### 4.4 Añadir un switch con vigilancia de puertos

1. En el switch: activar SNMP (v2c) con la comunidad de lectura, accesible desde 192.168.0.191.
2. *Create host*: grupo `Routers & Switches Likson`, interfaz **SNMP** (SNMPv2, `{$SNMP_COMMUNITY}`).
3. **Templates:** la del fabricante (p. ej. `TP-LINK by SNMP`) + `Switch port changes by SNMP`.
4. **Macros:** `{$IFCONTROL}` = `0`. En TP-Link, `{$PORT.IFNAME.NOT_MATCHES}` = `^(<|Vlan-interface)`.
5. Dependencias (4.1).
6. **Verificar:** en *Latest data*, items *Port …: Operational status / Negotiated speed* con valores (`up`/`down`, 1000/100 Mbps). Desconectar un puerto no crítico 5 s → *Port X: Disconnected* y luego resuelto.

### 4.5 Añadir un servidor Linux

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

### 4.6 Ajustar umbrales

Las plantillas propias usan macros; los umbrales se cambian **en el host**, sin tocar la plantilla:

1. Host → pestaña **Macros** → *Inherited and host macros* → **Change** en la macro → nuevo valor → **Update**.
2. Con **contexto**, solo para un elemento concreto:
   - `{$UBNT.STA.SIGNAL.MIN.WARN:"NOMBRE_CLIENTE"}` = `-80`: un cliente lejano con señal débil aceptable.
   - `{$TEMP.CRIT:"nvme"}` = `70`: umbral propio para los discos NVMe.
3. Para cambiar el valor por defecto en todos los hosts, se edita la macro en la plantilla (4.8).

### 4.7 Configurar el envío de traps desde un equipo nuevo

1. Destino de traps: `192.168.0.191` (o `zabbix.likson.com`), puerto **162/udp**, SNMPv2c, comunidad de traps.
2. El trap debe salir con la misma IP que la interfaz SNMP del host en Zabbix.
3. Comprobar la llegada en el servidor:
   ```sh
   cd ~/zabbix-docker && docker compose --env-file .env --env-file server.env exec zabbix-snmptraps tail -8 /var/lib/zabbix/snmptraps/snmptraps.log
   ```
   Debe aparecer `ZBXTRAP <IP del equipo>`. Los traps sin host coincidente se registran en el log del server como *unmatched trap*.
4. Si se ha olvidado la comunidad de traps: `sudo awk '/^authCommunity/{print $3}' ~/zabbix-docker/snmptraps/snmptrapd.conf`.

### 4.8 Crear o modificar una plantilla propia

1. Editar el YAML en `zabbix_templates/` (reglas de formato en `AGENTS.md`, regla 6), hacer commit y push, y documentar el cambio en esta guía.
2. Respaldo en el servidor.
3. *Data collection → Templates → Import* → elegir el YAML. Marcar **Update existing** y **Create new**. Para que se eliminen items, triggers o prototipos que ya no están en el YAML, marcar también **Delete missing** en *Items*, *Discovery rules* y *Triggers*.
4. Verificar en un host que la usa: items con datos y sin no soportados nuevos.

No editar las plantillas propias desde la interfaz: el cambio se perdería al reimportar el YAML. Las plantillas oficiales tampoco se editan; se ajustan con macros de host.

### 4.9 Dar de baja un equipo

- **Temporal** (equipo apagado o en reparación): *Data collection → Hosts* → estado **Disabled**. Se conserva el historial.
- **Definitiva:** antes, revisar qué hosts dependen de él (etiqueta `uplink`, sección 1) y reasignar sus dependencias. Después, **Delete**. Se pierde su historial.
- Actualizar el inventario y la topología de esta guía.

### 4.10 Cambiar la IP de un equipo

Las dependencias, el historial y las alertas van ligados al **host**, no a su IP. Cambiar la IP no rompe nada:

1. Respaldo.
2. *Data collection → Hosts* → host → pestaña **Host** → *Interfaces*: nueva IP → **Update**.
3. Si es un MikroTik que envía traps, actualizar también `/snmp set src-address=<nueva IP>`: los traps se asocian por la IP de la interfaz.
4. Si otros equipos filtran por IP la comunicación con Zabbix (comunidades SNMP con `addresses`, `Server=` de agentes), revisar que sigan apuntando a `192.168.0.191`. Solo cambia la IP del equipo monitoreado, no la de Zabbix.
5. Actualizar el inventario de esta guía y **verificar** que el icono SNMP/ZBX vuelve a verde.

### 4.11 Añadir un enlace PTP Mimosa

**En los radios** (los dos extremos): activar SNMP v2c con la comunidad de lectura, en la sección de gestión SNMP del radio (firmware 2.x: *Preferences → Management*). Anotar la **señal de diseño** (RSL) del enlace.

**En Zabbix** (respaldo antes):
1. Crear **primero el extremo más cercano a Zabbix**: los dependientes necesitan que su padre exista.
2. *Create host* para cada extremo:
   - Nombre = *Device Name* del radio. Grupo `Enlaces PTP Troncales`.
   - Interfaz **SNMP** (IP, 161, **SNMPv2**, `{$SNMP_COMMUNITY}`).
   - **Templates:** `Network Generic Device by SNMP` + `Mimosa C5C by SNMP` + `Switch port changes by SNMP`.
   - **Macros:** `{$IFCONTROL}` = `0`, `{$MIMOSA.RX.POWER.MIN.WARN}` = diseño − 6 y `{$MIMOSA.RX.POWER.MIN.CRIT}` = diseño − 11.
3. **Dependencias (4.1):** el extremo lejano depende del cercano (si no hay conexión con el cercano, tampoco con el lejano), y el cercano depende del equipo que le da conectividad hacia Zabbix.
4. **Verificar:** SNMP en verde, *Link: Status = connected*, potencias y SNR con valores reales en *Latest data*, y en *Switch port changes* solo el puerto Ethernet (`eth1_emac1`), no `wifi0`.

### 4.12 Añadir un enlace PTP Ubiquiti (airOS)

Para enlaces punto a punto con equipos airMAX AC (LiteBeam, PowerBeam, Rocket…). Cada enlace tiene **sus propios umbrales**, que se ponen como macros en sus hosts, no en la plantilla.

1. **En los radios:** SNMP activado (4.2) y anotar la **capacidad mínima aceptable** en cada sentido y la señal normal.
2. **Crear primero el extremo más cercano a Zabbix**, y después el lejano (4.2):
   - Grupo `Enlaces PTP Backhaul` (o `Troncales`), **SNMPv1**, plantillas `Ubiquiti AirOS by SNMP` + `Ubiquiti AirOS 8 wireless by SNMPv1`.
   - Si el nombre lleva caracteres no válidos (`[AP]`), *Host name* sin ellos y *Visible name* exacto.
3. **Macros de cada host:**
   - `{$UBNT.GPS.SATS.MIN}` = `0` si no tiene GPS.
   - `{$UBNT.STA.SIGNAL.MIN.WARN}` ≈ señal normal − 7 dB.
   - Capacidad: en ambos radios SNMP reporta el mismo par de valores, **TX = capacidad AP→estación** y **RX = estación→AP**. Para no duplicar alertas, cada sentido se vigila en un solo host: en el **AP** `{$UBNT.STA.TXCAP.MIN}` (capacidad del AP) y en la **estación** `{$UBNT.STA.RXCAP.MIN}` (capacidad de la estación).
4. **Dependencias (4.1):** extremo lejano → extremo cercano → equipo que da conectividad al cercano. Si el enlace cae, avisa el lejano por ping (*High*).
5. **Verificar** en *Latest data*: *Client …: TX/RX capacity* con los valores de la interfaz de airOS, y en *Triggers* los de capacidad con el umbral correcto en el nombre.

Ejemplo `Lk_Hq_Pintores_1`: AP `{$UBNT.STA.TXCAP.MIN}=50`, estación `{$UBNT.STA.RXCAP.MIN}=30`, señal normal -50 → aviso -57.

**Enlaces sensibles a la lluvia** (ej. `Lk_Hq_Caribe_1`):
- Activar además `{$UBNT.STA.SIGNAL.MIN.CRIT}` ≈ señal normal − 13 dB (*High*), dejando el aviso ≈ normal − 7 dB (*Warning*).
- Añadir la etiqueta `escalation=off` a los dos hosts.
- Con la histéresis de la plantilla, una lluvia de ~2 h produce **un aviso al empezar y otro al terminar**, sin repeticiones ni avisos por cada oscilación.
- Capacidades de Caribe: 20 % de la capacidad medida al darlo de alta (AP 183.6 → 37 Mbps; estación 63.7 → 13 Mbps).

### 4.13 Revisar falsos positivos y salud del monitoreo

Conviene hacerlo tras cada alta de equipos y periódicamente:
1. *Monitoring → Problems* con *Show: History* de las últimas 24 h, agrupando por trigger. Un trigger que se abre muchas veces indica umbral mal ajustado o *flapping*. Por API: `agents/scripts/zbx_events.py --hours 24`.
2. *Data collection → Hosts*: iconos de disponibilidad en rojo e items no soportados. Por API: `zbx_host_status.py --details`.
3. Log del server: `docker compose --env-file .env --env-file server.env logs --since 12h zabbix-server | grep -iE "timed out|not supported|failed"`. Muchos *timed out* de un equipo = equipo sobrecargado o lecturas demasiado grandes (ver 4.3, NAS).
4. Corregir con los mecanismos de esta guía (macros, dependencias, *overrides*). Desactivar un objeto solo si es inútil por diseño, y registrarlo en la tabla de la sección 6.

---

## 5. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Host SNMP no disponible (*timed out*) y el ping responde | Versión SNMP incorrecta (Ubiquiti solo v1), comunidad distinta, SNMP desactivado o firewall del equipo | Probar SNMPv1 en la interfaz. Revisar la comunidad y la regla de input del 161 |
| Traps que no aparecen en el host | `src-address` distinto de la IP del host. Comunidad de traps incorrecta | Log del server (*unmatched trap from …*): configurar `src-address`. Si no llega nada al log de traps, revisar comunidad y destino |
| NAS con cientos de interfaces `<pppoe-…>` | Falta la exclusión de PPPoE | 4.3, paso 3. Las sesiones se desactivan en ≤ 1 h y se borran a los 7 días |
| Alerta de GPS en un AP sin GPS | Falta `{$UBNT.GPS.SATS.MIN}=0` | 4.2 |
| AP airOS 6 sin datos de clientes (*noSuchName*) | En SNMPv1, leer la última columna del MIB falla | Usar la plantilla airMAX M (no lee esa columna) |
| Discos "fantasma" (`/etc/hosts`, `/var/lib/zabbix/…`) en un servidor | Agente en contenedor | Macros de sistemas de archivos (4.5). Se aplican en ≤ 1 h |
| *Firmware version* / *Hardware model name* no soportados en APs AC | airOS 8 no los publica | Normal, ignorar |
| El cambio de una macro no se refleja en el descubrimiento | Las reglas de descubrimiento reprocesan como mucho 1 vez por hora si el resultado no cambia | Esperar hasta 1 h |
| Aviso duplicado de desconexión en un switch | Falta `{$IFCONTROL}=0` con *Switch port changes* | 4.4, paso 4 |
| Muchos *timed out* SNMP en el log y datos con huecos en un MikroTik, sobre todo cuando su CPU está alta | La lectura de la tabla de interfaces (con todas las sesiones PPPoE) es grande y el router responde tarde | 4.3: *Max repetition count* = 50 y desactivar *SNMP walk wireless interfaces* si no tiene radios. Si persiste, el router está saturado (hardware) |
| A la vez saltan *Unavailable* en EDGE 01, NAS-01… sin fallo real | Cayó la red del propio servidor Zabbix (log del kernel: `enp2s0: Link is Down`) | Dependencia de los equipos raíz sobre *Zabbix server: Interface enp2s0: Link down* (4.1, paso 6). Revisar el cable del servidor si renegocia a 100 Mbps (*downshifted*) |
| Un problema sigue abierto aunque su item o trigger ya no se descubre o está desactivado | Zabbix no cierra los problemas de triggers desactivados por el descubrimiento | *Monitoring → Problems → Update → Close problem* con un comentario. Por API: `zbx_close_problems.py` |
| Alertas continuas "speed changed" en la interfaz de radio (`wifi0`, `ath0`) | La vigilancia de puertos incluía una interfaz inalámbrica, cuya velocidad es adaptativa | La plantilla ya las excluye por defecto. Si un host tiene su propio `{$PORT.IFNAME.NOT_MATCHES}`, incluir `wifi\|wlan\|ath`. Cerrar los problemas falsos (*Update → Close problem*) |
| Al caer un equipo llegan varias alertas (ping, pérdida, latencia, SNMP) en vez de una | Se usó *Replace* al configurar dependencias y se borraron las internas de la plantilla | En cada trigger (*Dependencies*): *High ICMP ping loss* y *No SNMP data collection* → *Unavailable by ICMP ping* propio; *High ICMP ping response time* → *Unavailable by ICMP ping* y *High ICMP ping loss* propios |

---

## 6. Objetos desactivados a propósito

No son errores. Se desactivaron porque no aplican a ese equipo y solo generaban ruido. Si se reactiva alguno, hay que actualizar esta tabla.

| Host | Objeto | Motivo |
|---|---|---|
| Zabbix server | Items de *connector*, *ipmi*, *vmware* (plantilla *Zabbix server health*) | Esos procesos del server no están activados. Los items siempre serían no soportados |
| Zabbix server, server-04 | *Number of installed packages* | El agente corre en un contenedor y no puede leer la base de paquetes del host (en server-04, además, el agente 6.0 no conoce la clave) |
| Zabbix server | *Interface wlp3s0: Speed* | Tarjeta WiFi del portátil sin uso, no informa de velocidad |
| server-04 | *Interface enp2s0: Speed* | La tarjeta informa de velocidad desconocida (-1) |
| server-04 | *Kernel memory enabled*, *Kernel memory TCP enabled* (Docker) | Las versiones recientes de Docker ya no publican ese dato |
| NAS-01, NAS-03 | *SNMP walk wireless interfaces* | Routers sin radios. Leía cada minuto toda la tabla de interfaces (con las sesiones PPPoE) y sobrecargaba el router |
| AP-Lk_Trunk_01_A, STA-Lk_Trunk_01_A | Trigger *Interface wifi0(): Ethernet has changed to lower speed* (plantilla *Network Generic Device*) | La velocidad de `wifi0` es la capacidad radio adaptativa y cambia continuamente. La capacidad se vigila con los triggers de velocidad PHY de *Mimosa C5C* |
| server-04 | Discos `/etc/hosts`, `/etc/hostname`, `/etc/resolv.conf`, `/etc/zabbix/zabbix_agentd.d` | No descubiertos por las macros `{$VFS.FS.FSNAME.*}` (montajes del contenedor). Se borran solos a los 7 días |
