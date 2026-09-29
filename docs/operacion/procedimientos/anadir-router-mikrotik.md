# Añadir un router MikroTik

> **Cuándo:** al instalar un router MikroTik, incluidos los concentradores PPPoE (NAS).
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

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
4. Dependencias ([Configurar las dependencias de un host](dependencias.md)) y etiqueta `uplink`.
5. **Verificar:** SNMP en verde. En *Latest data*, interfaces sin `<pppoe-…>` (en un NAS, el filtro tarda hasta 1 h en aplicarse). Prueba de traps: deshabilitar y habilitar una interfaz **sin uso** con comentario:
   ```routeros
   /interface disable etherX; :delay 5s; /interface enable etherX
   ```
   Aparecerá en *Latest data* → *SNMP traps* del host, o en el trigger *Link down (SNMP trap)*.

## Con scripts (opcional)

`snmp_probe.py`, `zbx_create_snmp_host.py`, `zbx_set_status.py` (desactivar la lectura wifi) y `zbx_host_status.py`. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
