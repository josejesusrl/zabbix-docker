# Registro de decisiones y situaciones

Lo que se hizo a propósito y por qué, para que nadie lo "corrija" por error.

## Objetos desactivados a propósito

No son errores. Se desactivaron porque no aplican a ese equipo y solo generaban ruido. Si se reactiva alguno, hay que actualizar esta tabla.

| Host | Objeto | Motivo |
|---|---|---|
| Zabbix server | Items de *connector*, *ipmi*, *vmware* (plantilla *Zabbix server health*) | Esos procesos del server no están activados. Los items siempre serían no soportados |
| Zabbix server, server-04 | *Number of installed packages* | El agente corre en un contenedor y no puede leer la base de paquetes del host (en server-04, además, el agente 6.0 no conoce la clave) |
| Zabbix server | *Interface wlp3s0: Speed* | Tarjeta WiFi del portátil sin uso, no informa de velocidad |
| server-04 | *Interface enp2s0: Speed* | La tarjeta informa de velocidad desconocida (-1) |
| server-04 | *Kernel memory enabled*, *Kernel memory TCP enabled* (Docker) | Las versiones recientes de Docker ya no publican ese dato |
| NAS-01, NAS-03 | *SNMP walk wireless interfaces* | Routers sin radios. Leía cada minuto toda la tabla de interfaces (con las sesiones PPPoE) y sobrecargaba el router |
| AP-Lk_Trunk_01_A, STA-Lk_Trunk_01_A | Trigger *Interface wifi0(): Ethernet has changed to lower speed* (plantilla *Network Generic Device*) | La velocidad de `wifi0` es la capacidad radio adaptativa y cambia continuamente. La capacidad se vigila con los triggers de velocidad PHY de *Mimosa C5C* |
| server-04 | Discos `/etc/hosts`, `/etc/hostname`, `/etc/resolv.conf`, `/etc/zabbix/zabbix_agentd.d` | No descubiertos por las macros `{$VFS.FS.FSNAME.*}` (montajes del contenedor). Se borran solos a los 7 días |

## Situaciones conocidas

Avisos reales que se mantienen a propósito. No son falsos positivos.

| Equipo | Situación | Decisión |
|---|---|---|
| NAS-03 (RB2011iL-RM) | CPU al 91–95 % cada noche (≈ 16:00–00:00, hora de México), con picos del 98 %. El trigger *High CPU utilization* de la plantilla se abre y cierra varias veces por noche (*Warning*, Gmail) | Se deja como está: indica que el RB2011 está saturado y necesita reemplazo. Al cambiar el equipo, revisar la plantilla de modelo y los ajustes de NAS ([Añadir un router MikroTik](procedimientos/anadir-router-mikrotik.md)) |
| Zabbix server | El 2026-09-29 la tarjeta `enp2s0` perdió el enlace 2 min y volvió a **100 Mbps (downshifted)**: cable o conector que no soporta gigabit | Revisar o cambiar el cable. Mientras tanto, los equipos raíz dependen de su *Link down* ([Configurar las dependencias de un host](procedimientos/dependencias.md)) |

## Decisiones de configuración

| Decisión | Motivo |
|---|---|
| Las notificaciones de **actualización** (reconocer, comentar) no llegan a quien las hace | Comportamiento de Zabbix: no se envían al usuario que hizo la actualización. Se probó una operación explícita y no cambia nada; se deja así |
| Telegram solo para High y superiores; Gmail desde Warning | Telegram es para lo urgente; el resto queda en el correo |
| `{$SNMP_COMMUNITY}` es macro de tipo texto, no secreta | Los scripts de sondeo la leen por la API sin mostrarla ([configuración base](../despliegue/configuracion-base.md)) |
| Las dependencias se **añaden**, nunca se reemplazan | Las plantillas traen dependencias internas (p. ej. *Link down* → *Speed changed*) que se perderían ([dependencias](procedimientos/dependencias.md)) |
| Certificado autofirmado | Los puertos 80/443 aún no están redirigidos en el NAT; Let's Encrypt no puede validar ([instalación](../despliegue/instalacion.md#2-arrancar-y-emitir-el-certificado)) |

## Pendientes

| Pendiente | Qué hacer |
|---|---|
| Certificado de Let's Encrypt | Redirigir 80 y 443 en el NAT y ejecutar `sudo ./server_letsencrypt.sh issue` |
| Respaldos fuera del servidor | Copiarlos periódicamente ([mantenimiento](../despliegue/mantenimiento.md#copiar-los-respaldos-fuera-del-servidor)) |
| MFA desactivado | Activar TOTP en *Users → Authentication → MFA settings* |
| Cierre automático de sesión de `jjrl` en `0` | Poner un valor (p. ej. 15 min) en *User settings → Profile* |
| Token de API para agentes (caduca 2026-09-30) | Revocarlo al terminar la sesión de trabajo (*User settings → API tokens*) |
| Cable del Zabbix server a 100 Mbps | Ver *Situaciones conocidas* |
