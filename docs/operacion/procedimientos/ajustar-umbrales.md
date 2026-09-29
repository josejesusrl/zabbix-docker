# Ajustar umbrales

> **Cuándo:** cuando un aviso salta demasiado o demasiado poco para un equipo concreto.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

Las plantillas propias usan macros; los umbrales se cambian **en el host**, sin tocar la plantilla:

1. Host → pestaña **Macros** → *Inherited and host macros* → **Change** en la macro → nuevo valor → **Update**.
2. Con **contexto**, solo para un elemento concreto:
   - `{$UBNT.STA.SIGNAL.MIN.WARN:"NOMBRE_CLIENTE"}` = `-80`: un cliente lejano con señal débil aceptable.
   - `{$TEMP.CRIT:"nvme"}` = `70`: umbral propio para los discos NVMe.
3. Para cambiar el valor por defecto en todos los hosts, se edita la macro en la plantilla ([Crear o modificar una plantilla propia](plantilla-propia.md)).

## Con scripts (opcional)

no hay script específico: las macros se cambian en la interfaz o con la API. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
