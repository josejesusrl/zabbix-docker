# Programar un mantenimiento (silenciar alertas durante un trabajo)

> **Cuándo:** antes de un trabajo planificado que va a cortar equipos: subir a una torre, realinear un enlace, cambiar un switch, actualizar firmware o reiniciar un router. Evita que Telegram y Gmail envíen alertas de algo que ya se sabe.
> **Requisitos:** usuario administrador (`jjrl`). Crear un mantenimiento modifica la configuración: respaldo reciente ([AGENTS.md](../../../AGENTS.md), regla 1). Todo se hace desde la interfaz web.

Durante el mantenimiento Zabbix sigue monitoreando. Los problemas se marcan como **suprimidos**: aparecen en *Monitoring → Problems* con un icono de llave inglesa, pero las acciones no envían notificaciones ni escalan. Al terminar, si el problema sigue abierto, las notificaciones se reanudan.

## 1. Decidir qué equipos incluir

Incluir el equipo en el que se trabaja **y todos los que dependen de él**. Las dependencias silencian las alertas de disponibilidad de los hijos, pero no otras, como "sin clientes conectados" o los traps. Los equipos que cuelgan de cada uno están en la [topología](../inventario.md#topología-y-dependencias-actuales). También se pueden buscar en *Data collection → Hosts* filtrando por la etiqueta `uplink`.

| Trabajo | Incluir |
|---|---|
| Un AP | Solo ese AP |
| Un enlace PTP (p. ej. Pintores) | Los dos extremos y todo lo que cuelga del extremo lejano (Pintores → Cañadas) |
| `MAIN-SW-01` | El switch y los hosts con `uplink = MAIN-SW-01` |
| NAS-01 o NAS-03 | El NAS, los switches y APs que cuelgan de él y sus hijos |
| `EDGE 01` | Prácticamente todo excepto el propio Zabbix server: usar los grupos de hosts |

## 2. Crear el mantenimiento

*Data collection → Maintenance → Create maintenance period*:

1. **Name:** qué y cuándo, p. ej. `Realineación enlace Pintores 2026-10-05`.
2. **Maintenance type:**
   - **With data collection** (recomendado): se siguen guardando datos y queda el historial del corte.
   - *No data collection*: solo si el equipo va a enviar datos falsos durante el trabajo, por ejemplo un equipo de pruebas con la misma IP.
3. **Active since / Active till:** ventana que envuelve todas las ventanas del periodo. Para un trabajo único, el mismo día.
4. **Periods → Add:**
   - *Period type:* **One time only** para un trabajo puntual. *Daily*, *Weekly* o *Monthly* para ventanas fijas, p. ej. reinicios semanales.
   - *Date:* inicio. Dejar **15 min antes** de la hora prevista, porque Zabbix aplica el mantenimiento con hasta 1 min de retraso.
   - *Maintenance period length:* duración estimada con margen. Si el trabajo se alarga, editar el mantenimiento y ampliarla.
5. **Host groups / Hosts:** los equipos del paso 1. Un grupo completo incluye también los hosts que se añadan después.
6. **Tags** (opcional): limitar el silencio a ciertos problemas, p. ej. `scope = availability`, para seguir recibiendo otros avisos. Normalmente vacío.
7. **Description:** quién hace el trabajo y un teléfono de contacto.
8. **Add**.

## 3. Durante y después del trabajo

- En *Monitoring → Hosts* los equipos muestran el icono de mantenimiento. Los problemas que se abran aparecen como suprimidos (*Monitoring → Problems*, marcar *Show suppressed problems* para verlos).
- Al terminar, comprobar que todo vuelve a verde **antes** de que acabe el periodo. Si queda algún problema abierto al finalizar, Zabbix enviará su notificación.
- Si el trabajo termina antes, se puede dejar que el periodo caduque solo o acortarlo editando el mantenimiento.
- Borrar los mantenimientos de una sola vez que ya han pasado (*Maintenance* → marcar → *Delete*) para mantener la lista limpia. Los periódicos se conservan.

## 4. Verificar

1. En la ventana del mantenimiento, *Monitoring → Hosts* muestra el icono de mantenimiento en los equipos incluidos.
2. Un corte durante el trabajo no genera mensajes en Telegram ni en Gmail. En *Reports → Action log* no aparecen envíos para esos problemas.
3. Las acciones *Alert by severity* y *Escalate unacknowledged High/Disaster* tienen marcado **Pause operations for suppressed problems** (*Alerts → Actions → Trigger actions* → acción → *Operations*), que viene así por defecto. Si alguien lo desmarca, los mantenimientos dejan de silenciar ([configuración base](../../despliegue/configuracion-base.md)).

## Notas

- Los triggers con `nodata()`, como *Cloudflared: Tunnel connector not responding* o *no data for 30m*, no se disparan durante un mantenimiento *No data collection*, ni durante el mismo tiempo después de que acabe.
- Un mantenimiento **no** detiene la recogida de traps ni los guarda en otro sitio: siguen apareciendo en *Latest data*.
- Para silenciar un solo problema ya abierto, sin programar nada, se puede usar *Update → Suppress* en *Monitoring → Problems*.
