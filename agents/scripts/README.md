# Scripts de agentes para la API de Zabbix

Herramientas reutilizables para consultar y modificar el Zabbix de producción por la API. Las usan los agentes de IA (y cualquier persona) en lugar de escribir scripts de un solo uso. Las reglas de uso están en [AGENTS.md](../../AGENTS.md) (regla 8).

## Cómo se ejecutan

Los scripts se ejecutan **en el servidor**, donde la API está en `https://localhost`, pero se lanzan desde la copia local con `run_remote.sh`. Este copia el directorio a una carpeta temporal privada del servidor, ejecuta el script y la borra al terminar.

```sh
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh SCRIPT [ARGS...]
printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh -f zabbix_templates/X.yaml zbx_import_template.py X.yaml
```

- **Token:** siempre por la entrada estándar (primera línea). Nunca como argumento, variable de entorno ni fichero. El token debe tener caducidad (*User settings → API tokens*) y revocarse al terminar la sesión.
- `-f FICHERO`: sube además ese fichero, por ejemplo una plantilla. En los argumentos se usa su nombre base.
- `ZBX_SSH=usuario@host` cambia el servidor (por defecto `jjrl@192.168.0.191`).
- Requisitos en el servidor: `python3`. `snmp_probe.py` necesita además Docker.
- **Scripts que escriben** (crear hosts, dependencias, importar): requieren un **respaldo de menos de 60 min** (`AGENTS.md`, regla 1). Todos aceptan `--dry-run` para ver qué harían sin cambiar nada.

## Scripts

| Script | Tipo | Para qué |
|---|---|---|
| `zbx_api.py` | Librería | Cliente de la API y funciones compartidas (búsquedas, dependencias, macros, etiquetas, importación) |
| `zbx_inventory.py` | Lectura | Inventario de hosts: interfaces, grupos, plantillas, macros, etiquetas y de quién depende. `--markdown` genera las tablas de [inventario](../../docs/operacion/inventario.md); `--dependencies` muestra las dependencias de cada trigger de disponibilidad |
| `zbx_host_status.py` | Lectura | Estado tras un cambio: disponibilidad, items sin datos o no soportados (separa las limitaciones conocidas) y problemas |
| `snmp_probe.py` | Lectura | Sondeo previo al alta: ping, SNMPv1/v2c, `sysName`, modelo/firmware airOS 6, clientes y GPS Ubiquiti |
| `snmp_walk.py` | Lectura | Recorrido SNMP de un equipo para ver qué OIDs publica antes de diseñar una plantilla (`--hide` oculta valores sensibles) |
| `snmp_tools.py` | Librería | Ejecuta net-snmp en un contenedor temporal con la comunidad de Zabbix sin mostrarla (usada por `snmp_probe` y `snmp_walk`) |
| `zbx_latest.py` | Lectura | Últimos valores de los items (como *Latest data*), filtrados por clave o nombre |
| `zbx_add_interface.py` | Escritura | Añade una interfaz a un host que no la tiene: `ping` (tipo *Agent*, para *ICMP Ping* en equipos sin SNMP) o `snmp` |
| `zbx_set_macro.py` | Escritura | Crea o cambia macros de host con valores no secretos (rechaza nombres de secretos: esos van en la interfaz como *Secret text*) |
| `zbx_set_tag.py` | Escritura | Pone o quita una etiqueta de host (`notificar=no`, `escalation=off`…) conservando las demás |
| `zbx_create_snmp_host.py` | Escritura | Alta de un host SNMP (o solo ping con `--interface ping`, p. ej. cámaras Hikvision) con plantillas, macros, etiquetas y dependencia de su uplink (`--visible-name` si el nombre del equipo tiene caracteres no válidos para el *Host name*) |
| `zbx_align_host_name.py` | Escritura | Pone el *Host name* técnico igual al visible (sin caracteres no válidos), conservando el *Visible name*. Para hosts dados de alta con la IP como *Host name* |
| `zbx_set_uplink.py` | Escritura | Cambia el equipo padre (dependencias + etiqueta `uplink`), conservando las dependencias internas de la plantilla |
| `zbx_import_template.py` | Escritura | Importa plantillas YAML (`--delete-missing` para eliminar lo que ya no está en el fichero). Comprueba que se crearon todos los triggers: Zabbix descarta sin error los que tienen una expresión no válida |
| `zbx_link_template.py` | Escritura | Enlaza plantillas a hosts (`host.massadd`), conservando las que ya tienen |
| `zbx_check_now.py` | Acción | Ejecuta ya los items y reglas de descubrimiento de unos hosts |
| `zbx_events.py` | Lectura | Eventos de problema de las últimas horas agrupados por trigger: veces abierto, notificaciones, cierres manuales. Detecta falsos positivos y *flapping* |
| `zbx_add_dependency.py` | Escritura | Añade una dependencia a cualquier trigger (p. ej. equipos raíz → enlace de red del Zabbix server), conservando las existentes |
| `zbx_set_status.py` | Escritura | Activa o desactiva items o triggers por nombre (registrar el motivo en el [registro](../../docs/operacion/registro.md)) |
| `zbx_mediatype_update.py` | Escritura | Aplica a un medio el script, las plantillas y parámetros concretos desde `zabbix_media/`, sin tocar ni mostrar el token |
| `zbx_action_operations.py` | Escritura | Reemplaza las operaciones de mensaje de una acción desde un JSON (p. ej. los recordatorios de la escalada en `zabbix_media/escalation.json`), con un mensaje propio por medio |
| `zbx_test_notification.py` | Escritura | Prueba real de extremo a extremo: host temporal que abre, actualiza y resuelve un problema, muestra el estado de entrega de cada notificación y se borra |
| `zbx_dashboard_apply.py` | Escritura | Crea o actualiza un dashboard desde `zabbix_dashboards/*.json` (hosts, grupos e items por nombre) |
| `zbx_users.py` | Lectura | Roles (UI, acciones, API), grupos de usuarios con permisos por grupo de hosts, usuarios y, con `--dashboards`, con quién se comparte cada dashboard |
| `zbx_access_apply.py` | Escritura | Crea o actualiza un perfil de acceso desde `zabbix_access/*.json`: rol de tipo *User*, grupo de usuarios con lectura en grupos de hosts y dashboards compartidos |
| `zbx_user_set.py` | Escritura | Asigna a un usuario su rol, añade grupos (conserva los que tiene) y auto-logout. No toca contraseñas |
| `zbx_map_apply.py` | Escritura | Genera o actualiza los mapas de red (general y un submapa por sitio) desde las dependencias, según `zabbix_maps/*.json` ([mapas](../../docs/operacion/mapas.md)) |
| `zbx_close_problems.py` | Escritura | Cierra problemas abiertos por nombre con un comentario (falsos positivos, problemas de objetos desactivados) |
| `docs_check.py` | Local | Comprueba la documentación: enlaces relativos y anclas, referencias a documentos antiguos, plantillas y scripts documentados. `--zabbix` (en el servidor, con token) compara el inventario con los hosts de Zabbix |
| `run_remote.sh` | Envoltorio | Ejecuta un script en el servidor con el token por la entrada estándar |

