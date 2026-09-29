# Zabbix de Likson (zabbix.likson.com)

Monitoreo de la red WISP de Likson con Zabbix 7.4 en Docker: routers MikroTik, switches, APs Ubiquiti, enlaces PTP (Mimosa y Ubiquiti) y servidores. Este repositorio es un fork de [`zabbix/zabbix-docker`](https://github.com/zabbix/zabbix-docker). La rama `server-deploy` tiene el despliegue de producción; `7.4` se mantiene igual que la rama oficial.

| Necesito… | Ir a |
|---|---|
| Ver qué se monitorea y cómo | [Documentación](docs/README.md) |
| Instalar o recuperar el servidor | [Despliegue](docs/README.md#servidor) |
| Añadir un equipo o resolver una alerta | [Operación](docs/README.md#añadir-o-cambiar-equipos) |
| Trabajar como agente de IA | [AGENTS.md](AGENTS.md) |
| El README original de Zabbix | [docs/upstream-zabbix-README.md](docs/upstream-zabbix-README.md) |

## Estructura

| Ruta | Contenido |
|---|---|
| `docker-compose.yml`, `compose_server.yaml`, `server.env.example`, `env_vars/`, `nginx/` | Definición del stack |
| `server_*.sh` | Preparación del host, certificados, respaldo y restauración |
| `zabbix_templates/`, `zabbix_media/`, `zabbix_dashboards/`, `zabbix_agentd.d/` | Plantillas, mensajes, dashboard y UserParameters |
| `agents/scripts/` | Scripts de la API de Zabbix |
| `docs/` | Documentación |
| Resto (`Dockerfiles/`, `compose_*.yaml`, `kubernetes.yaml`…) | Ficheros oficiales de Zabbix, sin modificar |

Servidor: `jjrl@192.168.0.191`, repositorio en `~/zabbix-docker`. **Antes de cualquier cambio en producción, respaldo** (`sudo ./server_backup.sh`).
