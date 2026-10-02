# Documentación: índice

Zabbix 7.4 de Likson (`zabbix.likson.com`). Cada documento empieza indicando **cuándo** usarlo. Las reglas para cambiar el proyecto o la producción están en [AGENTS.md](../AGENTS.md) y aplican también a las personas.

Tres formas de encontrar algo:
1. [Por necesidad](#1-por-necesidad): qué leer según lo que vas a hacer.
2. [Busco…](#2-busco): un tema o una palabra y el documento donde está.
3. [Mapa completo](#3-mapa-completo): todos los documentos.

`python3 agents/scripts/docs_check.py` comprueba que todos los documentos estén enlazados desde este índice.

## 1. Por necesidad

### Soy nuevo

1. [Inventario y topología](operacion/inventario.md): qué equipos hay, cómo se nombran y de quién depende cada uno.
2. [Dashboard "Likson NOC"](operacion/dashboard.md) y [mapas de red](operacion/mapas.md): la vista diaria y la topología en vivo.
3. [Alertas](operacion/alertas.md): quién recibe qué, qué dice cada mensaje y qué hacer con un problema.
4. [Registro](operacion/registro.md): decisiones, situaciones conocidas y pendientes.

### Algo falla

- [Solución de problemas](operacion/solucion-de-problemas.md): síntomas frecuentes y cómo resolverlos.
- [Revisar falsos positivos y salud del monitoreo](operacion/procedimientos/revisar-falsos-positivos.md).
- [Registro](operacion/registro.md): antes de "arreglar" algo, comprobar que no está así a propósito.

### Añadir o cambiar equipos

Antes de cualquier cambio, respaldo (`sudo ./server_backup.sh`). Leer las [particularidades por tipo de equipo](operacion/plantillas.md#particularidades-por-tipo-de-equipo).

| Tarea | Procedimiento |
|---|---|
| Añadir un AP Ubiquiti | [anadir-ap-ubiquiti](operacion/procedimientos/anadir-ap-ubiquiti.md) |
| Añadir un router MikroTik (incluidos NAS PPPoE) | [anadir-router-mikrotik](operacion/procedimientos/anadir-router-mikrotik.md) |
| Añadir un switch | [anadir-switch](operacion/procedimientos/anadir-switch.md) |
| Añadir un servidor Linux (LAN o remoto) | [anadir-servidor-linux](operacion/procedimientos/anadir-servidor-linux.md) |
| Añadir un enlace PTP Mimosa | [enlace-ptp-mimosa](operacion/procedimientos/enlace-ptp-mimosa.md) |
| Añadir un enlace PTP Ubiquiti | [enlace-ptp-ubiquiti](operacion/procedimientos/enlace-ptp-ubiquiti.md) |
| Añadir una cámara o NVR Hikvision | [anadir-camara-hikvision](operacion/procedimientos/anadir-camara-hikvision.md) |
| Vigilar un proveedor de internet (gateway y salida a Internet) | [anadir-gateway-proveedor](operacion/procedimientos/anadir-gateway-proveedor.md) |
| Avisar automáticamente al proveedor de sus incidencias | [avisar-proveedor](operacion/procedimientos/avisar-proveedor.md) |
| Configurar dependencias (siempre, en cada alta) | [dependencias](operacion/procedimientos/dependencias.md) |
| Configurar el envío de traps | [configurar-traps](operacion/procedimientos/configurar-traps.md) |
| Ajustar umbrales de un equipo | [ajustar-umbrales](operacion/procedimientos/ajustar-umbrales.md) |
| Cambiar la IP de un equipo | [cambiar-ip](operacion/procedimientos/cambiar-ip.md) |
| Dar de baja un equipo | [baja-equipo](operacion/procedimientos/baja-equipo.md) |
| Crear o modificar una plantilla propia | [plantilla-propia](operacion/procedimientos/plantilla-propia.md) |

### Alertas, accesos y trabajos

| Tarea | Procedimiento |
|---|---|
| Cambiar el texto de los avisos (Telegram, Gmail, recordatorios) | [cambiar-mensajes](operacion/procedimientos/cambiar-mensajes.md) |
| Silenciar avisos durante un trabajo planificado | [mantenimiento-programado](operacion/procedimientos/mantenimiento-programado.md) |
| Trabajar en el router o el rack sin avisar al proveedor | [mantenimiento-programado, trabajos en el router o el rack](operacion/procedimientos/mantenimiento-programado.md#trabajos-en-el-router-o-el-rack-no-avisar-al-proveedor) |
| Dar acceso de solo lectura a una persona | [dar-acceso-lectura](operacion/procedimientos/dar-acceso-lectura.md) |
| Dar acceso desde Internet (Cloudflare Access) | [acceso externo, sección 2](despliegue/acceso-externo.md#2-proteger-la-web-con-access) |

### Servidor

| Tarea | Documento |
|---|---|
| Instalar desde cero | [Instalación](despliegue/instalacion.md) |
| Configurar el host "Zabbix server" (instalación o reconstrucción sin BD) | [Host Zabbix server](despliegue/host-zabbix-server.md) |
| Recuperar tras perder el servidor, o migrar otro Zabbix | [Restauración y migración](despliegue/restauracion-y-migracion.md) |
| Acceso desde Internet: túnel de Cloudflare y Access | [Acceso externo](despliegue/acceso-externo.md) |
| Estado, logs, rendimiento, copiar respaldos | [Mantenimiento](despliegue/mantenimiento.md) |
| Actualizar Zabbix (incluido 8.0 LTS), PostgreSQL o `cloudflared` | [Actualizar](despliegue/actualizar.md) |
| Medios, usuarios, acciones y ajustes (lo que solo está en la BD) | [Configuración base](despliegue/configuracion-base.md) |

### Soy un agente de IA

1. [AGENTS.md](../AGENTS.md): reglas y checklist de sesión.
2. [agents/scripts/README.md](../agents/scripts/README.md): scripts de la API. Reutilizarlos antes de escribir nada nuevo.
3. Este índice, para localizar el documento que hay que actualizar en el mismo commit que el cambio.
4. Al terminar: `python3 agents/scripts/docs_check.py`, y con `--zabbix` si cambiaron hosts.

## 2. Busco…

| Tema o palabra clave | Dónde |
|---|---|
| Acciones de trigger, condiciones, escalada | [Configuración base](despliegue/configuracion-base.md#acciones-de-trigger-alerts--actions--trigger-actions) · [alertas](operacion/alertas.md) |
| Actualizar versión de Zabbix, 8.0 LTS | [Actualizar](despliegue/actualizar.md) |
| airOS, Ubiquiti, SNMPv1, GPS, señal de clientes | [Plantilla airOS 8](operacion/plantillas/ubiquiti-airos8.md) · [airOS 6](operacion/plantillas/ubiquiti-airmax-m-airos6.md) · [añadir AP](operacion/procedimientos/anadir-ap-ubiquiti.md) |
| Bloqueo de IP de cámaras Hikvision | [Añadir una cámara](operacion/procedimientos/anadir-camara-hikvision.md) |
| Cámaras, NVR, `{$PASSWORD}`, resolución del canal | [Añadir una cámara](operacion/procedimientos/anadir-camara-hikvision.md) |
| Certificado TLS, autofirmado | [Instalación, sección 2](despliegue/instalacion.md#2-arrancar-y-crear-el-certificado) · [host Zabbix server](despliegue/host-zabbix-server.md) |
| Cloudflare Tunnel, Access, token del túnel, `cloudflared` | [Acceso externo](despliegue/acceso-externo.md) · [plantilla del túnel](operacion/plantillas/cloudflare-tunnel.md) |
| Ticket del proveedor, aviso automático a Coefi01 | [Avisar al proveedor](operacion/procedimientos/avisar-proveedor.md) |
| Coefi01, gateway, cortes y degradación del proveedor, evidencia, Uptime Kuma | [Vigilar un proveedor](operacion/procedimientos/anadir-gateway-proveedor.md) · [ping rápido al gateway](operacion/plantillas/isp-gateway-fast-ping.md) · [salida a Internet](operacion/plantillas/isp-internet-fast-ping.md) |
| Contraseñas, secretos, comunidad SNMP | [AGENTS.md, regla 4](../AGENTS.md#regla-4--secretos) · [configuración base](despliegue/configuracion-base.md#macros-globales-administration--macros) |
| CPU, KPIs del dashboard | [Plantilla Likson KPIs](operacion/plantillas/likson-kpis.md) · [dashboard](operacion/dashboard.md) |
| Dependencias, `uplink`, equipos raíz, corte de red del servidor | [Dependencias](operacion/procedimientos/dependencias.md) · [trigger raíz](operacion/plantillas/likson-topology-root.md) |
| Disco, temperaturas, carga de servidores | [Añadir un servidor Linux](operacion/procedimientos/anadir-servidor-linux.md) · [plantilla de temperaturas](operacion/plantillas/linux-hwmon-temperature.md) |
| Docker, `zbx`, logs, estado del stack | [Mantenimiento](despliegue/mantenimiento.md) |
| Enlaces PTP, Mimosa, capacidad, PHY | [Plantilla Mimosa](operacion/plantillas/mimosa-c5c.md) · [enlace Mimosa](operacion/procedimientos/enlace-ptp-mimosa.md) · [enlace Ubiquiti](operacion/procedimientos/enlace-ptp-ubiquiti.md) |
| `escalation=off`, `notificar=no` | [Alertas](operacion/alertas.md) |
| Falsos positivos, *flapping* | [Revisar falsos positivos](operacion/procedimientos/revisar-falsos-positivos.md) · [registro](operacion/registro.md) |
| Firewall, puertos, NAT | [Instalación, requisitos](despliegue/instalacion.md#requisitos) · [acceso externo](despliegue/acceso-externo.md) |
| Grupos de hosts, convención de nombres (`SITIO-ROL-NN`) | [Inventario, convenciones](operacion/inventario.md#convenciones) |
| Mantenimiento programado (silenciar avisos), trabajos en el rack, desconexión accidental | [Programar un mantenimiento](operacion/procedimientos/mantenimiento-programado.md) · [sin avisar al proveedor](operacion/procedimientos/mantenimiento-programado.md#trabajos-en-el-router-o-el-rack-no-avisar-al-proveedor) |
| Mapas, topología | [Mapas de red](operacion/mapas.md) · [inventario](operacion/inventario.md) |
| Mensajes de Telegram y Gmail | [Alertas](operacion/alertas.md) · [cambiar mensajes](operacion/procedimientos/cambiar-mensajes.md) |
| MikroTik, PPPoE, traps de enlace | [Añadir un router](operacion/procedimientos/anadir-router-mikrotik.md) · [plantilla de traps](operacion/plantillas/mikrotik-link-traps.md) · [configurar traps](operacion/procedimientos/configurar-traps.md) |
| Pendientes, decisiones, situaciones conocidas | [Registro](operacion/registro.md) |
| Plantillas: catálogo, oficiales, particularidades | [Plantillas](operacion/plantillas.md) |
| Puertos de switch, desconexiones, velocidad | [Plantilla de puertos](operacion/plantillas/switch-port-changes.md) · [añadir un switch](operacion/procedimientos/anadir-switch.md) |
| Rendimiento (cachés, pingers, PostgreSQL) | [Mantenimiento, ajustes de rendimiento](despliegue/mantenimiento.md#ajustes-de-rendimiento) |
| Respaldo, restauración, servidor nuevo | [AGENTS.md, regla 1](../AGENTS.md#regla-1--respaldo-antes-de-modificar-producción) · [restauración](despliegue/restauracion-y-migracion.md) · [mantenimiento](despliegue/mantenimiento.md#copiar-los-respaldos-fuera-del-servidor) |
| Scripts de la API, token | [agents/scripts/README.md](../agents/scripts/README.md) |
| Umbrales, macros de host | [Ajustar umbrales](operacion/procedimientos/ajustar-umbrales.md) · ficha de cada [plantilla](operacion/plantillas.md) |
| Usuarios, roles, solo lectura | [Dar acceso de solo lectura](operacion/procedimientos/dar-acceso-lectura.md) · [configuración base](despliegue/configuracion-base.md#usuarios-users--users) |

## 3. Mapa completo

```
README.md · AGENTS.md · CLAUDE.md · agents/scripts/README.md
docs/
├── README.md                  este índice
├── despliegue/                el servidor
└── operacion/                 Zabbix en el día a día
    ├── plantillas/            una ficha por plantilla propia
    └── procedimientos/        un fichero por tarea: Cuándo, Requisitos, pasos, Verificar, Con scripts
```

**Proyecto**

| Documento | Contenido |
|---|---|
| [README.md](../README.md) | Portada del repositorio |
| [AGENTS.md](../AGENTS.md) | Reglas para personas y agentes: respaldo, secretos, flujo de cambios, scripts, documentación |
| [agents/scripts/README.md](../agents/scripts/README.md) | Catálogo y uso de los scripts de la API |

**Despliegue (`docs/despliegue/`)**

| Documento | Contenido |
|---|---|
| [instalacion.md](despliegue/instalacion.md) | Requisitos, clonar, preparar, arrancar, firewall, tareas programadas |
| [host-zabbix-server.md](despliegue/host-zabbix-server.md) | Plantillas, macros y dependencias del host que monitorea el propio servidor |
| [acceso-externo.md](despliegue/acceso-externo.md) | Cloudflare Tunnel y Access; servidor nuevo; rotar el token |
| [restauracion-y-migracion.md](despliegue/restauracion-y-migracion.md) | Restaurar desde respaldos, migrar otra instalación, reconstruir sin BD |
| [mantenimiento.md](despliegue/mantenimiento.md) | Estado, logs, ajustes de rendimiento, copiar respaldos |
| [actualizar.md](despliegue/actualizar.md) | Versiones menores y mayores de Zabbix, PostgreSQL y `cloudflared` |
| [configuracion-base.md](despliegue/configuracion-base.md) | Medios, usuarios, roles, acciones, macros globales, ajustes, grupos de hosts |

**Operación (`docs/operacion/`)**

| Documento | Contenido |
|---|---|
| [inventario.md](operacion/inventario.md) | Convenciones, topología e inventario generado desde Zabbix |
| [plantillas.md](operacion/plantillas.md) | Catálogo de plantillas propias y oficiales, particularidades por tipo de equipo |
| [alertas.md](operacion/alertas.md) | Quién recibe qué, contenido de los mensajes, etiquetas `escalation` y `notificar` |
| [dashboard.md](operacion/dashboard.md) | Páginas y widgets del dashboard "Likson NOC" |
| [mapas.md](operacion/mapas.md) | Mapas de red generados desde la topología |
| [solucion-de-problemas.md](operacion/solucion-de-problemas.md) | Síntomas y soluciones |
| [registro.md](operacion/registro.md) | Objetos desactivados, situaciones conocidas, decisiones y pendientes |

**Fichas de plantillas propias (`docs/operacion/plantillas/`)**

[Mimosa C5C](operacion/plantillas/mimosa-c5c.md) · [Ubiquiti airOS 8](operacion/plantillas/ubiquiti-airos8.md) · [Ubiquiti airMAX M (airOS 6)](operacion/plantillas/ubiquiti-airmax-m-airos6.md) · [MikroTik link traps](operacion/plantillas/mikrotik-link-traps.md) · [Switch port changes](operacion/plantillas/switch-port-changes.md) · [Linux hwmon temperature](operacion/plantillas/linux-hwmon-temperature.md) · [Likson KPIs](operacion/plantillas/likson-kpis.md) · [Cloudflare Tunnel](operacion/plantillas/cloudflare-tunnel.md) · [ISP gateway fast ping](operacion/plantillas/isp-gateway-fast-ping.md) · [ISP internet fast ping](operacion/plantillas/isp-internet-fast-ping.md) · [Likson topology root](operacion/plantillas/likson-topology-root.md)

**Procedimientos (`docs/operacion/procedimientos/`)**: todos están en las tablas de la [sección 1](#1-por-necesidad).
