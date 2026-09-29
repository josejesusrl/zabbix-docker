# Añadir un enlace PTP Mimosa

> **Cuándo:** al instalar un enlace punto a punto con radios Mimosa.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

**En los radios** (los dos extremos): activar SNMP v2c con la comunidad de lectura, en la sección de gestión SNMP del radio (firmware 2.x: *Preferences → Management*). Anotar la **señal de diseño** (RSL) del enlace.

**En Zabbix** (respaldo antes):
1. Crear **primero el extremo más cercano a Zabbix**: los dependientes necesitan que su padre exista.
2. *Create host* para cada extremo:
   - Nombre = *Device Name* del radio. Grupo `Enlaces PTP Troncales`.
   - Interfaz **SNMP** (IP, 161, **SNMPv2**, `{$SNMP_COMMUNITY}`).
   - **Templates:** `Network Generic Device by SNMP` + `Mimosa C5C by SNMP` + `Switch port changes by SNMP`.
   - **Macros:** `{$IFCONTROL}` = `0`, `{$MIMOSA.RX.POWER.MIN.WARN}` = diseño − 6 y `{$MIMOSA.RX.POWER.MIN.CRIT}` = diseño − 11.
3. **Dependencias ([Configurar las dependencias de un host](dependencias.md)):** el extremo lejano depende del cercano (si no hay conexión con el cercano, tampoco con el lejano), y el cercano depende del equipo que le da conectividad hacia Zabbix.
4. **Verificar:** SNMP en verde, *Link: Status = connected*, potencias y SNR con valores reales en *Latest data*, y en *Switch port changes* solo el puerto Ethernet (`eth1_emac1`), no `wifi0`.

## Con scripts (opcional)

`snmp_walk.py` (ver qué publica el radio), `zbx_create_snmp_host.py`, `zbx_latest.py --key mimosa.`. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
