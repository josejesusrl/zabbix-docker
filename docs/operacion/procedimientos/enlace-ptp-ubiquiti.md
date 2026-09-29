# Añadir un enlace PTP Ubiquiti (airOS)

> **Cuándo:** al instalar un enlace punto a punto con radios Ubiquiti airMAX.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

Para enlaces punto a punto con equipos airMAX AC (LiteBeam, PowerBeam, Rocket…). Cada enlace tiene **sus propios umbrales**, que se ponen como macros en sus hosts, no en la plantilla.

1. **En los radios:** SNMP activado ([Añadir un AP Ubiquiti](anadir-ap-ubiquiti.md)) y anotar la **capacidad mínima aceptable** en cada sentido y la señal normal.
2. **Crear primero el extremo más cercano a Zabbix**, y después el lejano ([Añadir un AP Ubiquiti](anadir-ap-ubiquiti.md)):
   - Grupo `Enlaces PTP Backhaul` (o `Troncales`), **SNMPv1**, plantillas `Ubiquiti AirOS by SNMP` + `Ubiquiti AirOS 8 wireless by SNMPv1`.
   - Si el nombre lleva caracteres no válidos (`[AP]`), *Host name* sin ellos y *Visible name* exacto.
3. **Macros de cada host:**
   - `{$UBNT.GPS.SATS.MIN}` = `0` si no tiene GPS.
   - `{$UBNT.STA.SIGNAL.MIN.WARN}` ≈ señal normal − 7 dB.
   - Capacidad: en ambos radios SNMP reporta **TX ≈ capacidad AP→estación** y **RX ≈ estación→AP**. TX coincide en los dos extremos; RX puede variar entre lecturas y entre radios (en Caribe: 95.6 frente a 63.7 Mbps): tomar el valor menor para el umbral. Para no duplicar alertas, cada sentido se vigila en un solo host: en el **AP** `{$UBNT.STA.TXCAP.MIN}` (capacidad del AP) y en la **estación** `{$UBNT.STA.RXCAP.MIN}` (capacidad de la estación).
4. **Dependencias ([Configurar las dependencias de un host](dependencias.md)):** extremo lejano → extremo cercano → equipo que da conectividad al cercano. Si el enlace cae, avisa el lejano por ping (*High*).
5. **Verificar** en *Latest data*: *Client …: TX/RX capacity* con los valores de la interfaz de airOS, y en *Triggers* los de capacidad con el umbral correcto en el nombre.

Ejemplo `Lk_Hq_Pintores_1`: AP `{$UBNT.STA.TXCAP.MIN}=50`, estación `{$UBNT.STA.RXCAP.MIN}=30`, señal normal -50 → aviso -57.

**Enlaces sensibles a la lluvia** (ej. `Lk_Hq_Caribe_1`):
- Activar además `{$UBNT.STA.SIGNAL.MIN.CRIT}` ≈ señal normal − 13 dB (*High*), dejando el aviso ≈ normal − 7 dB (*Warning*).
- Añadir la etiqueta `escalation=off` a los dos hosts.
- Con la histéresis de la plantilla, una lluvia de ~2 h produce **un aviso al empezar y otro al terminar**, sin repeticiones ni avisos por cada oscilación.
- Capacidades de Caribe: 20 % de la capacidad medida al darlo de alta (AP 183.6 → 37 Mbps; estación 63.7 → 13 Mbps).

## Con scripts (opcional)

`snmp_probe.py`, `snmp_walk.py`, `zbx_create_snmp_host.py` (`--visible-name` para nombres con `[ ]`) y `zbx_inventory.py --dependencies`. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
