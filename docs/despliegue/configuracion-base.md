# Configuración base (solo en la base de datos)

> **Cuándo:** para saber cómo está configurado Zabbix fuera de los hosts y plantillas, o para rehacerlo si se pierde la base de datos sin respaldo.
> Esta configuración vive **solo en la BD**: el respaldo diario la conserva, pero no está en git. Si se cambia en la interfaz, actualizar este documento en el mismo commit ([AGENTS.md](../../AGENTS.md)).
> Los secretos (token del bot, contraseña de aplicación de Gmail, comunidad SNMP) **no** se escriben aquí: los introduce la persona en la interfaz.

## Medios (*Alerts → Media types*)

### Telegram (webhook)

| Campo | Valor |
|---|---|
| Script | `zabbix_media/telegram/telegram.js` (oficial con cambios marcados `CUSTOM`: formato HTML, emoji por severidad) |
| Parámetros | `api_parse_mode` = `html`, `api_chat_id` = `{ALERT.SENDTO}`, `api_token` = token del bot (secreto) y el resto de los parámetros oficiales sin cambios |
| Process tags | Sí |
| Intentos | 10, cada 30 s |
| Plantillas de mensaje | `zabbix_media/telegram/message_templates.json` |

Cargar script y plantillas: `zbx_mediatype_update.py --name Telegram --script telegram.js --templates message_templates.json --param api_parse_mode=html` (ver [agents/scripts/README.md](../../agents/scripts/README.md)).

### Gmail (correo)

| Campo | Valor |
|---|---|
| Servidor SMTP | `smtp.gmail.com`, puerto 587, STARTTLS, autenticación usuario/contraseña |
| Remitente y usuario | `servicio_clientes@likson.com` |
| Contraseña | Contraseña de aplicación de Google (secreto) |
| Formato | HTML |
| Intentos | 10, cada 30 s |
| Plantillas de mensaje | `zabbix_media/gmail/message_templates.json` |

Formato de los mensajes de ambos medios: [alertas](../operacion/alertas.md).

## Usuarios (*Users → Users*)

| Usuario | Rol | Medios | Notas |
|---|---|---|---|
| `jjrl` | Super admin | Gmail: Warning y superiores. Telegram: High y superiores. Ambos 1-7, 00:00-24:00 | Cierre automático de sesión `60m` |
| `guest` | — | — | Desactivado |
| `coefi01-noc` (Coefi01, proveedor) | Solo lectura, grupo `Proveedores externos` (**sin acceso web**) | Gmail: soporte del proveedor + `servicio_clientes@likson.com` | Solo recibe los avisos de la acción *Aviso a proveedor Coefi01* ([procedimiento](../operacion/procedimientos/avisar-proveedor.md)) |
| `melb` (Maria Elena Lopez Balderas) | Solo lectura (grupo `Solo lectura`) | — | Consulta. Auto-logout `15m` |

### Roles y grupos de usuarios

Grupo `Proveedores externos`: *Frontend access: Disabled*, lectura en *Proveedores de internet* y *Routers & Switches Likson*. Solo para usuarios que reciben avisos (proveedores).

Definidos en `zabbix_access/solo_lectura.json` y aplicados con `zbx_access_apply.py`, o a mano según [dar acceso de solo lectura](../operacion/procedimientos/dar-acceso-lectura.md).

| Rol / grupo | Tipo | Permisos |
|---|---|---|
| Rol `Solo lectura` | User | Toda la interfaz del tipo *User* (dashboards, monitoring, services, inventory, reports). **Ninguna acción** (no reconoce ni cierra problemas, no ejecuta scripts, no edita dashboards). **Sin API** |
| Grupo `Solo lectura` | — | **Read** en: Access Points PPPoE Clients, CCTV, Enlaces PTP Backhaul, Enlaces PTP Troncales, Likson KPIs, Linux servers, Proveedores de internet, Routers & Switches Likson, Zabbix servers |
| Dashboard *Likson NOC* | — | Compartido con el grupo `Solo lectura`, solo lectura |

Al crear un grupo de hosts nuevo, añadirlo al grupo `Solo lectura` y al JSON.

## Acciones de trigger (*Alerts → Actions → Trigger actions*)

