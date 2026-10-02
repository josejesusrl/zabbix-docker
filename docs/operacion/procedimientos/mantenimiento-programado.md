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
| `EDGE 01` | Prácticamente todo excepto el propio Zabbix server: usar los grupos de hosts. **Siempre** también `ISP-COEFI01-GW` e `ISP-COEFI01-INTERNET` (ver [trabajos en el router o el rack](#trabajos-en-el-router-o-el-rack-no-avisar-al-proveedor)) |
| Cableado del rack, `ether1`, fuente o equipo del proveedor | `EDGE 01`, `ISP-COEFI01-GW`, `ISP-COEFI01-INTERNET` ([trabajos en el router o el rack](#trabajos-en-el-router-o-el-rack-no-avisar-al-proveedor)) |

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

## Trabajos en el router o el rack: no avisar al proveedor

**Riesgo:** el soporte de Coefi01 recibe un correo automático 5 minutos después de que empiece una incidencia de su servicio ([avisar al proveedor](avisar-proveedor.md)). Si al trabajar en EDGE 01 o en el rack se desconecta `ether1`, se reinicia el router o se mueve el cable del proveedor, Zabbix vería "el gateway no responde" o "sin salida a Internet" y **avisaría al proveedor de un fallo nuestro**.

**Protección:** la acción del proveedor tiene *Pause operations for suppressed problems*. Mientras sus hosts están en mantenimiento, sus problemas quedan suprimidos y no se le envía nada.

**Hosts que siempre hay que incluir**, porque los avisos al proveedor salen de ellos:

| Host | Avisos al proveedor |
|---|---|
| `ISP-COEFI01-GW` | Corte del proveedor, pérdida intermitente hacia el gateway |
| `ISP-COEFI01-INTERNET` | Sin salida a Internet, pérdida intermitente hacia Internet |
| `EDGE 01` | Bajada degradada |

**Dos variantes:**

| Variante | Qué silencia | Cuándo usarla |
|---|---|---|
| **A. Solo el proveedor** (recomendada). En *Tags*: `proveedor` *Equals* `Coefi01` | Solo los avisos de Coefi01. **Tú sigues recibiendo** el resto: si cae EDGE 01, lo sabes | Trabajos breves en el rack o en `ether1` en los que quieres enterarte de cualquier otro efecto |
| **B. Todo** (sin *Tags*), añadiendo los grupos afectados | Todos los avisos de esos hosts | Reinicio o actualización de EDGE 01: caerá toda la red y ya lo sabes |

### Trabajo planificado

1. **Antes de empezar**, al menos 2 min antes (Zabbix lo aplica con hasta 1 min de retraso): crear el mantenimiento con los pasos de la [sección 2](#2-crear-el-mantenimiento), con los tres hosts y la variante elegida. Nombre `Trabajo en rack <fecha>`, duración con margen, por ejemplo 1 h para un trabajo de 30 min.
2. Comprobar en *Monitoring → Hosts* que los tres hosts tienen el icono de mantenimiento.
3. Hacer el trabajo.
4. **Antes de que termine el mantenimiento**, comprobar que todo está en verde: en *Monitoring → Problems* no hay problemas de los tres hosts, y en *Latest data* `Ping rápido al gateway` = Up y `Ping rápido a Internet 1/2` = Up. Si algo sigue abierto al terminar, **el aviso al proveedor sale en ese momento**, porque ya pasaron sus 5 min: ampliar el mantenimiento (editar *Active till* y la duración del periodo) hasta resolverlo.
5. Dejar que caduque o borrarlo (*Maintenance* → marcar → *Delete*) cuando todo esté bien.
6. Comprobar en *Reports → Action log* (filtro: acción *Aviso a proveedor Coefi01*) que no se envió nada.

### Desconexión accidental (sin mantenimiento)

Hay **5 minutos** desde el inicio de la incidencia hasta el aviso al proveedor:
1. **Lo más rápido:** *Alerts → Actions → Trigger actions* → *Aviso a proveedor Coefi01* → **Disable**. Detiene el aviso en cuanto se guarda.
2. Corregir la desconexión y comprobar que todo vuelve a verde.
3. **Volver a activar la acción** (*Enable*). Si se queda desactivada, el proveedor deja de recibir avisos reales. Comprobar en *Reports → Action log* que no salió nada.
4. Alternativa, si queda margen: crear el mantenimiento (variante A). Los problemas ya abiertos se suprimen en cuanto se aplica (≈1 min).

Si el aviso llegó a salir, responder al correo del proveedor indicando la referencia `#ID` y que fue un trabajo de Likson.

### Para agentes

- **Pedir confirmación** a la persona antes de crear, ampliar o terminar un mantenimiento: silencia avisos reales.
- Usar `zbx_maintenance.py` (sección *Con scripts*). Siempre `--dry-run` primero y respaldo reciente ([AGENTS.md](../../../AGENTS.md), regla 1).
- **No terminar** un mantenimiento con problemas abiertos de esos hosts. Comprobar antes con `zbx_host_status.py --host "EDGE 01" ISP-COEFI01-GW ISP-COEFI01-INTERNET`.
- **No desactivar** la acción del proveedor salvo que la persona lo pida, y comprobar al final que vuelve a estar activa.

## Con scripts

```sh
S=agents/scripts/run_remote.sh
# Ver mantenimientos activos y programados
printf '%s\n' "$TOKEN" | $S zbx_maintenance.py --list
# Variante A: solo avisos al proveedor, 60 min desde ahora (hora de Ciudad de México)
printf '%s\n' "$TOKEN" | $S zbx_maintenance.py --create "Trabajo en rack 2026-10-03" \
    --host "EDGE 01" ISP-COEFI01-GW ISP-COEFI01-INTERNET --minutes 60 --tag proveedor=Coefi01 --dry-run
# Variante B programada: todo, con los grupos afectados
printf '%s\n' "$TOKEN" | $S zbx_maintenance.py --create "Reinicio EDGE 01" --group "Routers & Switches Likson" \
    --minutes 30 --start "2026-10-03 02:00" --dry-run
# Terminar antes de tiempo (solo con todo en verde)
printf '%s\n' "$TOKEN" | $S zbx_maintenance.py --end "Trabajo en rack 2026-10-03" --dry-run
```

## Notas

- Los triggers con `nodata()`, como *Cloudflared: Tunnel connector not responding* o *no data for 30m*, no se disparan durante un mantenimiento *No data collection*, ni durante el mismo tiempo después de que acabe.
- Un mantenimiento **no** detiene la recogida de traps ni los guarda en otro sitio: siguen apareciendo en *Latest data*.
- Para silenciar un solo problema ya abierto, sin programar nada, se puede usar *Update → Suppress* en *Monitoring → Problems*.
