# Configurar el envío de traps

> **Cuándo:** al configurar un equipo para que envíe traps SNMP a Zabbix.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. Destino de traps: `192.168.0.191` (o `zabbix.likson.com`), puerto **162/udp**, SNMPv2c, comunidad de traps.
2. El trap debe salir con la misma IP que la interfaz SNMP del host en Zabbix.
3. Comprobar la llegada en el servidor:
   ```sh
   cd ~/zabbix-docker && docker compose --env-file .env --env-file server.env exec zabbix-snmptraps tail -8 /var/lib/zabbix/snmptraps/snmptraps.log
   ```
   Debe aparecer `ZBXTRAP <IP del equipo>`. Los traps sin host coincidente se registran en el log del server como *unmatched trap*.
4. Si se ha olvidado la comunidad de traps: `sudo awk '/^authCommunity/{print $3}' ~/zabbix-docker/snmptraps/snmptrapd.conf`.