| Acción | Estado | Condiciones | Operaciones |
|---|---|---|---|
| Alert by severity | Activa | Severidad ≥ Warning **y** valor de la etiqueta `notificar` distinto de `no` | Paso 1: enviar a `jjrl` (todos los medios). Recuperación: avisar. Actualización: avisar a todos los implicados |
| Escalate unacknowledged High/Disaster | Activa | Severidad ≥ High **y** no existe la etiqueta `escalation` **y** valor de la etiqueta `notificar` distinto de `no` | Paso de 30 min. Pasos 2 → ∞: reenviar a `jjrl` mientras el problema **no esté reconocido**, con dos operaciones (*Send only to* Telegram y Gmail) y *Custom message* de recordatorio desde `zabbix_media/escalation.json` ([alertas](../operacion/alertas.md#recordatorios-de-la-escalada)) |
| Aviso a proveedor Coefi01 | Activa | Etiqueta `proveedor` = `Coefi01` **y** existe la etiqueta `aviso_proveedor` **y** `notificar` distinto de `no` | Paso de 5 min. Paso 2: enviar a `coefi01-noc` por Gmail (mensaje propio de `zabbix_media/proveedor_coefi01.json`). Recuperación: avisar a los implicados |
| Report problems to Zabbix administrators | Desactivada | (la acción por defecto) | — |

Condición `notificar` en la interfaz: acción → pestaña *Action* → *Conditions → Add* → *Type: Tag value*, *Tag:* `notificar`, *Operator: does not equal*, *Value:* `no` ([alertas](../operacion/alertas.md#solo-dashboard-etiqueta-notificarno)).

Las dos acciones activas tienen marcado **Pause operations for suppressed problems**: los problemas suprimidos por un [mantenimiento](../operacion/procedimientos/mantenimiento-programado.md) no notifican. Las acciones de descubrimiento, autorregistro e internas están desactivadas. Las notificaciones de actualización no se envían al usuario que hizo la actualización (comportamiento de Zabbix, ver [registro](../operacion/registro.md)).

## Macros globales (*Administration → Macros*)

| Macro | Tipo | Uso |
|---|---|---|
| `{$SNMP_COMMUNITY}` | Texto | Comunidad SNMP de lectura de todos los equipos. Es de tipo texto a propósito: los scripts `snmp_probe.py` y `snmp_walk.py` la leen por la API sin mostrarla |
| `{$ISP.COEFI01.CONTRACT}`, `{$ISP.COEFI01.TICKET}`, `{$ISP.COEFI01.WAN.IP}`, `{$ISP.COEFI01.GW.IP}`, `{$NOC.CONTACT}` | Texto | Datos de los correos al proveedor: contrato, ticket abierto (`No asignado` si no hay), IPs del servicio y contacto del NOC. Los valores solo están en Zabbix ([avisar al proveedor](../operacion/procedimientos/avisar-proveedor.md)) |
| `{$VFS.FS.FREE.MIN.WARN}` / `{$VFS.FS.FREE.MIN.CRIT}` | Texto | `1073741824` (1 GB). Las plantillas oficiales de MikroTik las usan en sus avisos de disco sin definirlas; sin estas macros, esos avisos quedan en error. Con 1 GB (más que la flash de un router) solo cuenta el % de uso: aviso al 80 %, crítico al 90 %. Las plantillas Linux no las usan |

## Ajustes generales (*Administration → General*)

| Sección | Ajuste |
|---|---|
| GUI | Zona horaria `America/Mexico_City` |
| Other | Frontend URL `https://zabbix.likson.com/`. Registrar traps SNMP no emparejados: sí. Inventario de hosts: automático. Timeout SNMP: 3 s |
| Autenticación | Contraseña mínima de 8 caracteres con reglas de complejidad. MFA desactivado: Cloudflare Access ya pide un código por correo ([registro](../operacion/registro.md)) |
| Login | Bloqueo tras 5 intentos durante 300 s |
| Housekeeping | Historial 31 días, tendencias 730 días, eventos 365 días, auditoría 90 días |

## Grupos de hosts

`Access Points PPPoE Clients`, `CCTV`, `Enlaces PTP Backhaul`, `Enlaces PTP Troncales`, `Likson KPIs`, `Linux servers`, `Proveedores de internet`, `Routers & Switches Likson`, `Zabbix servers`. Qué va en cada uno: [inventario](../operacion/inventario.md).

## Dashboard

"Likson NOC": se define en `zabbix_dashboards/likson_noc.json` y se aplica con `zbx_dashboard_apply.py` ([dashboard](../operacion/dashboard.md)).
