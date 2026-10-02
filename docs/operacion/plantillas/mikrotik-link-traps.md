# MikroTik link traps by SNMP

> **Fichero:** `zabbix_templates/mikrotik_link_traps.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** routers MikroTik, junto con su plantilla oficial de modelo. Alerta **al instante** cuando cae un enlace, a partir del trap `linkDown`.
**Requisitos en el router:** traps configurados y `src-address` igual a la IP del host en Zabbix ([Añadir un router MikroTik](../procedimientos/anadir-router-mikrotik.md)).

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Interface X(comentario): Link down (SNMP trap) | Average | Llega un `linkDown` con la interfaz habilitada. Si se deshabilita a mano, no alerta | Con el trap `linkUp`, o manualmente |

| Macro | Defecto | Uso |
|---|---|---|
| `{$LINKTRAP.IFALIAS.MATCHES}` | `.+` | Solo interfaces **con comentario** en RouterOS. Para quitar una interfaz, borrar su comentario o ajustar la regex (p. ej. `^(?!.*RESERVED)`) |
| `{$LINKTRAP.IFNAME.NOT_MATCHES}` | `^<` | Excluye interfaces dinámicas (PPPoE, túneles) |

Complementa, no sustituye, el *Link down* por consulta de la plantilla oficial (cada pocos minutos). Si el trap se pierde, la consulta lo detecta. Una misma caída puede generar los dos avisos.
