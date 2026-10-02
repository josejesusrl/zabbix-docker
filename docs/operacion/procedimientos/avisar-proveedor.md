# Avisar automáticamente a un proveedor de internet

> **Cuándo:** para que el soporte de un proveedor (hoy Coefi01) reciba por correo las incidencias de su servicio sin intervención de Likson.
> **Requisitos:** el proveedor ya vigilado ([vigilar un proveedor](anadir-gateway-proveedor.md)), respaldo reciente ([AGENTS.md](../../../AGENTS.md), regla 1), el correo de soporte del proveedor y el número de contrato.

El proveedor recibe un correo **5 minutos** después de que empiece una incidencia, si sigue activa, y otro cuando se resuelve. El mensaje tiene lo necesario para diagnosticar y nada de la infraestructura interna:

| Incluye | No incluye |
|---|---|
| Contrato, ticket del proveedor (si existe), referencia Likson (`#ID` del evento) | Nombres de host internos, IPs privadas, topología |
| Qué ocurre, en lenguaje del proveedor (etiqueta `aviso_proveedor` del trigger) y la medición | Otros proveedores, número de clientes |
| Inicio y duración (hora de Ciudad de México, UTC−6) | Enlaces a Zabbix |
| Nuestra IP pública en su red y su gateway | |
| **Estado del puerto WAN** de EDGE 01 (conectado o no, velocidad negociada, tráfico): descarta una desconexión de nuestro lado | |
| Contacto del NOC de Likson | |

No se le avisa si el fallo es nuestro: las dependencias impiden que se abran los avisos si cae EDGE 01 o la red del servidor Zabbix.

## Qué incidencias se le envían

Los triggers con la etiqueta **`aviso_proveedor`**, cuyo valor es el texto que lee el proveedor, en problemas con la etiqueta `proveedor=<Proveedor>`:

| Trigger | Texto para el proveedor |
|---|---|
| Corte del proveedor ([ficha](../plantillas/isp-gateway-fast-ping.md)) | El gateway del servicio no responde al ping |
| Pérdida intermitente hacia el gateway | Pérdida de paquetes intermitente hacia el gateway |
| Sin salida a Internet ([ficha](../plantillas/isp-internet-fast-ping.md)) | El gateway responde, pero no hay salida a Internet |
| Pérdida intermitente hacia Internet | Pérdida de paquetes intermitente hacia Internet |
| Bajada degradada (EDGE 01, [sección 4](anadir-gateway-proveedor.md#4-degradación-bajada-por-debajo-de-un-mínimo)) | Enlace conectado, pero con bajada inferior a 20 Mbps |

Las plantillas ya traen la etiqueta. En el trigger de degradación, creado en el host, se añade a mano en su pestaña *Tags*.

## Configurarlo (en la interfaz web)

1. **Macros globales** (*Administration → Macros*). Los datos personales y del contrato viven solo aquí, nunca en el repositorio:

   | Macro | Contenido |
   |---|---|
   | `{$ISP.COEFI01.CONTRACT}` | Número de contrato y titular |
   | `{$ISP.COEFI01.TICKET}` | Ticket abierto con el proveedor, o `No asignado` (ver abajo) |
   | `{$ISP.COEFI01.WAN.IP}` / `{$ISP.COEFI01.GW.IP}` | Nuestra IP pública en su red y su gateway |
   | `{$NOC.CONTACT}` | Nombre, teléfono y correo del contacto del NOC |

2. **Grupo de usuarios** *Users → User groups → Create*: `Proveedores externos`, ***Frontend access: Disabled***. *Host permissions*: **Read** en *Proveedores de internet* y en el grupo de EDGE 01 (*Routers & Switches Likson*). Zabbix solo notifica de hosts que el usuario puede leer; sin acceso a la web no ve nada.
3. **Usuario** *Users → Users → Create*:
   - *Username:* `coefi01-noc`.
   - *Groups:* `Proveedores externos`.
   - *Password:* una larga y aleatoria que no se apunta; el usuario nunca entra.
   - *Role:* `Solo lectura` (sin API).
   - *Media → Add*: tipo **Gmail**, *Send to* con el correo de soporte del proveedor y, como segundo destinatario, `servicio_clientes@likson.com`. Todas las severidades.
4. **Acción** *Alerts → Actions → Trigger actions → Create*: `Aviso a proveedor Coefi01`.
   - *Conditions:*
     - *Tag value* `proveedor` *equals* `Coefi01`.
     - *Tag name* *equals* `aviso_proveedor`.
     - *Tag value* `notificar` *does not equal* `no`.
   - *Operations:*
     - *Default operation step duration* `5m`.
     - Operación en los **pasos 2 → 2**: enviar a `coefi01-noc` solo por Gmail, con *Custom message*.
     - Marcar *Pause operations for suppressed problems*. Desmarcar *Notify about canceled escalations*.
   - *Recovery operations:* *Notify all involved* con *Custom message*. Solo lo recibe si ya recibió el aviso.
   - **Textos:** asunto y cuerpo HTML de `zabbix_media/proveedor_coefi01.json` (campos `operations[0]` y `recovery`).

## Ticket del proveedor

Cuando el proveedor abra un ticket, poner su número en `{$ISP.COEFI01.TICKET}` (*Administration → Macros*): aparecerá en los siguientes correos, incluido el de "Resuelto". Al cerrarse, volver a `No asignado`.

## Verificar

1. Con **tu propio correo** en el medio del usuario (en lugar del proveedor), forzar una incidencia de prueba que dure más de 5 min (sección *Con scripts*). Deben llegar el correo de incidencia y el de "Resuelto", sin nombres internos.
2. Poner el correo del proveedor y `servicio_clientes@likson.com` en el medio del usuario.
3. En *Reports → Action log*, filtrando por la acción, aparecen los envíos al proveedor.

## Con scripts

```sh
S=agents/scripts/run_remote.sh
# Macros globales (valores solo en Zabbix)
printf '%s\n' "$TOKEN" | $S zbx_set_macro.py --global --macro '{$ISP.COEFI01.TICKET}=No asignado'
# Usuario sin acceso web (primero con tu correo para probar)
printf '%s\n' "$TOKEN" | $S zbx_notify_user.py --user coefi01-noc --name "Coefi01 (proveedor)" --group "Proveedores externos" \
    --read "Proveedores de internet" "Routers & Switches Likson" --media Gmail --sendto <correo-de-prueba> --dry-run
# Acción
printf '%s\n' "$TOKEN" | $S -f zabbix_media/proveedor_coefi01.json zbx_action_apply.py proveedor_coefi01.json --dry-run
# Prueba de punta a punta (problema abierto 5 min 30 s)
printf '%s\n' "$TOKEN" | $S zbx_test_notification.py --severity 2 --group "Proveedores de internet" \
    --tag proveedor=Coefi01 "aviso_proveedor=Prueba de aviso automático (no es una incidencia real)" --hold 330
```

Para otro proveedor (p. ej. Telmex): copiar el JSON cambiando `Coefi01`, las macros (`{$ISP.TELMEX.…}`) y el usuario, y añadir `aviso_proveedor` a sus triggers.
