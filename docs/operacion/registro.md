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
| CANADAS-CAM-01 (antes CAM 05 Canadas del bosque) | Lecturas HTTP fallidas que se abren y cierran solas (22 avisos en 14 h, 2026-09-30), probablemente por NAS-03 saturado. No está caída: responde al ping | Etiqueta `notificar=no` (2026-10-01): sus problemas solo se ven en el dashboard ([alertas](alertas.md#solo-dashboard-etiqueta-notificarno)). Revisar al reemplazar NAS-03 |
| NVR 01 | Item *Memory utilization* no soportado: el NVR devuelve el valor con un salto de línea delante y la plantilla *Hikvision camera by HTTP* (pensada para cámaras) no lo convierte | Se deja así: el resto de datos del NVR (canales, CPU, reinicios) funciona. Si hace falta la memoria, crear una plantilla propia derivada con un paso *Trim* |
| NAS-03 (RB2011iL-RM) | CPU al 91–95 % cada noche (≈ 16:00–00:00, hora de México), con picos del 98 %. El trigger *High CPU utilization* de la plantilla se abre y cierra varias veces por noche (*Warning*, Gmail) | Se deja como está: indica que el RB2011 está saturado y necesita reemplazo. Al cambiar el equipo, revisar la plantilla de modelo y los ajustes de NAS ([Añadir un router MikroTik](procedimientos/anadir-router-mikrotik.md)) |
| Zabbix server | El 2026-09-29 la tarjeta `enp2s0` perdió el enlace 2 min y volvió a **100 Mbps (downshifted)**: cable o conector que no soporta gigabit | Revisar o cambiar el cable. Mientras tanto, los equipos raíz dependen de su *Link down* ([Configurar las dependencias de un host](procedimientos/dependencias.md)) |

## Decisiones de configuración

| Decisión | Motivo |
|---|---|
| Las notificaciones de **actualización** (reconocer, comentar) no llegan a quien las hace | Comportamiento de Zabbix: no se envían al usuario que hizo la actualización. Se probó una operación explícita y no cambia nada; se deja así |
| Telegram solo para High y superiores; Gmail desde Warning | Telegram es para lo urgente; el resto queda en el correo |
| `{$SNMP_COMMUNITY}` es macro de tipo texto, no secreta | Los scripts de sondeo la leen por la API sin mostrarla ([configuración base](../despliegue/configuracion-base.md)) |
| Las dependencias se **añaden**, nunca se reemplazan | Las plantillas traen dependencias internas (p. ej. *Link down* → *Speed changed*) que se perderían ([dependencias](procedimientos/dependencias.md)) |
| Acceso público por **Cloudflare Tunnel + Access**, sin puertos redirigidos en el NAT (2026-09-29) | No se expone ningún puerto a Internet. Access añade un login previo al de Zabbix y Cloudflare gestiona el certificado público. Sustituye a Let's Encrypt con redirección de 80/443 ([acceso externo](../despliegue/acceso-externo.md)) |
| Certificado autofirmado de 10 años en el origen | Solo lo ven `cloudflared` (sin verificarlo) y el acceso directo por la LAN, que muestra un aviso ([instalación](../despliegue/instalacion.md#2-arrancar-y-crear-el-certificado)) |
| Traps y agentes usan `192.168.0.191`, no `zabbix.likson.com` | El nombre apunta a Cloudflare, que solo lleva la web |
| Ajustes de rendimiento (caché de configuración 128M, 3 pingers, memoria de PostgreSQL) (2026-09-29) | Recomendaciones de Zabbix revisadas: caché al 73 % y pinger al 63 %. Detalle en [mantenimiento](../despliegue/mantenimiento.md#ajustes-de-rendimiento). Descartados por ahora: TimescaleDB (solo 90 valores/s), CSP estricta (puede romper la interfaz), `SameSite` en la cookie (Access ya protege) |
| Cámaras con esquema `SITIO-CAM-NN` (2026-10-02) | Las de Main Site son MAIN-CAM-01 a 05 (192.168.60.10 – .14, en orden de IP) y la de Cañadas, CANADAS-CAM-01. En las cámaras, el *Device name* aún es el de fábrica (`Torre`, `IP CAMERA`, `Camera 05`); conviene cambiarlo por el mismo nombre. La .13 (MAIN-CAM-04) transmite a 1280×720 |
| Sin MFA en Zabbix | Cloudflare Access ya exige un código enviado al correo autorizado antes del login de Zabbix. El acceso por la LAN no pasa por Access y queda protegido solo por la contraseña |

## Pendientes

| Pendiente | Qué hacer |
|---|---|
| **Actualizar a Zabbix 8.0 LTS antes del 2026-12-31** | Zabbix 7.4 deja de tener soporte (ni parches de seguridad) el 31-12-2026. El 2026-09-29, 8.0 LTS seguía en beta. Cuando salga la versión estable: leer las notas de actualización, respaldo, probar en una copia (restaurar el respaldo en otra máquina con `ZBX_IMAGE_TAG` de 8.0), y después en producción ([mantenimiento](../despliegue/mantenimiento.md)). Revisar también que las plantillas propias y los scripts de `agents/scripts/` funcionen con la API de 8.0 |
| Respaldos fuera del servidor | Copiarlos periódicamente ([mantenimiento](../despliegue/mantenimiento.md#copiar-los-respaldos-fuera-del-servidor)) |
| Token de API para agentes (caduca 2026-09-30) | Revocarlo al terminar la sesión de trabajo (*User settings → API tokens*) |
| Cable del Zabbix server a 100 Mbps | Ver *Situaciones conocidas* |
