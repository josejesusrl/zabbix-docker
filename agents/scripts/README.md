# Scripts de agentes para la API de Zabbix

Herramientas reutilizables para consultar y modificar el Zabbix de producción por la API. Las usan los agentes de IA (y cualquier persona) en lugar de escribir scripts de un solo uso. Las reglas de uso están en `AGENTS.md` (regla 8).

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
| `zbx_inventory.py` | Lectura | Inventario de hosts: interfaces, grupos, plantillas, macros, etiquetas y de quién depende. `--markdown` genera la tabla para `OPERACION.md`; `--dependencies` muestra las dependencias de cada trigger de disponibilidad |
| `zbx_host_status.py` | Lectura | Estado tras un cambio: disponibilidad, items sin datos o no soportados (separa las limitaciones conocidas) y problemas |
| `snmp_probe.py` | Lectura | Sondeo previo al alta: ping, SNMPv1/v2c, `sysName`, modelo/firmware airOS 6, clientes y GPS Ubiquiti |
| `snmp_walk.py` | Lectura | Recorrido SNMP de un equipo para ver qué OIDs publica antes de diseñar una plantilla (`--hide` oculta valores sensibles) |
| `snmp_tools.py` | Librería | Ejecuta net-snmp en un contenedor temporal con la comunidad de Zabbix sin mostrarla (usada por `snmp_probe` y `snmp_walk`) |
| `zbx_latest.py` | Lectura | Últimos valores de los items (como *Latest data*), filtrados por clave o nombre |
| `zbx_create_snmp_host.py` | Escritura | Alta de un host SNMP con plantillas, macros, etiquetas y dependencia de su uplink (`--visible-name` si el nombre del equipo tiene caracteres no válidos para el *Host name*) |
| `zbx_set_uplink.py` | Escritura | Cambia el equipo padre (dependencias + etiqueta `uplink`), conservando las dependencias internas de la plantilla |
| `zbx_import_template.py` | Escritura | Importa plantillas YAML (`--delete-missing` para eliminar lo que ya no está en el fichero) |
| `zbx_check_now.py` | Acción | Ejecuta ya los items y reglas de descubrimiento de unos hosts |
| `zbx_events.py` | Lectura | Eventos de problema de las últimas horas agrupados por trigger: veces abierto, notificaciones, cierres manuales. Detecta falsos positivos y *flapping* |
| `zbx_add_dependency.py` | Escritura | Añade una dependencia a cualquier trigger (p. ej. equipos raíz → enlace de red del Zabbix server), conservando las existentes |
| `zbx_set_status.py` | Escritura | Activa o desactiva items o triggers por nombre (registrar el motivo en `OPERACION.md`, sección 6) |
| `zbx_close_problems.py` | Escritura | Cierra problemas abiertos por nombre con un comentario (falsos positivos, problemas de objetos desactivados) |
| `run_remote.sh` | Envoltorio | Ejecuta un script en el servidor con el token por la entrada estándar |

Selección de hosts común (`zbx_inventory`, `zbx_host_status`, `zbx_set_uplink`, `zbx_check_now`): `--host NOMBRE ...`, `--group GRUPO` o `--tag uplink=EQUIPO`.

## Ejemplos

```sh
S=agents/scripts/run_remote.sh
# Estado de todos los APs
printf '%s\n' "$TOKEN" | $S zbx_host_status.py --group "Access Points PPPoE Clients"
# Inventario en Markdown para OPERACION.md
printf '%s\n' "$TOKEN" | $S zbx_inventory.py --markdown
# Sondear APs antes de darlos de alta (solo las IPs indicadas por el propietario)
printf '%s\n' "$TOKEN" | $S snmp_probe.py 172.16.1.20 172.16.1.21
# Alta de un AP airOS 8 sin GPS que cuelga del switch (primero con --dry-run)
printf '%s\n' "$TOKEN" | $S zbx_create_snmp_host.py --name LIKSON_PDV_11 --ip 172.16.1.20 \
    --group "Access Points PPPoE Clients" --snmp-version 1 \
    --template "Ubiquiti AirOS by SNMP" "Ubiquiti AirOS 8 wireless by SNMPv1" \
    --macro '{$UBNT.GPS.SATS.MIN}=0' --uplink "Switch Main Site #01" \
    --self-dependency "no connected clients" --dry-run
# Cambiar de padre a todos los hosts con una etiqueta
printf '%s\n' "$TOKEN" | $S zbx_set_uplink.py --tag "uplink=EDGE 01" --parent "Switch Main Site #01" --dry-run
# Ver qué publica un equipo nuevo en su MIB de fabricante
printf '%s\n' "$TOKEN" | $S snmp_walk.py 10.100.0.2 1.3.6.1.4.1.43356 --max-lines 200
# Últimos valores de un host (verificación tras el alta)
printf '%s\n' "$TOKEN" | $S zbx_latest.py --host AP-Lk_Trunk_01_A --key mimosa.
# Actualizar una plantilla propia
printf '%s\n' "$TOKEN" | $S -f zabbix_templates/switch_port_changes.yaml zbx_import_template.py switch_port_changes.yaml --delete-missing
```

## Cómo añadir o modificar scripts

- **Genéricos:** parámetros por argumentos, nada de nombres de hosts, IPs ni valores fijos en el código. Si algo se repite dos veces, va a `zbx_api.py`.
- **SOLID / KISS / DRY:** un script = una tarea. Las funciones compartidas, en la librería. Sin dependencias fuera de la biblioteca estándar de Python.
- **Documentados:** docstring del módulo con propósito y uso (se muestra con `--help`), y una fila en la tabla de este README.
- **Seguros:** los que escriben tienen `--dry-run` y nunca imprimen secretos. Las comprobaciones de secretos (comunidades) se hacen dentro del script sin mostrarlos.
- Se validan antes de usarlos: `python3 -m py_compile agents/scripts/*.py` y una ejecución con `--dry-run` o de solo lectura.
