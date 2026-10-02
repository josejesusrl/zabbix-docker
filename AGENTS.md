# AGENTS.md — Reglas para trabajar en este proyecto

Despliegue de producción de Zabbix 7.4 (Docker) para `zabbix.likson.com`, basado en el repositorio oficial `zabbix-docker`.
Estas reglas aplican a cualquier persona o agente (IA) que modifique el proyecto o el servidor de producción.

## Contexto

| Elemento | Valor |
|---|---|
| Servidor de producción | `jjrl@192.168.0.191` (Ubuntu 24.04), repositorio en `~/zabbix-docker` |
| Rama del despliegue | `server-deploy`. `7.4` se mantiene igual que la rama oficial |
| Stack | `docker-compose.yml` + `compose_server.yaml`, variables en `.env` + `server.env` |
| Comando base | `docker compose --env-file .env --env-file server.env <acción>` |
| Documentación (índice para personas y agentes) | [`docs/README.md`](docs/README.md) |
| Inventario y topología (qué hay y de quién depende) | [`docs/operacion/inventario.md`](docs/operacion/inventario.md) |
| Particularidades por tipo de equipo | [`docs/operacion/plantillas.md`](docs/operacion/plantillas.md#particularidades-por-tipo-de-equipo) |
| Decisiones, situaciones conocidas y pendientes | [`docs/operacion/registro.md`](docs/operacion/registro.md) |

## Checklist de sesión

Al empezar:
1. Leer este fichero y el [índice de la documentación](docs/README.md). Revisar el [registro](docs/operacion/registro.md) antes de "corregir" algo que parezca un error.
2. Pedir el token de la API a la persona (con caducidad) y no escribirlo en ningún fichero.

Antes de cada cambio en producción: respaldo de menos de 60 min (regla 1).

Al terminar:
1. Documentación actualizada en el mismo commit que el cambio (regla 7): inventario, plantillas, procedimientos, configuración base o registro según corresponda.
2. `python3 agents/scripts/docs_check.py` sin errores (y `--zabbix` si cambiaron hosts, regla 7).
3. Commit de `agents/scripts/` y del resto (reglas 3 y 8), push y, con respaldo, `git pull` en el servidor.
4. Recordar a la persona que revoque el token.

## Regla 1 — Respaldo antes de modificar producción

**Antes de cualquier cambio en el Zabbix de producción se crea un respaldo nuevo.** Se considera cambio:

- Escrituras por la API o la interfaz web: hosts, plantillas, macros, acciones, usuarios, ajustes.
- Importar o actualizar plantillas.
- `git pull` en el servidor, `up`, `pull`, recrear o reiniciar contenedores, o cambiar `server.env` o `env_vars/`.
- Actualizar la versión de Zabbix o de PostgreSQL.

Las consultas de solo lectura (API `*.get`, logs, `ps`) no requieren respaldo.

Procedimiento:

1. En el servidor, ejecutar `sudo ./server_backup.sh`. Requiere sudo, así que un agente sin la contraseña se lo pide a la persona.
2. Verificar que existe un respaldo de los últimos 60 minutos antes de continuar:
   ```sh
   find ~/zabbix-docker/backups -name 'zabbix-db-*.dump' -mmin -60 -size +1M | grep -q . && echo "respaldo reciente OK"
   ```
3. Si no hay respaldo reciente, **no se hace el cambio**.

Los respaldos se deben copiar fuera del servidor. Una copia local no protege si falla el disco.

## Regla 2 — Lo que no está en la base de datos vive en el repositorio

El respaldo de la base de datos (`pg_dump`) contiene hosts, plantillas importadas, macros, acciones, usuarios, medios, historial y tendencias.
**Todo lo demás debe estar en este repositorio** (o poder regenerarse desde él), para reconstruir el servidor completo si falla el disco o la máquina.

| Qué | Dónde | Cómo se restaura |
|---|---|---|
| Definición del stack | `docker-compose.yml`, `compose_server.yaml`, `server.env.example` | `git clone` |
| Variables de Zabbix | `env_vars/.env_*_override` | `git clone` |
| Configuración de Nginx (HTTP → HTTPS) | `nginx/zabbix_http.conf` | `git clone` |
| UserParameters del Agent 2 (temperaturas) | `zabbix_agentd.d/` | `git clone` |
| Plantillas propias | `zabbix_templates/*.yaml` | Están también en la BD; si la BD se pierde, se importan desde aquí |
| Scripts de alertas y externos | `alertscripts/`, `externalscripts/` | `git clone` |
| Configuración que solo está en la BD (medios, acciones, usuarios, ajustes) | Documentada en [`docs/despliegue/configuracion-base.md`](docs/despliegue/configuracion-base.md) (sin secretos) | Respaldo de la BD; si se pierde, a mano según ese documento |
| Preparación del host: directorios, cron, lm-sensors | `server_setup.sh` | `./server_setup.sh` |
| Respaldo, restauración y certificado | `server_backup.sh`, `server_restore.sh`, `server_certificate.sh` | `git clone` |
| Túnel de Cloudflare, ruta pública y Access | Panel de Cloudflare Zero Trust, documentado en [`docs/despliegue/acceso-externo.md`](docs/despliegue/acceso-externo.md). El conector está en `compose_server.yaml` | Ya está en Cloudflare; si se pierde, a mano según ese documento |
| Scripts de agentes para la API | `agents/scripts/` | `git clone` |
| Perfiles de acceso (rol, grupo de usuarios, dashboards compartidos) | `zabbix_access/*.json` | Están también en la BD; si se pierde, `zbx_access_apply.py` |
| Mapas de red (se generan desde las dependencias) | `zabbix_maps/*.json` | Están también en la BD; si se pierde, `zbx_map_apply.py` |
| Dashboards | `zabbix_dashboards/*.json` (por nombres) | Están también en la BD; si se pierde, `zbx_dashboard_apply.py` |
| Script y plantillas de mensajes de los medios (Telegram…) y mensajes de la escalada | `zabbix_media/` (sin tokens: el token del bot está solo en la BD) | Están también en la BD; si se pierde, `zbx_mediatype_update.py` y `zbx_action_operations.py` desde aquí |
| **Secretos**: contraseña de PostgreSQL, token del túnel (`env_vars/.CLOUDFLARE_TUNNEL_TOKEN`), comunidad de traps, `server.env` | **Nunca en git.** En el archivo `zabbix-config-*.tar.gz` del respaldo | `server_restore.sh` o `server_setup.sh` |
| Certificado TLS autofirmado del origen y `dhparam` | `zbx_env/etc/ssl/nginx` (en el respaldo) | `server_restore.sh` o `server_certificate.sh selfsigned` |
| MIBs de fabricantes | `zbx_env/var/lib/zabbix/mibs` (en el respaldo) | `server_restore.sh` |

Al añadir cualquier configuración nueva fuera de la base de datos (un script, un MIB, un fichero montado en un contenedor, una tarea de cron, un paquete del host):

1. Añadirla al repositorio. Si es un secreto, añadir la ruta a `server_backup.sh` y a `server_restore.sh`.
2. Actualizar la tabla anterior y [la guía de instalación](docs/despliegue/instalacion.md).
3. Si hace falta en el host, que `server_setup.sh` la instale de forma idempotente.

## Regla 3 — Flujo de cambios

1. Editar en la copia local, hacer commit en `server-deploy` y hacer push.
2. En el servidor: respaldo (regla 1) → `git pull` → aplicar (`up -d`, importar la plantilla…).
3. **No editar ficheros versionados directamente en el servidor.** `git status` en el servidor debe quedar limpio. Las rutas locales están excluidas en `.git/info/exclude`, y `env_vars/.POSTGRES_PASSWORD` está marcada con `skip-worktree`.
4. Las actualizaciones oficiales se incorporan uniendo `7.4` en `server-deploy`, nunca editando los ficheros originales de Zabbix. Las personalizaciones van en overrides (`compose_server.yaml`, `*_override`).
5. Cada commit termina con las líneas de atribución que correspondan.

## Regla 4 — Secretos

- No imprimir ni escribir en la conversación, en los logs ni en commits: contraseñas, comunidades SNMP, tokens de la API ni claves privadas.
- El token de la API se pasa al script por la entrada estándar y en una llamada SSH aparte: los `docker compose exec` consumen la entrada estándar.
- Para probar SNMP, la comunidad se lee de Zabbix (`{$SNMP_COMMUNITY}`) dentro del script y se pasa por variable de entorno, sin mostrarla.
- Los secretos nuevos los introduce la persona: con `server_setup.sh` (entrada oculta) o en la interfaz como macro de tipo *Secret text*.
- Los tokens de la API deben tener fecha de caducidad y revocarse al terminar cada sesión de trabajo.

## Regla 5 — Límites de actuación

- No ejecutar Docker en el equipo local. Los comandos de Docker se ejecutan solo en el servidor.
- No escanear la red. Se pide la IP del equipo y solo se consulta ese objetivo.
- No borrar contenedores, volúmenes, datos ni hosts de Zabbix sin confirmación explícita.
- Si aparece un estado inesperado (restos de otra instalación, cambios que no son propios), se informa y se pregunta antes de actuar.

## Regla 6 — Plantillas y configuración de Zabbix

- Las plantillas propias se guardan en `zabbix_templates/` y se importan por la API (`configuration.import`) o la interfaz.
- UUID en formato **v4**. El nombre técnico, sin paréntesis (el nombre visible sí puede llevarlos).
- Los triggers de items normales van en la sección `triggers` de primer nivel del export. Los de prototipos van dentro del prototipo.
- En `opdata` y `event_name` de una plantilla, las macros de expresión usan `/{HOST.HOST}/clave`.
- Los ajustes de host hechos por la API (macros, dependencias, items desactivados) quedan en la base de datos. Si son un patrón repetible, se documentan en el procedimiento correspondiente de [`docs/operacion/procedimientos/`](docs/operacion/procedimientos/).
- Cada equipo nuevo se da de alta con su dependencia topológica (quién le da conectividad). Las dependencias se **añaden** a las que ya existen, nunca se sustituyen: las plantillas oficiales traen dependencias internas (pérdida, latencia y SNMP dependen del ping del propio host) que evitan alertas duplicadas.

Las particularidades ya conocidas de cada tipo de equipo están en [plantillas](docs/operacion/plantillas.md#particularidades-por-tipo-de-equipo). **Leerlas antes de dar de alta un equipo.**

## Regla 7 — Documentar para que una persona pueda hacerlo

Todo lo que se configure o se haga en el proyecto debe poder repetirlo una persona sin ayuda y sin la API. La documentación está en [`docs/`](docs/README.md); su **índice** tiene tres entradas: por necesidad, *Busco…* (tema → documento) y mapa completo.

| Documento | Contenido |
|---|---|
| `docs/despliegue/` | Instalar, configurar el host Zabbix server, acceso externo, restaurar, migrar, mantener y actualizar el **servidor**, y la configuración que vive solo en la BD |
| `docs/operacion/inventario.md` | Convenciones, topología e inventario de hosts (tabla generada con `zbx_inventory.py --markdown`) |
| `docs/operacion/plantillas.md` | Catálogo de plantillas (propias y oficiales) y particularidades por tipo de equipo |
| `docs/operacion/plantillas/` | **Una ficha por plantilla propia**: items, triggers, macros y requisitos |
| `docs/operacion/alertas.md`, `dashboard.md`, `mapas.md` | Notificaciones, dashboard y mapas de red |
| `docs/operacion/procedimientos/` | Un fichero por procedimiento |
| `docs/operacion/solucion-de-problemas.md` | Síntomas y soluciones |
| `docs/operacion/registro.md` | Objetos desactivados, situaciones conocidas, decisiones y pendientes |

Cada procedimiento indica:

1. **Cuándo** se usa y los requisitos previos (incluido el respaldo, regla 1).
2. Los **pasos en la interfaz web** de Zabbix y en el equipo (airOS, RouterOS…), con los menús exactos. La API es opcional (sección *Con scripts*); la interfaz es obligatoria.
3. Qué **plantillas, macros, dependencias y etiquetas** aplicar y por qué.
4. Cómo **verificar** que funciona.

Cualquier cambio que añada o modifique una plantilla, un trigger, una macro, un tipo de equipo, una dependencia, un procedimiento o la configuración base se documenta **en el mismo commit**.

**Documentos cortos y atómicos:** una tarea repetible es un procedimiento propio, y una plantilla propia tiene su ficha. Los documentos de referencia (alertas, mantenimiento, plantillas) enlazan a ellos en vez de repetir pasos. Todo documento nuevo se enlaza desde el índice [`docs/README.md`](docs/README.md), en su tabla por necesidad y en *Busco…*. Al dar de alta, mover o retirar equipos se regenera el inventario. Los enlaces entre documentos son relativos; `python3 agents/scripts/docs_check.py` comprueba enlaces y anclas, que cada plantilla tenga su ficha, que cada script esté en el catálogo y que todos los documentos estén en el índice, y con `--zabbix` que el inventario coincide con Zabbix.

## Regla 8 — Scripts reutilizables para la API

Los scripts que se usan para consultar o modificar Zabbix por la API **no se escriben de un solo uso**. Se guardan en **`agents/scripts/`** para reutilizarlos. Guía y catálogo: `agents/scripts/README.md`.

1. **Antes de escribir un script, se busca en `agents/scripts/`** uno que ya lo haga, o una función de `zbx_api.py` que se pueda reutilizar o ampliar.
2. **Genéricos:** todo lo variable (hosts, grupos, IPs, plantillas, macros, umbrales) llega por argumentos. Nada de valores de producción fijos en el código.
3. **SOLID, KISS y DRY:**
   - Un script, una responsabilidad.
   - La lógica común (cliente de la API, búsquedas, reglas de dependencias, macros, etiquetas, importación) vive solo en `zbx_api.py`.
   - Solución lo más simple posible, sin dependencias fuera de la biblioteca estándar de Python.
4. **Documentados:** docstring con propósito y uso (visible con `--help`) y una fila en la tabla del README.
5. **Seguros:**
   - El token se pasa por la entrada estándar con `run_remote.sh` (regla 4).
   - Los scripts que escriben tienen `--dry-run` y exigen el respaldo previo (regla 1).
   - Ninguno imprime secretos.
6. **Validados** con `python3 -m py_compile` y una ejecución de solo lectura o `--dry-run` antes de usarlos en producción.
7. **Commits:** los cambios en `agents/scripts/` no necesitan un commit por script. Se agrupan en un commit **al final de la sesión de trabajo**, antes de terminarla. El resto de cambios siguen la regla 3.

Las tareas únicas que no justifican un script (una consulta de diagnóstico puntual) pueden hacerse con un script temporal, que se borra al terminar. Si una tarea se repite, se convierte en script de `agents/scripts/`.

## Regla 9 — Verificación

Después de cada cambio se comprueba el resultado real. No basta con que el comando haya terminado sin error:

- `docker compose … ps`: todos los servicios en `running`/`healthy` y `server-db-init` en `exited (0)`.
- En la API: disponibilidad de las interfaces, items no soportados inesperados y problemas activos nuevos.
- Se informa con honestidad de lo que no se pudo verificar.
