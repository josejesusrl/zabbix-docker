# Añadir un AP Ubiquiti

> **Cuándo:** al instalar un AP Ubiquiti nuevo (airOS 8 o airOS 6).
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

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
2. **Add**. Configurar las dependencias ([Configurar las dependencias de un host](dependencias.md)), incluida la de "AP has no connected clients".
3. **Verificar** (unos 5 min):
   - En *Data collection → Hosts*, el icono **SNMP** en verde.
   - En *Monitoring → Latest data*, filtrado por el host: *Connected clients* igual al número de clientes que muestra airOS, y un grupo de items *Client …* por cada uno.
   - *Firmware version* y *Hardware model name* no soportados es normal en airOS 8: **desactivarlos** en el host (*Items* → marcar → *Disable*, o `zbx_set_status.py --item "Firmware version" "Hardware model name" --disable`). Si no, su trigger *Firmware has changed* queda en error ([registro](../registro.md)). Cualquier otro item no soportado se revisa en [solución de problemas](../solucion-de-problemas.md).

**Por qué SNMPv1:** airOS ignora las consultas SNMPv2c aunque la comunidad sea correcta, y el host aparece como no disponible.

## Con scripts (opcional)

`snmp_probe.py` (sondeo previo: versión SNMP, nombre, GPS, modelo), `zbx_create_snmp_host.py` y `zbx_host_status.py` / `zbx_latest.py` para verificar. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
