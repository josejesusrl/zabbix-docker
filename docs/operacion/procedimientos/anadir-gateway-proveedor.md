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
2. **Templates:** `ICMP Ping` e `ISP gateway fast ping` ([catálogo](../plantillas/isp-gateway-fast-ping.md)).
   - *ICMP Ping* comprueba cada minuto: *Unavailable by ICMP ping* (High), *High ICMP ping loss* y *High ICMP ping response time* (Warning). Solo detecta caídas de varios minutos.
   - *ISP gateway fast ping* comprueba cada 10 s: **Corte del proveedor** (High, Telegram y Gmail) con unos 20 s sin respuesta, y *Pérdida intermitente* (Warning).
3. **Host groups:** `Proveedores de internet`.
4. **Interfaces → Add → Agent:** IP del gateway, puerto `10050`. No hay agente; la interfaz solo da al ping la IP.
5. **Tags:** `proveedor` = nombre del proveedor y `uplink` = `EDGE 01`.
6. **Add**. Después, **dependencias** ([dependencias](dependencias.md)):
   - Los triggers de *ICMP Ping*, *Corte del proveedor* y *Pérdida intermitente* dependen de *EDGE 01: Unavailable by ICMP ping*. Así, si cae nuestro router, no se culpa al proveedor.
   - *Unavailable by ICMP ping* del gateway depende también de su propio *Corte del proveedor*, para recibir un solo aviso en un corte largo.
7. Regenerar el [inventario](../inventario.md) y los [mapas](../mapas.md).

## 3. Salida a Internet por ese proveedor

El gateway puede responder aunque el proveedor no dé salida a Internet. Para detectarlo:

1. **En EDGE 01:** dos direcciones de Internet enrutadas **solo** por ese proveedor (Coefi01: `208.67.222.222` y `8.8.4.4`). No usar direcciones que los clientes necesiten con conmutación al otro proveedor: esta ruta afecta a todo el tráfico hacia ellas.
2. **En Zabbix**, *Create host*:
   - **Host name:** `ISP-<PROVEEDOR>-INTERNET`.
   - **Template:** `ISP internet fast ping`.
   - **Group:** `Proveedores de internet`.
   - **Interfaz *Agent*** con la primera dirección (solo la requieren los chequeos simples).
   - **Macros** `{$ISP.INET.TARGET1}` y `{$ISP.INET.TARGET2}` con las dos direcciones.
   - **Etiquetas:** `proveedor` y `uplink` = el host del gateway.
3. **Dependencias:** *Sin salida a Internet* y *Pérdida intermitente hacia Internet* dependen de *Corte del proveedor* del gateway. *Sin salida a Internet* depende también de *EDGE 01: Unavailable by ICMP ping*.

| Gateway | Internet por el proveedor | Interpretación |
|---|---|---|
| *Corte del proveedor* | (no avisa, depende del gateway) | Falla el primer salto: enlace o equipo del proveedor |
| Responde | *Sin salida a Internet* | El proveedor no da salida más allá de su gateway |
| Responde | Responde | Sin problema del proveedor (salvo degradación, sección 4) |

## 4. Degradación: bajada por debajo de un mínimo

Un enlace inalámbrico del proveedor puede seguir conectado pero sin capacidad. Sin acceso SNMP a su radio, se detecta por el **tráfico de bajada** del puerto WAN en EDGE 01. La subida no sirve: de madrugada baja de forma normal a unos 8 Mbps.

Antes de elegir el umbral, revisar en *Latest data* → *Interface etherX: Bits received* → *Graph* (7 días) el mínimo normal de madrugada. Con Coefi01 el mínimo normal es de unos 62 Mbps; solo bajó de 20 Mbps en cortes reales.

