# Alertas y notificaciones

## A quién y cómo llegan

| Severidad | Gmail | Telegram | Repetición |
|---|---|---|---|
| Information / Not classified | — | — | — |
| Warning / Average | ✅ | — | Un aviso |
| High / Disaster | ✅ | ✅ | Cada 30 min hasta que se reconozca o se resuelva |

Acciones (*Alerts → Actions → Trigger actions*; su configuración exacta, en [configuración base](../despliegue/configuracion-base.md)):

- **Alert by severity:** severidad ≥ Warning. Primer aviso, aviso de "Resuelto" y avisos de reconocimientos y comentarios.
- **Escalate unacknowledged High/Disaster:** repite los *High/Disaster* no reconocidos cada 30 min, **excepto** los problemas con la etiqueta `escalation` (condición *Tag name does not equal escalation*).
- *Report problems to Zabbix administrators:* **desactivada** a propósito (duplicaba los avisos).
- **Aviso a proveedor Coefi01:** envía al soporte del proveedor cada incidencia de su servicio: a los 5 min si sigue activa y, siempre, al normalizarse (también cortes de segundos), con un mensaje sin datos internos ([avisar al proveedor](procedimientos/avisar-proveedor.md)).

El reparto por canal se hace en el usuario: *User settings → Profile → Media*, severidades de cada medio.

## Formato de los mensajes de Telegram

Mensajes en español con formato HTML y emoji según el tipo: 🔥 Disaster, 🔴 High, 🟠 Average, 🟡 Warning, 🔵 Information, ✅ Resuelto, 💬 Actualización, 🔔 Recordatorio.

Telegram lleva **solo lo necesario para actuar desde el móvil**; el detalle va en el correo.

| Mensaje | Contenido |
|---|---|
| Problema | Problema · host e IP · severidad · datos operativos · **de quién depende** (etiqueta `uplink`) · **veces abierto sin reconocer** (detecta *flapping*) · inicio · enlaces **Ver problema** y **Datos del host** |
| Resuelto | Problema · host e IP · severidad · **datos al resolverse** · duración · hora · enlace |
| Actualización | Usuario · acción · comentario · host e IP · estado · enlace |
| Recordatorio (escalada) | Problema · host e IP · severidad · **sin reconocer desde hace** · datos · enlace **Reconocer en Zabbix** |

- La resolución y las actualizaciones se envían como **respuesta** al mensaje original del problema, formando un hilo por incidente.
- Las líneas sin valor se omiten: "Datos:" cuando el trigger no tiene datos operativos, o "Depende de:" en equipos raíz sin etiqueta `uplink`. También se omiten las que quedan en `*UNKNOWN*` o con una macro sin resolver.
- Si un mensaje superara el límite de Telegram (4096 caracteres), se recorta con "…".

## Formato de los correos (Gmail)

Correo HTML **completo**, para analizar el incidente. Cabecera con el **color de la severidad** (colores estándar de Zabbix, clase `sev{EVENT.NSEVERITY}`), verde para las resoluciones y azul para las actualizaciones. El asunto empieza por 🚨 / ✅ / 💬 / 🔔, seguido de la severidad, el problema y el host.

| Mensaje | Además de lo de Telegram |
|---|---|
| Problema | **Grupos** del host · **valor exacto** del item que disparó el problema · edad · todas las **etiquetas** · cuadro **"Qué significa / qué revisar"** con la descripción del trigger (las plantillas explican la causa probable) · botones *Ver problema*, *Datos del host* y *Problemas del host* |
| Resuelto | Grupos · valor final · inicio y fin |
| Actualización | **Historial** de reconocimientos y comentarios del problema |
| Recordatorio (escalada) | Aviso "sigue abierto hace … y nadie lo ha reconocido" · **historial de la escalada** (a quién se avisó y cuándo) · botón *Reconocer en Zabbix* |

Si el trigger no tiene descripción o el host no tiene etiquetas, esos campos salen vacíos: el correo no puede ocultar filas.

**Cambiar el texto de los mensajes** (Telegram, Gmail o recordatorios): [procedimiento](procedimientos/cambiar-mensajes.md).

## Recordatorios de la escalada

Los reenvíos cada 30 min de *Escalate unacknowledged High/Disaster* usan un **mensaje propio** para cada medio ("🔔 Recordatorio"), distinto del primer aviso: dice cuánto lleva sin reconocer y, en el correo, a quién se avisó y cuándo.

## Entrega

- **Actualizaciones (reconocimientos y comentarios):** Zabbix solo ejecuta las operaciones de actualización para usuarios **distintos del que hizo el cambio**. Con un solo usuario, los reconocimientos y comentarios propios no generan mensaje.
- Los medios (Gmail y Telegram) reintentan **10 veces cada 30 s** (*Alerts → Media types → Options*): un corte de red del servidor de hasta 5 min no pierde notificaciones.

## Avisar una sola vez: etiqueta `escalation=off`

En equipos cuyos problemas duran horas por causas conocidas (p. ej. un enlace que se degrada con la lluvia), añadir al host la etiqueta **`escalation` = `off`** (*Host → Tags*). Sus problemas *High* avisan al empezar y al resolverse, pero no se repiten cada 30 min. Las etiquetas del host se heredan en todos sus problemas.

## Solo dashboard: etiqueta `notificar=no`

En equipos inestables cuyos avisos no son accionables (p. ej. una cámara tras un enlace débil), y mientras se termina el alta de un equipo, añadir al host la etiqueta **`notificar` = `no`** (*Host → Tags*). Sus problemas se siguen viendo en el dashboard y en *Monitoring → Problems*, pero **no envían Telegram ni Gmail**. Las dos acciones tienen la condición *Tag value* `notificar` *does not equal* `no` ([configuración base](../despliegue/configuracion-base.md#acciones-de-trigger-alerts--actions--trigger-actions)).

- La etiqueta solo afecta a los problemas que se abren **después** de ponerla: un problema ya abierto conserva sus etiquetas y notificará su resolución.
- Cada equipo con `notificar=no` permanente se registra en el [registro](registro.md) con el motivo.

## Qué hacer con un problema

En *Monitoring → Problems* → *Update* sobre el problema:

- **Acknowledge:** indica que se está atendiendo y detiene la repetición cada 30 min. Se puede añadir un comentario, que se notifica.
- **Close problem:** solo en los triggers que lo permiten. Se usa en los que no se resuelven solos: cambio de velocidad de un puerto, o un *linkDown* por trap cuyo *linkUp* se perdió.

## Silenciar durante trabajos programados

Un mantenimiento programado suprime los avisos de los equipos incluidos mientras se sigue recogiendo datos: [programar un mantenimiento](procedimientos/mantenimiento-programado.md).
