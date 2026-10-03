# ISP internet fast ping

> **Fichero:** `zabbix_templates/isp_internet_fast_ping.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** comprobar la **salida a Internet** de un proveedor, más allá de su gateway. Hace ping cada **5 s** a dos direcciones de Internet que EDGE 01 enruta **solo** por ese proveedor: `{$ISP.INET.TARGET1}` y `{$ISP.INET.TARGET2}`, macros de host (Coefi01: `208.67.222.222` y `8.8.4.4`, las mismas que Uptime Kuma).

| Trigger | Severidad | Para | Cuándo |
|---|---|---|---|
| Sin salida a Internet por el proveedor | High | **Likson** | Pérdida media de más de `{$ISP.CUT.LOSS}` (33 %) en 1 minuto hacia **las dos** direcciones. Si solo falla una, el problema suele ser de ese destino y no avisa. Depende de *Corte del proveedor* del gateway y de EDGE 01 |
| Pérdida intermitente hacia Internet por el proveedor | Information (no notifica) | Registro | Pérdida en las dos direcciones en `{$ISP.LOSS.CHECKS}` (3) comprobaciones en 5 min |
| Aviso al proveedor: sin salida a Internet más de 5 min | Information | **Proveedor** | Ninguna de las dos direcciones respondió durante 5 minutos seguidos. Depende de *Aviso al proveedor: gateway sin respuesta más de 5 min*: en un corte total solo se envía el del gateway |
| Aviso al proveedor: pérdida alta hacia Internet durante 5 min | Information | **Proveedor** | Pérdida media de `{$ISP.PROVIDER.LOSS}` (50 %) o más en las dos direcciones durante 5 min. Depende de los avisos de proveedor del gateway |

Lectura junto con el gateway: si *Corte del proveedor* está activo, falla el primer salto; si solo está *Sin salida a Internet*, el gateway responde pero la red del proveedor no da salida. **Límite:** con el puerto WAN del proveedor desconectado, EDGE 01 alcanza esas direcciones por el otro proveedor y este aviso no salta; en ese caso avisan *Corte del proveedor* y el *Link down* del puerto. El host no tiene *ICMP Ping*: su interfaz solo existe porque los chequeos simples la requieren.

Los dos *Aviso al proveedor* llevan la etiqueta `aviso_proveedor` ([avisar al proveedor](../procedimientos/avisar-proveedor.md)).
