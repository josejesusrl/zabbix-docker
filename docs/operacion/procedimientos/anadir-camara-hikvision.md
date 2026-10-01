# Añadir una cámara o un NVR Hikvision

> **Cuándo:** al monitorear una cámara IP o un NVR Hikvision.
> **Requisitos:**
> - Respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.
> - IP del equipo, usuario y contraseña de su web (ISAPI), y saber de qué equipo depende (el NVR si va a sus puertos PoE, o el router o switch que le da conectividad).

Las cámaras Hikvision no tienen SNMP activado. Se monitorean con dos plantillas oficiales:

| Plantilla | Qué aporta |
|---|---|
| *Hikvision camera by HTTP* | Lee la API ISAPI de la cámara por HTTP: nombre, modelo, firmware, CPU, memoria, reinicios y estado de cada canal de vídeo. Necesita usuario y contraseña |
| *ICMP Ping* | Disponibilidad (*Unavailable by ICMP ping*), pérdida y latencia. Es el trigger que usan las dependencias y los [mapas](../mapas.md) |

## 1. En la cámara o el NVR

1. Asignar IP fija dentro de `192.168.60.0/28`, la red de CCTV de EDGE 01, o la red del sitio.
2. *Configuración → Sistema → Configuración del sistema → Información básica → Nombre del dispositivo*: el nombre definitivo, con la convención `CAM NN <ubicación>` (p. ej. `CAM 05 Canadas del bosque`) o `NVR NN`. Es el que se usa en Zabbix.
3. Usar un usuario con permiso de lectura de configuración. Por defecto, `admin`.

## 2. En Zabbix

*Data collection → Hosts → Create host*:

1. **Host name:** el nombre del dispositivo, solo con letras, dígitos, espacios, `.`, `-` y `_` ([convenciones](../inventario.md#convenciones)). *Visible name:* igual.
2. **Templates:** `Hikvision camera by HTTP` e `ICMP Ping`.
3. **Host groups:** `CCTV`.
4. **Interfaces → Add → Agent:** IP del equipo, puerto `10050`. No hay agente; la interfaz solo da al ping la IP que debe usar. Su disponibilidad *ZBX* quedará en gris (*unknown*), lo cual es normal.
5. **Tags:**
   - `uplink` = equipo del que depende (`NVR 01`, `NAS-03`…).
   - **`notificar` = `no` mientras se termina el alta.** Sin contraseña, la plantilla da *Authorisation error* y, sin esta etiqueta, enviaría correos. Si se pone después de crear el host, los problemas ya abiertos no la tienen y sí notifican.
6. **Macros** (pestaña *Macros*):

   | Macro | Valor |
   |---|---|
   | `{$HIKVISION_ISAPI_HOST}` | IP del equipo |
   | `{$PASSWORD}` | Contraseña, de tipo **Secret text** (botón del candado). Nunca en texto plano |
   | `{$USER}` | Solo si no es `admin`, el valor por defecto de la plantilla |
   | `{$HIKVISION_STREAM_WIDTH}` / `{$HIKVISION_STREAM_HEIGHT}` | Resolución del canal principal si no es 1920×1080 (p. ej. `2560`/`1440`). Si no coincide, aparece el aviso *Invalid video stream resolution parameters* |

   Para varias cámaras con la misma contraseña: crearlas y después *Data collection → Hosts* → marcarlas → *Mass update* → pestaña *Macros* → *Add* `{$PASSWORD}` (Secret text).
7. **Add**.
8. **Dependencias** ([dependencias](dependencias.md)):
   - *Unavailable by ICMP ping*, *High ICMP ping loss* y *High ICMP ping response time* dependen del *Unavailable by ICMP ping* del equipo padre.
   - **Hikvision: Error receiving data** depende del *Unavailable by ICMP ping* **del propio equipo**, para no recibir dos avisos cuando la cámara cae.
   - Los triggers por canal (*Channel "1": Error receiving data*) se crean por descubrimiento y no admiten dependencias en el host. Si la cámara cae, también pueden avisar.
9. Cuando haya datos (≈ 5 min) y *Monitoring → Latest data* muestre *Device name*:
   - Comprobar que el nombre del host coincide con él.
   - **Quitar la etiqueta `notificar=no`**, salvo en cámaras inestables (ver abajo).
10. Regenerar el [inventario](../inventario.md) y los [mapas](../mapas.md).

## Cámaras inestables: solo dashboard

Si una cámara se cae a menudo por un enlace débil y sus alertas no son accionables, dejarle la etiqueta **`notificar` = `no`**.
- Sus problemas siguen viéndose en el dashboard y en *Monitoring → Problems*.
- Las acciones no envían Telegram ni Gmail ([alertas](../alertas.md#solo-dashboard-etiqueta-notificarno)).
- Registrar el motivo en el [registro](../registro.md).

## Verificar

- *Latest data*: `ICMP ping` = 1 y *Get device info: Login status* = 0 (correcto). Un 1 indica error de autorización: revisar `{$USER}` y `{$PASSWORD}`.
- *Device name*, *Model* y *Firmware version* tienen valor.
- El equipo aparece en el submapa *Likson - CCTV NVR 01*, o en el de su sitio, con la línea hacia su padre.

## Con scripts

```sh
S=agents/scripts/run_remote.sh
# Alta (con la etiqueta notificar=no desde el principio)
printf '%s\n' "$TOKEN" | $S zbx_create_snmp_host.py --name "CAM 06 Patio" --ip 192.168.60.15 --group CCTV --interface ping \
    --template "Hikvision camera by HTTP" "ICMP Ping" --macro '{$HIKVISION_ISAPI_HOST}=192.168.60.15' \
    --tag notificar=no --uplink "NVR 01" --self-dependency "Error receiving data" --dry-run
# La contraseña la pone una persona en la interfaz (Secret text). Después, nombre desde la cámara y etiqueta:
printf '%s\n' "$TOKEN" | $S zbx_latest.py --group CCTV --name "Device name"
printf '%s\n' "$TOKEN" | $S zbx_align_host_name.py --host "CAM 192.168.60.15" --rename "CAM 06 Patio"
printf '%s\n' "$TOKEN" | $S zbx_set_tag.py --host "CAM 06 Patio" --remove notificar
# Equipo ya creado sin interfaz: añadir la de ping
printf '%s\n' "$TOKEN" | $S zbx_add_interface.py --host "CAM 06 Patio" --ip 192.168.60.15 --type ping
```
