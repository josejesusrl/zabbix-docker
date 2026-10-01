# Monitorear el gateway de un proveedor de internet

> **Cuándo:** para detectar y documentar las caídas de un proveedor (Coefi01, Telmex…) y tener evidencia con hora exacta de si el fallo es suyo o nuestro.
> **Requisitos:**
> - Respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.
> - IP del gateway del proveedor (la puerta de enlace de la interfaz WAN en EDGE 01).

Zabbix hace ping al gateway cada minuto. Ese dato se cruza con el estado físico del puerto WAN de EDGE 01, que ya está monitoreado (*Interface ether1(Coefi01): Link down*).

| Puerto WAN de EDGE 01 | Gateway del proveedor | Interpretación |
|---|---|---|
| Arriba | No responde | **Falla del proveedor:** nuestro enlace físico está bien y su equipo no contesta |
| Caído | No responde | Corte físico: cable, ONT o radio del proveedor, o nuestro puerto. Revisar en sitio |
| Arriba | Pérdida o latencia alta | Degradación en la red del proveedor |

## 1. En EDGE 01 (RouterOS): forzar que el ping salga por ese proveedor

El gateway está en la misma red que la IP WAN de EDGE 01, así que se alcanza por la ruta directa de esa interfaz. Si el puerto cae, esa ruta desaparece. El ping podría salir entonces por el otro proveedor y llegar al gateway por Internet, de modo que la caída no se vería.

En Winbox: *IP → Routes → +*:
- *Dst. Address:* `<IP del gateway>/32` (Coefi01: `170.80.29.30/32`)
- *Type:* `blackhole`
- *Distance:* `254`
- *Comment:* `Zabbix: ping al gateway <proveedor> solo por su interfaz`

Con el enlace activo, la ruta directa tiene prioridad y esta no se usa. Sin enlace, el ping se descarta y Zabbix detecta la caída.

## 2. En Zabbix

*Data collection → Hosts → Create host*:

1. **Host name:** `ISP-<PROVEEDOR>-GW` (p. ej. `ISP-COEFI01-GW`).
2. **Templates:** `ICMP Ping`. Comprueba cada minuto y avisa con:
   - *Unavailable by ICMP ping* (**High**: Telegram y Gmail).
   - *High ICMP ping loss* y *High ICMP ping response time* (Warning: Gmail).
3. **Host groups:** `Proveedores de internet`.
4. **Interfaces → Add → Agent:** IP del gateway, puerto `10050`. No hay agente; la interfaz solo da al ping la IP.
5. **Tags:** `proveedor` = nombre del proveedor y `uplink` = `EDGE 01`.
6. **Add**. Después, **dependencias** de los tres triggers de ping hacia *EDGE 01: Unavailable by ICMP ping* ([dependencias](dependencias.md)). Así, si cae nuestro router, no se culpa al proveedor.
7. Regenerar el [inventario](../inventario.md) y los [mapas](../mapas.md).

## 3. Evidencia para el proveedor

- **Cada caída:** *Monitoring → Problems* → filtro *Hosts* = el gateway, *Show* = *History*, con el periodo. Muestra inicio, fin y duración. Añadir en el filtro el host EDGE 01 para ver si coincidió con un *Link down* del puerto WAN.
- **Disponibilidad del periodo:** *Reports → Availability report* → *Mode: By trigger template* (o *By host*) → host del gateway, trigger *Unavailable by ICMP ping* → periodo. Da el % de tiempo *Problem* y *OK*.
- **Gráficos:** *Latest data* → `ICMP loss` y `ICMP response time` → *Graph*. Se pueden exportar como imagen.

## Verificar

- *Latest data*: `ICMP ping` = 1 y `ICMP response time` con valor en milisegundos.
- En RouterOS, `/ip route print where dst-address=<IP>/32` muestra la ruta *blackhole* inactiva mientras la interfaz está arriba.
- En el mapa general, el gateway aparece bajo EDGE 01 con icono de nube.

## Con scripts

```sh
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh zbx_create_snmp_host.py --name ISP-COEFI01-GW --ip 170.80.29.30 \
    --group "Proveedores de internet" --interface ping --template "ICMP Ping" --tag proveedor=Coefi01 --uplink "EDGE 01" --dry-run
```