Selección de hosts común (`zbx_inventory`, `zbx_host_status`, `zbx_set_uplink`, `zbx_check_now`): `--host NOMBRE ...`, `--group GRUPO` o `--tag uplink=EQUIPO`.

## Ejemplos

```sh
S=agents/scripts/run_remote.sh
# Estado de todos los APs
printf '%s\n' "$TOKEN" | $S zbx_host_status.py --group "Access Points PPPoE Clients"
# Inventario en Markdown para docs/operacion/inventario.md
printf '%s\n' "$TOKEN" | $S zbx_inventory.py --markdown
# Sondear APs antes de darlos de alta (solo las IPs indicadas por el propietario)
printf '%s\n' "$TOKEN" | $S snmp_probe.py 172.16.1.20 172.16.1.21
# Alta de un AP airOS 8 sin GPS que cuelga del switch (primero con --dry-run)
printf '%s\n' "$TOKEN" | $S zbx_create_snmp_host.py --name LIKSON_PDV_11 --ip 172.16.1.20 \
    --group "Access Points PPPoE Clients" --snmp-version 1 \
    --template "Ubiquiti AirOS by SNMP" "Ubiquiti AirOS 8 wireless by SNMPv1" \
    --macro '{$UBNT.GPS.SATS.MIN}=0' --uplink MAIN-SW-01 \
    --self-dependency "no connected clients" --dry-run
# Cambiar de padre a todos los hosts con una etiqueta
printf '%s\n' "$TOKEN" | $S zbx_set_uplink.py --tag "uplink=EDGE 01" --parent MAIN-SW-01 --dry-run
# Ver qué publica un equipo nuevo en su MIB de fabricante
printf '%s\n' "$TOKEN" | $S snmp_walk.py 10.100.0.2 1.3.6.1.4.1.43356 --max-lines 200
# Últimos valores de un host (verificación tras el alta)
printf '%s\n' "$TOKEN" | $S zbx_latest.py --host AP-Lk_Trunk_01_A --key mimosa.
# Aplicar el script y las plantillas de Telegram, y probar
printf '%s\n' "$TOKEN" | $S -f zabbix_media/telegram/telegram.js -f zabbix_media/telegram/message_templates.json \
    zbx_mediatype_update.py --name Telegram --script telegram.js --templates message_templates.json --param api_parse_mode=html
printf '%s\n' "$TOKEN" | $S zbx_test_notification.py
# Enlazar una plantilla a un host
printf '%s\n' "$TOKEN" | $S zbx_link_template.py --host "Zabbix server" --template "Cloudflare Tunnel by HTTP" --dry-run
# Actualizar una plantilla propia
printf '%s\n' "$TOKEN" | $S -f zabbix_templates/switch_port_changes.yaml zbx_import_template.py switch_port_changes.yaml --delete-missing
```

## Cómo añadir o modificar scripts

- **Genéricos:** parámetros por argumentos, nada de nombres de hosts, IPs ni valores fijos en el código. Si algo se repite dos veces, va a `zbx_api.py`.
- **SOLID / KISS / DRY:** un script = una tarea. Las funciones compartidas, en la librería. Sin dependencias fuera de la biblioteca estándar de Python.
- **Documentados:** docstring del módulo con propósito y uso (se muestra con `--help`), y una fila en la tabla de este README.
- **Seguros:** los que escriben tienen `--dry-run` y nunca imprimen secretos. Las comprobaciones de secretos (comunidades) se hacen dentro del script sin mostrarlos.
- Se validan antes de usarlos: `python3 -m py_compile agents/scripts/*.py` y una ejecución con `--dry-run` o de solo lectura.
