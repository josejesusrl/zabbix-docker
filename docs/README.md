# Documentación

Cada documento empieza indicando **cuándo** usarlo. Las reglas para modificar el proyecto o la producción están en [AGENTS.md](../AGENTS.md) (aplican también a personas).

## Soy nuevo

1. [Inventario y topología](operacion/inventario.md): qué equipos hay, cómo se nombran y de quién depende cada uno.
2. [Dashboard "Likson NOC"](operacion/dashboard.md): la vista diaria.
3. [Alertas](operacion/alertas.md): quién recibe qué, cómo se leen los mensajes y qué hacer con un problema.
4. [Registro](operacion/registro.md): decisiones tomadas, situaciones conocidas y pendientes.

## Algo falla

- [Solución de problemas](operacion/solucion-de-problemas.md): síntomas frecuentes y cómo resolverlos.
- [Revisar falsos positivos y salud del monitoreo](operacion/procedimientos/revisar-falsos-positivos.md).
- [Registro](operacion/registro.md): antes de "arreglar" algo, comprobar que no está así a propósito.

## Añadir o cambiar equipos

Antes de cualquier cambio: respaldo (`sudo ./server_backup.sh`). Leer las [particularidades por tipo de equipo](operacion/plantillas.md#particularidades-por-tipo-de-equipo).

| Tarea | Procedimiento |
|---|---|
| Añadir un AP Ubiquiti | [anadir-ap-ubiquiti](operacion/procedimientos/anadir-ap-ubiquiti.md) |
| Añadir un router MikroTik (incluidos NAS PPPoE) | [anadir-router-mikrotik](operacion/procedimientos/anadir-router-mikrotik.md) |
| Añadir un switch | [anadir-switch](operacion/procedimientos/anadir-switch.md) |
| Añadir un servidor Linux (LAN o remoto) | [anadir-servidor-linux](operacion/procedimientos/anadir-servidor-linux.md) |
| Añadir un enlace PTP Mimosa | [enlace-ptp-mimosa](operacion/procedimientos/enlace-ptp-mimosa.md) |
| Añadir un enlace PTP Ubiquiti | [enlace-ptp-ubiquiti](operacion/procedimientos/enlace-ptp-ubiquiti.md) |
| Configurar dependencias (siempre, en cada alta) | [dependencias](operacion/procedimientos/dependencias.md) |
| Configurar el envío de traps | [configurar-traps](operacion/procedimientos/configurar-traps.md) |
| Ajustar umbrales de un equipo | [ajustar-umbrales](operacion/procedimientos/ajustar-umbrales.md) |
| Cambiar la IP de un equipo | [cambiar-ip](operacion/procedimientos/cambiar-ip.md) |
| Dar de baja un equipo | [baja-equipo](operacion/procedimientos/baja-equipo.md) |
| Crear o modificar una plantilla propia | [plantilla-propia](operacion/procedimientos/plantilla-propia.md) |
| Dar acceso de solo lectura a una persona | [dar-acceso-lectura](operacion/procedimientos/dar-acceso-lectura.md) |
| Silenciar alertas durante un trabajo planificado | [mantenimiento-programado](operacion/procedimientos/mantenimiento-programado.md) |

Catálogo de plantillas, macros y triggers: [plantillas](operacion/plantillas.md).

## Servidor

| Tarea | Documento |
|---|---|
| Instalar desde cero | [Instalación](despliegue/instalacion.md) |
| Recuperar tras perder el servidor o migrar otro Zabbix | [Restauración y migración](despliegue/restauracion-y-migracion.md) |
| Estado, logs, actualizar Zabbix, probar traps, copiar respaldos | [Mantenimiento](despliegue/mantenimiento.md) |
| Medios, usuarios, acciones y ajustes (lo que solo está en la BD) | [Configuración base](despliegue/configuracion-base.md) |
| Acceso desde Internet (Cloudflare Tunnel), dar acceso a una persona | [Acceso externo](despliegue/acceso-externo.md) |

## Soy un agente de IA

1. [AGENTS.md](../AGENTS.md): reglas y checklist de sesión.
2. [agents/scripts/README.md](../agents/scripts/README.md): scripts de la API; reutilizarlos antes de escribir nada nuevo.
3. Al terminar: `python3 agents/scripts/docs_check.py`.

## Organización

```
docs/
├── README.md                  este índice
├── despliegue/                el servidor: instalación, restauración, mantenimiento, acceso externo, configuración base
└── operacion/                 Zabbix en el día a día
    ├── inventario.md          qué hay (cambia con cada alta o baja)
    ├── plantillas.md          catálogo y particularidades
    ├── alertas.md, dashboard.md
    ├── procedimientos/        un fichero por tarea: Cuándo, Requisitos, pasos, Verificación, Con scripts
    ├── solucion-de-problemas.md
    └── registro.md            decisiones, situaciones conocidas y pendientes
```
