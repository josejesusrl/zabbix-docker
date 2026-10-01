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

El reparto por canal se hace en el usuario: *User settings → Profile → Media*, severidades de cada medio.

## Formato de los mensajes de Telegram

Mensajes en español con formato HTML y emoji según el tipo: 🔥 Disaster, 🔴 High, 🟠 Average, 🟡 Warning, 🔵 Information, ✅ Resuelto, 💬 Actualización.
- Incluyen el problema, el host, la severidad, los datos operativos, las fechas, el ID del evento y un enlace **Ver en Zabbix**.
- La resolución y las actualizaciones se envían como **respuesta** al mensaje original del problema, formando un hilo por incidente.
- Las líneas sin valor (p. ej. "Datos:" cuando el trigger no tiene datos operativos) se omiten.

**Origen:** el script y las plantillas se mantienen en el repositorio, en `zabbix_media/telegram/`:
- `telegram.js` es el script oficial de Zabbix con los cambios marcados `CUSTOM`.
- `message_templates.json` contiene las plantillas de problema, resolución y actualización.

**Para cambiar un mensaje:**
1. Editar `message_templates.json`. Formato con etiquetas HTML de Telegram: `<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<blockquote>`, `<a href="https://…">`. `{SEV.EMOJI}` pone el emoji.
2. Respaldo.
3. Aplicar con `agents/scripts/zbx_mediatype_update.py` (ver su README). Los valores de las macros se escapan solos.
4. Probar con `agents/scripts/zbx_test_notification.py`, que dispara un problema real y lo resuelve.

Si se edita en la interfaz (*Alerts → Media types → Telegram → Message templates*), copiar el cambio al JSON del repositorio: la próxima aplicación desde el repositorio lo sobrescribiría.

## Formato de los correos (Gmail)

Mismo contenido que Telegram, en un correo HTML: cabecera con el **color de la severidad** (colores estándar de Zabbix, clase `sev{EVENT.NSEVERITY}`), verde para las resoluciones y azul para las actualizaciones, más el botón **Ver en Zabbix**. El asunto empieza por 🚨 / ✅ / 💬, seguido de la severidad, el problema y el host.
- **Origen:** `zabbix_media/gmail/message_templates.json`. Se aplica y se prueba igual que Telegram. El email no tiene script, así que no hay `{SEV.EMOJI}` ni se omiten líneas vacías.
- Zabbix **no escapa** los valores en el cuerpo HTML de un correo: un texto como `<test>` desaparecería. Por eso los valores que pueden llevar `< > &` usan la función de macro `htmlencode()`, p. ej. `{{EVENT.NAME}.htmlencode()}`. Hay que mantenerla al añadir campos al cuerpo. El asunto es texto plano y no la necesita.

**Actualizaciones (reconocimientos y comentarios):** Zabbix solo ejecuta las operaciones de actualización para usuarios **distintos del que hizo el cambio**. Con un solo usuario, los reconocimientos y comentarios propios no generan mensaje.

Los medios (Gmail y Telegram) reintentan **10 veces cada 30 s** (*Alerts → Media types → Options*): un corte de red del servidor de hasta 5 min no pierde notificaciones.

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

*Data collection → Maintenance → Create maintenance period*: tipo *With data collection*, hosts o grupos afectados y horario. Durante el mantenimiento no se envían avisos, pero se siguen recogiendo datos.
