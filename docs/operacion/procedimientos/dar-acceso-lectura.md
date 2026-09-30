# Dar acceso de solo lectura a una persona

> **Cuándo:** una persona necesita ver gráficas, dashboards, problemas y datos de los equipos, sin poder modificar nada.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web. El rol y el grupo **Solo lectura** ya existen ([configuración base](../../despliegue/configuracion-base.md#roles-y-grupos-de-usuarios)); si no, crearlos primero con el paso 0.

Qué puede hacer un usuario **Solo lectura**:

| Puede | No puede |
|---|---|
| Ver dashboards compartidos (*Likson NOC*), problemas, hosts, *Latest data* y gráficas, mapas, inventario e informes de disponibilidad | Entrar en *Data collection*, *Alerts*, *Users* ni *Administration* (el tipo de rol *User* no las tiene) |
| Ver todos los equipos de los grupos de hosts de Likson | Reconocer, cerrar, suprimir o comentar problemas, ni cambiar severidades |
| | Ejecutar scripts ni *Execute now*, crear o editar dashboards y mapas, usar la API ni crear tokens |

0. **Solo la primera vez, o si se perdió la BD:** crear el rol y el grupo.
   - *Users → User roles → Create user role*: nombre `Solo lectura`, **User type: User**. Dejar marcadas todas las secciones de la interfaz. En **Access to actions**, desmarcar todas, incluido *Default access to new actions*. En **Access to API**, desmarcar *Enabled*. **Add**.
   - *Users → User groups → Create user group*: nombre `Solo lectura`, *Frontend access: System default*, *Enabled*. Pestaña **Host permissions** → *Add*: los grupos de hosts de la tabla de [configuración base](../../despliegue/configuracion-base.md#roles-y-grupos-de-usuarios) con **Read**. **Add**.
   - *Dashboards* → *Likson NOC* → *Edit dashboard* → *Sharing*: *List of user group shares* → *Add* `Solo lectura`, permiso **Read-only**.
1. **Crear el usuario:** *Users → Users → Create user*.
   - Pestaña **User:**
     - *Username:* en minúsculas, por ejemplo `melb`, con nombre y apellidos.
     - *Groups:* `Solo lectura`.
     - *Password:* la introduce la persona responsable. No se envía por chat ni por correo junto con el usuario.
     - *Auto-logout:* `15m`.
   - Pestaña **Permissions:** *Role:* `Solo lectura`.
   - **Add**.
2. **Acceso desde Internet:** añadir su correo a la política `Personal NOC` de Cloudflare Access ([acceso externo](../../despliegue/acceso-externo.md#2-proteger-la-web-con-access)). En la LAN (`https://192.168.0.191`) no hace falta.
3. **Registrar** el usuario en la tabla de usuarios de la [configuración base](../../despliegue/configuracion-base.md#usuarios-users--users).
4. **Verificar** con el usuario nuevo:
   - El menú solo muestra *Dashboards*, *Monitoring*, *Services*, *Inventory* y *Reports*.
   - *Likson NOC* muestra datos.
   - En *Monitoring → Hosts* aparecen los equipos.
   - En *Monitoring → Problems*, el botón *Update* de un problema no permite ninguna acción.

**Quitar el acceso:** *Users → Users* → el usuario → *Groups*: añadir `Disabled` (o borrar el usuario), quitar su correo de la política de Access y actualizar la configuración base.

**Un grupo de hosts nuevo:** sus equipos no son visibles para *Solo lectura* hasta añadirlo al grupo de usuarios (y a `zabbix_access/solo_lectura.json`).

## Con scripts

```sh
S=agents/scripts/run_remote.sh
# Paso 0: rol, grupo y dashboard compartido, desde zabbix_access/solo_lectura.json
printf '%s\n' "$TOKEN" | $S -f zabbix_access/solo_lectura.json zbx_access_apply.py solo_lectura.json --dry-run
# Paso 1, tras crear el usuario en la interfaz (la contraseña no se pone por script)
printf '%s\n' "$TOKEN" | $S zbx_user_set.py --user melb --role "Solo lectura" --group "Solo lectura" --autologout 15m --dry-run
# Revisar roles, grupos, usuarios y dashboards compartidos
printf '%s\n' "$TOKEN" | $S zbx_users.py --dashboards
```
