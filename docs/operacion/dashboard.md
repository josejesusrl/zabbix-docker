# Dashboard "Likson NOC"

*Dashboards → Likson NOC*: 4 páginas; se pueden rotar automáticamente con el botón de reproducción (60 s por página).

| Página | Contenido |
|---|---|
| **Resumen** | Clientes conectados y APs en línea (con tendencia), problemas por severidad, disponibilidad de equipos, tráfico de los proveedores de internet de EDGE 01 (Coefi01 principal, Telmex respaldo), CPU media de EDGE 01 / NAS-01 / NAS-03, problemas activos (Warning o superior) e histórico de clientes |
| **Access Points** | Panal con un AP por celda coloreado por clientes (rojo = 0, verde, naranja a partir de 35), y tabla por AP: clientes, peor señal y peor capacidad de sus clientes, ruido, carga y tráfico radio |
| **Enlaces PTP** | Tabla de backhaul (señal del par, capacidad TX/RX, ruido, velocidad de `eth0`; ordenada por peor señal), tabla del troncal Mimosa (estado, potencia RX, PHY, PER, temperatura) y gráficos de capacidad y PHY |
| **Infraestructura** | CPU media de routers y NAS, tráfico EDGE 01 → NAS, tabla de servidores (CPU, memoria, disco, contenedores), temperaturas del servidor Zabbix y tráfico del switch |

**Indicadores globales:** el host **KPI Likson** (grupo *Likson KPIs*, plantilla `zabbix_templates/likson_kpis.yaml`) calcula el total de clientes conectados, los APs en línea y totales, y la CPU media de EDGE 01, NAS-01 y NAS-03. Sus fórmulas usan el grupo *Access Points PPPoE Clients* y los nombres de esos hosts: si cambian, hay que actualizar la plantilla.

**Para modificar el dashboard:**
1. Editar `zabbix_dashboards/likson_noc.json`. Los hosts, grupos e items se escriben por nombre.
2. Respaldo.
3. Aplicar con `agents/scripts/zbx_dashboard_apply.py`, que reemplaza todas las páginas.

Los cambios hechos en la interfaz se pierden en la siguiente aplicación si no se copian al JSON. Las tablas (*Top hosts*) necesitan el nombre exacto del item en todos los hosts. Por eso las plantillas Ubiquiti tienen items con nombre fijo: *Clients: minimum signal / minimum TX capacity / minimum RX capacity* (el peor cliente, o el par en un enlace PTP).
