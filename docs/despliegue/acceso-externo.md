# Acceso externo: Cloudflare Tunnel y Access

> **Cuándo:** al instalar el servidor, al migrarlo, al dar acceso a una persona nueva o si la web no carga desde Internet.
> **Requisitos:** dominio `likson.com` en Cloudflare, acceso al panel de Cloudflare Zero Trust y respaldo reciente antes de tocar el servidor ([AGENTS.md](../../AGENTS.md), regla 1).

La web de Zabbix se publica en `https://zabbix.likson.com` **sin abrir puertos en el router**. El contenedor `cloudflared` (`compose_server.yaml`) abre conexiones salientes hacia Cloudflare, y Cloudflare entrega por ellas las peticiones al contenedor web por la red interna de Docker. Antes de llegar al login de Zabbix, **Cloudflare Access** pide el correo de la persona y le envía un código.

```
Navegador ──HTTPS──▶ Cloudflare (certificado válido, Access) ◀──túnel saliente── cloudflared ──▶ zabbix-web-nginx-pgsql:8443
LAN ──https://192.168.0.191──▶ zabbix-web-nginx-pgsql (certificado autofirmado, sin Access)
```

| Qué | Dónde vive | Cómo se recupera |
|---|---|---|
| Túnel, ruta pública y aplicación de Access | Panel de Cloudflare (este documento) | Ya está en Cloudflare; si se borra, se rehace con estos pasos |
| Token del túnel | `env_vars/.CLOUDFLARE_TUNNEL_TOKEN` en el servidor (nunca en git, sí en el respaldo) | `server_restore.sh --config` o volver a copiarlo del panel |
| Contenedor `cloudflared` y su versión | `compose_server.yaml`, `CLOUDFLARED_IMAGE_TAG` en `server.env` | `git clone` |

Solo pasa la web. Los traps (`162/udp`) y los agentes (`10051/tcp`) siguen llegando por la LAN a `192.168.0.191`. Para esos servicios **no** se usa `zabbix.likson.com`, que ahora apunta a Cloudflare.

## 1. Crear el túnel

En el panel de Cloudflare → *Zero Trust*:

1. *Networks → Tunnels* (en el panel nuevo, *Networks → Connectors → Cloudflare Tunnels*) → *Create a tunnel*.
2. Tipo **Cloudflared**, nombre `zabbix-likson`.
3. En *Install and run connectors*, elegir **Docker** y copiar **solo el token**, la cadena larga que va detrás de `--token`. No ejecutar el comando que muestra el panel: el conector ya está en `compose_server.yaml`.
4. **Aún no** añadir la ruta pública. Primero se crea la aplicación de Access (sección 2), para que la web no quede expuesta sin protección ni un momento.

En el servidor, el token lo introduce la persona, sin que se muestre:

```sh
cd ~/zabbix-docker
./server_setup.sh     # pide "Cloudflare Tunnel token" solo si falta env_vars/.CLOUDFLARE_TUNNEL_TOKEN
zbx up -d cloudflared
zbx logs cloudflared  # debe mostrar 4 líneas "Registered tunnel connection"
```

En el panel, el túnel pasa a **Healthy**.

## 2. Proteger la web con Access

*Zero Trust → Access → Applications* (en el panel nuevo, *Access controls → Applications*) → *Add an application* → **Self-hosted**:

1. **Application name:** `Zabbix Likson`. **Session duration:** `24 hours`.
2. **Public hostname:** subdominio `zabbix`, dominio `likson.com`, sin ruta.
3. **Policy** → *Add a policy*: nombre `Personal NOC`, **Action: Allow**, regla **Include → Emails** con los correos autorizados, uno por línea.
4. **Login methods:** **One-time PIN**, que viene activado por defecto: Cloudflare envía un código al correo. Se puede añadir Google en *Settings → Authentication*.
5. Guardar.

Dar de alta o de baja a una persona: editar la política `Personal NOC` y añadir o quitar su correo. Además, necesita su usuario de Zabbix ([configuración base](configuracion-base.md)).

## 3. Publicar la ruta del túnel

En el túnel `zabbix-likson` → *Public Hostname* (en el panel nuevo, *Published application routes*) → *Add*:

| Campo | Valor |
|---|---|
| Subdomain / Domain | `zabbix` / `likson.com` |
| Path | vacío |
| Service | `HTTPS` → `zabbix-web-nginx-pgsql:8443` |
| *Additional application settings → TLS → No TLS Verify* | **On**. El salto va dentro de la red Docker del mismo host y el origen tiene el certificado autofirmado |

Cloudflare crea o sustituye el registro DNS `zabbix.likson.com` por un CNAME al túnel, con proxy (nube naranja). Si ya había un registro A, el panel pide confirmar que se reemplace.

## 4. Verificar

- `zbx ps`: `cloudflared` en `healthy`.
- Desde fuera de la LAN (datos móviles), `https://zabbix.likson.com` muestra la pantalla de Cloudflare Access. Tras poner el código llega al login de Zabbix, con un certificado válido.
- Un correo que no está en la política no recibe el código ni puede entrar.
- `https://192.168.0.191` en la LAN sigue funcionando, con aviso de certificado. Es el acceso de emergencia si cae Internet o Cloudflare.
- En Zabbix, host *Zabbix server* → *Latest data*: `Cloudflared: Tunnel connections` = 4 ([plantilla](../operacion/plantillas.md#cloudflare-tunnel-by-http--cloudflared_tunnelyaml)).
- En el router, **ninguna** redirección de los puertos 80 ni 443 hacia el servidor.

## Rotar el token o mover el túnel a otro servidor

- **Rotar el token** (si se ha expuesto): en el túnel, renovar el token desde el panel. En el servidor, borrar `env_vars/.CLOUDFLARE_TUNNEL_TOKEN` (con `sudo`, el propietario es el usuario del contenedor), ejecutar `./server_setup.sh` para introducir el nuevo y después `zbx up -d --force-recreate cloudflared`.
- **Migrar el servidor:** el token restaurado conecta el túnel desde el servidor nuevo. **Parar antes `cloudflared` en el viejo** (`zbx stop cloudflared`). Si no, Cloudflare reparte las peticiones entre los dos.

## Limitaciones

- Access se aplica a todo el dominio, incluida la API (`/api_jsonrpc.php`). Los scripts de `agents/scripts` no se ven afectados porque usan la API desde el propio servidor (`https://localhost`). Una integración externa que necesite la API pública requerirá un *service token* de Access.
- El log de auditoría de Zabbix registra la IP de `cloudflared`, no la del usuario. La identidad real queda en *Zero Trust → Logs → Access*.
