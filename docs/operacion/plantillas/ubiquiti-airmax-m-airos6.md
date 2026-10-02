# Ubiquiti airMAX M (airOS 6) wireless by SNMPv1

> **Fichero:** `zabbix_templates/ubiquiti_airmax_m_airos6_wireless.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** equipos airMAX M con airOS 6 (Rocket M5, NanoStation M…). Es la misma plantilla que la de airOS 8, pero **sin** GPS, CINR ni capacidad de cliente, que son exclusivos de AC. Añade **airMAX quality y capacity** del AP y por cliente, que en airMAX M son las mejores medidas de calidad.
Mismos triggers y macros que [airOS 8](ubiquiti-airos8.md), salvo los de GPS y capacidad (airOS 6 no la publica); incluye el de cambio de velocidad de `eth0`. El CCQ viene en porcentaje directo. No recoge el tiempo de conexión del cliente (limitación de SNMPv1 en airOS 6). Tiene el item fijo *Clients: minimum signal*.
