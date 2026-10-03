# ISP internet fast ping

> **Fichero:** `zabbix_templates/isp_internet_fast_ping.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** comprobar la **salida a Internet** de un proveedor, más allá de su gateway. Hace ping cada **5 s** a dos direcciones de Internet que EDGE 01 enruta **solo** por ese proveedor: `{$ISP.INET.TARGET1}` y `{$ISP.INET.TARGET2}`, macros de host (Coefi01: `208.67.222.222` y `8.8.4.4`, las mismas que Uptime Kuma).

| Trigger | Severidad | Cuándo |
|---|---|---|
| Sin salida a Internet por el proveedor | High | **Las dos** direcciones sin respuesta en la misma comprobación. Si solo falla una, el problema suele ser de ese destino y no avisa. Se resuelve cuando una responde 3 veces. Depende de *Corte del proveedor* del gateway y de EDGE 01 |
| Pérdida intermitente hacia Internet por el proveedor | Warning | Pérdida en las dos direcciones en `{$ISP.LOSS.CHECKS}` (3) comprobaciones en 5 min |

Lectura junto con el gateway: si *Corte del proveedor* está activo, falla el primer salto; si solo está *Sin salida a Internet*, el gateway responde pero la red del proveedor no da salida. **Límite:** con el puerto WAN del proveedor desconectado, EDGE 01 alcanza esas direcciones por el otro proveedor y este aviso no salta; en ese caso avisan *Corte del proveedor* y el *Link down* del puerto. El host no tiene *ICMP Ping*: su interfaz solo existe porque los chequeos simples la requieren.

Los dos triggers llevan la etiqueta `aviso_proveedor` con el texto que recibe el proveedor ([avisar al proveedor](../procedimientos/avisar-proveedor.md)).
