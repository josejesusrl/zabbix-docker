# Operación de Zabbix — zabbix.likson.com

Guía para usar y ampliar Zabbix día a día: qué se monitorea, cómo está organizado, qué plantillas usar y cómo añadir o cambiar equipos.
Todos los procedimientos se pueden hacer desde la interfaz web (`https://zabbix.likson.com`). La instalación, la restauración y las actualizaciones del servidor están en `SERVER_DEPLOY.md`; las reglas del proyecto, en `AGENTS.md`.

> **Antes de cualquier cambio en Zabbix:** en el servidor, `cd ~/zabbix-docker && sudo ./server_backup.sh`. Esto incluye dar de alta equipos, importar plantillas o cambiar macros (`AGENTS.md`, regla 1).

---

## 1. Organización

### Convenciones

| Elemento | Convención |
|---|---|
| Nombre del host | El nombre de sistema del equipo (`sysName` o *Device Name*), idéntico en *Host name* y *Visible name*. Si el equipo no tiene nombre, se le pone primero en el propio equipo |
| Grupos de hosts | `Routers & Switches Likson` (MikroTik, switches), `Access Points PPPoE Clients` (APs Ubiquiti), `Linux servers`, `Zabbix servers` |
| Etiqueta `uplink` | Nombre del equipo del que depende (p. ej. `uplink = EDGE 01`). Sirve para filtrar y como documentación de la dependencia |
| Interfaz SNMP | Comunidad `{$SNMP_COMMUNITY}` (macro global de tipo secreto). MikroTik y TP-Link: SNMPv2. **Ubiquiti: SNMPv1** |
| Dependencias | Cada equipo depende del que le da conectividad hacia Zabbix (sección 4.1) |

### Topología y dependencias actuales

```
Zabbix server (192.168.0.191)                 sin dependencia
server-04 (192.168.50.254)                    sin dependencia
EDGE 01 (192.168.200.1)  MikroTik CCR2004
├── NAS-01 (192.168.200.2)  CCR2004, concentrador PPPoE
│   └── Switch Main Site #01 (172.16.100.2)  TP-Link
│       └── APs Ubiquiti 172.16.1.2 – 172.16.1.19 (16 APs, uplink = Switch Main Site #01)
└── NAS-03 (192.168.200.10)  RB2011iL-RM, concentrador PPPoE
```

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

Todas las IPs de APs son `172.16.1.x`. Las IPs `.12` y `.13` no responden y no están dadas de alta.

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
- **Escalate unacknowledged High/Disaster:** repite los *High/Disaster* no reconocidos cada 30 min.
- *Report problems to Zabbix administrators:* **desactivada** a propósito (duplicaba los avisos).

El reparto por canal se hace en el usuario: *User settings → Profile → Media*, severidades de cada medio.

### Qué hacer con un problema

En *Monitoring → Problems* → *Update* sobre el problema:

- **Acknowledge:** indica que se está atendiendo y detiene la repetición cada 30 min. Se puede añadir un comentario, que se notifica.
- **Close problem:** solo en los triggers que lo permiten. Se usa en los que no se resuelven solos: cambio de velocidad de un puerto, o un *linkDown* por trap cuyo *linkUp* se perdió.

### Silenciar durante trabajos programados

*Data collection → Maintenance → Create maintenance period*: tipo *With data collection*, hosts o grupos afectados y horario. Durante el mantenimiento no se envían avisos, pero se siguen recogiendo datos.

---

## 3. Catálogo de plantillas

### 3.1 Plantillas propias (en `zabbix_templates/`)

#### Ubiquiti AirOS 8 wireless by SNMPv1 — `ubiquiti_airos8_wireless.yaml`
**Para:** APs Ubiquiti airMAX AC con airOS 8 (LAP-GPS, LiteAP, Rocket AC, Prism…). Se usa **junto con** la oficial *Ubiquiti AirOS by SNMP*, que aporta CPU, memoria, uptime y ping.
**Recoge:** clientes conectados, señal, ruido, CCQ, velocidades, ancho de canal, frecuencia, potencia, airMAX, GPS (fix, satélites, HDOP), tráfico de `eth0` y `ath0` y, por cada cliente, señal, distancia, CCQ, CINR, capacidad, velocidades y tiempo conectado.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| AP has no connected clients | Average | Tenía clientes en la última hora y ahora tiene 0 | Al volver a tener clientes |
| High noise floor | Warning | Ruido > `{$UBNT.NOISE.MAX.WARN}` (-80 dBm) durante 15 min | Solo |
| GPS: Weak or lost signal | Warning | < `{$UBNT.GPS.SATS.MIN}` (4) satélites durante 10 min | Solo |
| Client …: Weak signal | Warning | Señal del cliente < `{$UBNT.STA.SIGNAL.MIN.WARN}` (-75 dBm) durante 15 min | Solo |

| Macro | Defecto | Uso |
|---|---|---|
| `{$UBNT.NOISE.MAX.WARN}` | -80 | Umbral de ruido |
| `{$UBNT.STA.SIGNAL.MIN.WARN}` | -75 | Umbral de señal de cliente. Por cliente: `{$UBNT.STA.SIGNAL.MIN.WARN:"<nombre del cliente>"}` |
| `{$UBNT.GPS.SATS.MIN}` | 4 | **Poner `0` en APs sin GPS**: devuelven 0 satélites y la alerta saltaría siempre |
| `{$UBNT.IF.MATCHES}` | `^(eth0\|ath0)$` | Interfaces con tráfico |

#### Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 — `ubiquiti_airmax_m_airos6_wireless.yaml`
**Para:** equipos airMAX M con airOS 6 (Rocket M5, NanoStation M…). Es la misma plantilla que la de airOS 8, pero **sin** GPS, CINR ni capacidad de cliente, que son exclusivos de AC. Añade **airMAX quality y capacity** del AP y por cliente, que en airMAX M son las mejores medidas de calidad.
Mismos triggers y macros, salvo los de GPS. El CCQ viene en porcentaje directo. No recoge el tiempo de conexión del cliente (limitación de SNMPv1 en airOS 6).

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
| `{$PORT.IFNAME.NOT_MATCHES}` | `^<` | Puertos excluidos. En TP-Link: `^(<\|Vlan-interface)` |

Al usarla, poner `{$IFCONTROL}=0` en el host para que el *Link down* de la plantilla del fabricante no duplique los avisos de desconexión. Los cortes de menos de 30 s pueden no detectarse; los repetidos, sí (flapping).

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
3. **Si es concentrador PPPoE (NAS):** en *Macros* → *Inherited and host macros*, copiar `{$NET.IF.IFNAME.NOT_MATCHES}` y añadir `|^<pppoe-` **antes del paréntesis final**. Si no, cada sesión de cliente se descubre como interfaz y los items crecen sin control.
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
| Al caer un equipo llegan varias alertas (ping, pérdida, latencia, SNMP) en vez de una | Se usó *Replace* al configurar dependencias y se borraron las internas de la plantilla | En cada trigger (*Dependencies*): *High ICMP ping loss* y *No SNMP data collection* → *Unavailable by ICMP ping* propio; *High ICMP ping response time* → *Unavailable by ICMP ping* y *High ICMP ping loss* propios |
