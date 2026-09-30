# Mapas de red

> **Cuándo:** para ver la topología con el estado en vivo, y para actualizar los mapas después de dar de alta, retirar o mover un equipo.
> **Requisitos para actualizarlos:** respaldo reciente ([AGENTS.md](../../AGENTS.md), regla 1). Los mapas se ven en *Monitoring → Maps*.

## Qué mapas hay

| Mapa | Contenido |
|---|---|
| **Likson - Red general** | Zabbix server, EDGE 01, el troncal Mimosa, server-04 y un elemento por cada sitio. El icono de cada sitio toma el color del peor problema de sus equipos; al hacer clic se abre su submapa |
| **Likson - Sitio NAS-01** | NAS-01, MAIN-SW-01, sus APs, los sectores y los enlaces de backhaul (Mayólica, Caribe, Pintores → Cañadas) |
| **Likson - Sitio NAS-03 Cañadas** | NAS-03 y los APs LIKSON_CANADAS |

Cómo leerlos:
- **Icono:** tipo de equipo (router, switch, AP o radio PTP). Se resalta con el color del problema más grave del equipo.
- **Etiqueta:** nombre y IP.
- **Línea** entre un equipo y su padre: gris en condiciones normales, **roja y gruesa** mientras el equipo de abajo no responde al ping (*Unavailable by ICMP ping*). Así se ve en qué punto se corta la red.
- En los submapas, el icono de arriba a la izquierda (*Volver a Likson - Red general*) abre el mapa general.

Están compartidos en solo lectura con el grupo *Solo lectura* ([dar acceso de solo lectura](procedimientos/dar-acceso-lectura.md)).

## Cómo se generan

Los mapas **no se dibujan a mano**: se generan desde la topología de Zabbix, es decir, las dependencias que se configuran en cada alta ([dependencias](procedimientos/dependencias.md)). La definición está en `zabbix_maps/likson_red.json`:
- nombres de los mapas y qué equipo es la raíz de cada sitio (`submaps`);
- iconos por grupo de hosts o plantilla;
- hosts excluidos (*KPI Likson*, que no es un equipo);
- grupos con los que se comparten.

La colocación es automática en árbol, de arriba abajo. Cuando un equipo tiene muchos hijos sin descendientes, como los APs de MAIN-SW-01, se colocan en filas de 8.

server-04 aparece suelto en el mapa general. Su dependencia está en el trigger del agente, que el generador no usa, por eso no tiene línea hacia el Zabbix server (el inventario también lo muestra sin padre).

## Actualizar los mapas (después de un alta, una baja o un cambio de padre)

Primero se hacen el alta y sus dependencias. Después, **una persona con acceso al repositorio** ejecuta:

```sh
S=agents/scripts/run_remote.sh
printf '%s\n' "$TOKEN" | $S -f zabbix_maps/likson_red.json zbx_map_apply.py likson_red.json --dry-run   # revisa la lista padre -> hijo
printf '%s\n' "$TOKEN" | $S -f zabbix_maps/likson_red.json zbx_map_apply.py likson_red.json
```

- Las posiciones se recalculan en cada ejecución. **Los cambios hechos a mano en el editor de mapas se pierden**; si algo se quiere distinto, se cambia en el JSON o en el script.
- Los mapas se identifican por nombre y conservan su id, así que los enlaces y widgets que los usan siguen funcionando.
- Si el `--dry-run` muestra un equipo bajo un padre equivocado, lo que está mal es su dependencia: corregirla ([dependencias](procedimientos/dependencias.md)) y volver a ejecutar.

### Un sitio nuevo (otro NAS o sitio con varios equipos)

Añadir una línea en `submaps` de `zabbix_maps/likson_red.json`, con el equipo raíz y el nombre del mapa (`Likson - Sitio <nombre>`). Hacer commit y ejecutar el script: crea el submapa y lo enlaza desde el general.

### Sin scripts (a mano en la interfaz)

Si no se puede usar el script, se puede editar el mapa en *Monitoring → Maps* → mapa → **Edit map**. El cambio se perderá la próxima vez que se ejecute el script.
1. **Add element** → *Type: Host* → elegir el host. *Label:* `{HOST.NAME}` y `{HOST.CONN}` en dos líneas. *Icon (default):* el del mismo tipo de equipo que los demás.
2. Seleccionar el padre y el equipo nuevo (Ctrl + clic) → **Add link**. En el enlace: *Color* `999999`. En *Link indicators*, *Type: Trigger* → *Add* → trigger *Unavailable by ICMP ping* del equipo nuevo, *Type: Bold line*, *Color* `DD0000`.
3. **Update** (arriba a la derecha).

Para crear un mapa nuevo: *Monitoring → Maps → Create map*, con los mismos criterios. En la pestaña *Sharing*, añadir el grupo *Solo lectura* con *Read-only*.

## Verificar

- *Monitoring → Maps* muestra los 3 mapas. Cada equipo del [inventario](inventario.md), salvo *KPI Likson*, aparece en uno de ellos.
- Un equipo caído muestra su icono en rojo y su línea hacia el padre roja y gruesa.
- Con un usuario *Solo lectura*, los mapas se ven pero no aparece *Edit map*.