En EDGE 01:
1. **Macros de host:** `{$ISP.<PROVEEDOR>.MIN.DOWN}` = umbral (Coefi01: `20M`) y `{$ISP.<PROVEEDOR>.RECOVERY.DOWN}` = valor para resolverse (Coefi01: `50M`).
2. *Triggers → Create trigger* (Coefi01, `ether1` = índice SNMP 2):
   - *Name:* `Coefi01: bajada degradada (menos de {$ISP.COEFI01.MIN.DOWN} durante 5 min)`.
   - *Severity:* **Average** (Gmail).
   - *Expression:* `max(/EDGE 01/net.if.in[ifHCInOctets.2],5m)<{$ISP.COEFI01.MIN.DOWN} and last(/EDGE 01/net.if.status[ifOperStatus.2])=1`. Todas las muestras de 5 min bajo el umbral y el puerto arriba (si el puerto cae, ya avisa *Link down*).
   - *OK event generation:* **Recovery expression**: `avg(/EDGE 01/net.if.in[ifHCInOctets.2],5m)>{$ISP.COEFI01.RECOVERY.DOWN}`. Se resuelve cuando la media de 5 min supera 50 Mbps; el margen evita que se abra y cierre alrededor del umbral.
   - *Operational data:* `Bajada: {ITEM.LASTVALUE1}`.
   - *Tags:* `proveedor` = `Coefi01`, `scope` = `performance` y `aviso_proveedor` = `Enlace conectado, pero con capacidad de bajada inferior a 20 Mbps durante 5 minutos` (texto para el [aviso al proveedor](avisar-proveedor.md)).
3. **Dependencias:** *ISP-COEFI01-GW: Corte del proveedor* y *ISP-COEFI01-INTERNET: Sin salida a Internet por el proveedor*. En un corte total solo llega el aviso de corte.

**Límite:** mide el tráfico que pasa, no la capacidad. Una demanda real por debajo del umbral durante 5 min también avisaría; con los datos de Coefi01 no ha ocurrido.

## 5. Evidencia para el proveedor

- **Cada caída, incluidos los cortes breves:** *Monitoring → Problems* → filtro *Hosts* = el gateway, *Show* = *History*, con el periodo. Muestra inicio, fin y duración. Añadir en el filtro el host EDGE 01 para ver si coincidió con un *Link down* del puerto WAN.
- **Degradación:** lo mismo con el host EDGE 01 y su trigger *Coefi01: bajada degradada*.
- **Salida a Internet:** lo mismo con el host `ISP-<PROVEEDOR>-INTERNET` y su trigger *Sin salida a Internet por el proveedor*.
- **Disponibilidad del periodo:** *Reports → Availability report* → *Mode: By trigger template* (o *By host*) → host del gateway, trigger **Corte del proveedor** (incluye los cortes breves; *Unavailable by ICMP ping* solo cuenta los de varios minutos) → periodo. Da el % de tiempo *Problem* y *OK*.
- **Gráficos:** *Latest data* → `ICMP loss` y `ICMP response time` → *Graph*. Se pueden exportar como imagen.

## Verificar

- *Latest data*: `ICMP ping` = 1, `ICMP response time` con valor en milisegundos y `Ping rápido al gateway` = 1 (Up) con datos cada 10 s.
- En RouterOS, `/ip route print where dst-address=<IP>/32` muestra la ruta *blackhole* inactiva mientras la interfaz está arriba.
- En el mapa general, el gateway aparece bajo EDGE 01 con icono de nube.

## Con scripts

```sh
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh zbx_create_snmp_host.py --name ISP-COEFI01-INTERNET --ip 208.67.222.222 \
    --group "Proveedores de internet" --interface ping --template "ISP internet fast ping" \
    --macro '{$ISP.INET.TARGET1}=208.67.222.222' '{$ISP.INET.TARGET2}=8.8.4.4' --tag proveedor=Coefi01 uplink=ISP-COEFI01-GW --dry-run
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh zbx_create_snmp_host.py --name ISP-COEFI01-GW --ip 170.80.29.30 \
    --group "Proveedores de internet" --interface ping --template "ICMP Ping" "ISP gateway fast ping" --tag proveedor=Coefi01 --uplink "EDGE 01" --dry-run
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh zbx_add_dependency.py --host ISP-COEFI01-GW --trigger "Corte del proveedor" --parent-host "EDGE 01" --parent-trigger "Unavailable by ICMP ping"
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh zbx_add_dependency.py --host ISP-COEFI01-GW --trigger "Unavailable by ICMP ping" --parent-host ISP-COEFI01-GW --parent-trigger "Corte del proveedor"
```
