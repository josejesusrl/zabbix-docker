# Configurar las dependencias de un host

> **Cuándo:** al dar de alta cualquier equipo, o al cambiarlo de sitio en la red.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

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
6. **Equipos raíz** (sin padre en la red, p. ej. EDGE 01 o un servidor directo): su trigger de disponibilidad (*Unavailable by ICMP ping* o *Zabbix agent is not available*) depende de **Zabbix server: Interface enp2s0: Link down** y de *Zabbix server: Interface enp2s0: link not stable in the last 5m (topology root)*. Si cae la red del propio servidor Zabbix, no se reporta toda la red como caída. El segundo sigue activo 5 min después del corte: el ping necesita unos 3 min de fallos y, cuando se evalúa, el *Link down* ya se ha resuelto (falso aviso del 2026-09-29).

7. **Actualizar los mapas de red**, que se dibujan a partir de estas dependencias ([mapas](../mapas.md#actualizar-los-mapas-después-de-un-alta-una-baja-o-un-cambio-de-padre)).

Para configurar varios hosts a la vez, filtrar en *Data collection → Triggers* por grupo o etiqueta y por nombre, seleccionarlos todos y usar **Mass update**.

## Con scripts (opcional)

`zbx_set_uplink.py` (padre y etiqueta `uplink`, conservando las dependencias internas), `zbx_add_dependency.py` (dependencias de equipos raíz) y `zbx_inventory.py --dependencies` para verificar. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
