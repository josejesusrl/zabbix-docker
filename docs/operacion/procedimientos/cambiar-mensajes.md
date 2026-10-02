# Cambiar el texto de los mensajes (Telegram, Gmail y recordatorios)

> **Cuándo:** para añadir, quitar o cambiar información de los avisos.
> **Requisitos:** respaldo reciente ([AGENTS.md](../../../AGENTS.md), regla 1). Qué contiene hoy cada mensaje: [alertas](../alertas.md).

El texto de los mensajes vive en el repositorio y se aplica a Zabbix. Si se edita en la interfaz, hay que copiar el cambio al JSON: la siguiente aplicación desde el repositorio lo sobrescribiría.

| Mensajes | Fichero | Dónde están en la interfaz | Se aplica con |
|---|---|---|---|
| Telegram: problema, resuelto, actualización | `zabbix_media/telegram/message_templates.json` (y el script `telegram.js`) | *Alerts → Media types → Telegram → Message templates* | `zbx_mediatype_update.py --name Telegram --script telegram.js --templates message_templates.json` |
| Gmail: problema, resuelto, actualización | `zabbix_media/gmail/message_templates.json` | *Alerts → Media types → Gmail → Message templates* | `zbx_mediatype_update.py --name Gmail --templates message_templates.json` |
| Recordatorios de la escalada (los dos medios) | `zabbix_media/escalation.json` | *Alerts → Actions → Trigger actions → Escalate unacknowledged High/Disaster → Operations*: una operación por medio (*Send only to*), pasos 2 → 0, *Custom message* | `zbx_action_operations.py escalation.json` |

## Reglas de cada medio

**Telegram:**
- `telegram.js` es el script oficial de Zabbix con los cambios marcados `CUSTOM`.
- El script envía el **asunto como primera línea** y después el cuerpo: la cabecera va solo en el asunto.
- Formato con etiquetas HTML de Telegram: `<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<blockquote>`, `<a href="https://…">`. `{SEV.EMOJI}` pone el emoji de la severidad.
- Los valores de las macros se escapan solos.
- Las líneas `<b>Etiqueta:</b>` sin valor, con `*UNKNOWN*` o con una macro sin resolver se omiten.
- El mensaje se recorta si supera el límite de Telegram (4096 caracteres).
- Conviene que sea corto: el detalle va en el correo.

**Gmail:**
- Correo HTML.
- No hay script: no hay `{SEV.EMOJI}` ni se omiten líneas vacías.
- Zabbix **no escapa** los valores en el cuerpo HTML: un texto como `<test>` desaparecería. Los valores que pueden llevar `< > &` usan la función de macro `htmlencode()`, p. ej. `{{EVENT.NAME}.htmlencode()}`. Mantenerla al añadir campos.
- El asunto es texto plano y no la necesita.

**Macros útiles:** `{HOST.IP}`, `{EVENT.TAGS.uplink}` (valor de una etiqueta), `{TRIGGER.DESCRIPTION}`, `{ITEM.NAME1}`/`{ITEM.LASTVALUE1}`, `{TRIGGER.EVENTS.PROBLEM.UNACK}`, `{TRIGGER.HOSTGROUP.NAME}`, `{EVENT.UPDATE.HISTORY}` y `{ESC.HISTORY}` (historial de la escalada).

## Pasos

1. Editar el fichero de la tabla.
2. Respaldo.
3. Aplicar (sección *Con scripts*) o copiar el texto a la interfaz.
4. **Verificar** con una prueba real: `zbx_test_notification.py` crea un host temporal, abre un problema High, lo reconoce, lo resuelve, muestra si cada mensaje se envió y borra el host. El reconocimiento no genera mensaje cuando lo hace el mismo usuario que recibe los avisos. Los recordatorios solo se pueden probar con un problema High sin reconocer durante 30 min.

## Con scripts

```sh
S=agents/scripts/run_remote.sh
printf '%s\n' "$TOKEN" | $S -f zabbix_media/telegram/telegram.js -f zabbix_media/telegram/message_templates.json \
    zbx_mediatype_update.py --name Telegram --script telegram.js --templates message_templates.json --dry-run
printf '%s\n' "$TOKEN" | $S -f zabbix_media/gmail/message_templates.json zbx_mediatype_update.py --name Gmail --templates message_templates.json
printf '%s\n' "$TOKEN" | $S -f zabbix_media/escalation.json zbx_action_operations.py escalation.json
printf '%s\n' "$TOKEN" | $S zbx_test_notification.py
```
