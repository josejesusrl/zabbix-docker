# Configurar el envío de traps

> **Cuándo:** al configurar un equipo para que envíe traps SNMP a Zabbix.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. Destino de traps: `192.168.0.191`, puerto **162/udp**, SNMPv2c, comunidad de traps. **No** usar `zabbix.likson.com`: apunta a Cloudflare, que solo lleva la web ([acceso externo](../../despliegue/acceso-externo.md)).
2. El trap debe salir con la misma IP que la interfaz SNMP del host en Zabbix.
3. Comprobar la llegada en el servidor:
   ```sh
   cd ~/zabbix-docker && docker compose --env-file .env --env-file server.env exec zabbix-snmptraps tail -8 /var/lib/zabbix/snmptraps/snmptraps.log
   ```
   Debe aparecer `ZBXTRAP <IP del equipo>`. Los traps sin host coincidente se registran en el log del server como *unmatched trap*.
4. Si se ha olvidado la comunidad de traps: `sudo awk '/^authCommunity/{print $3}' ~/zabbix-docker/snmptraps/snmptrapd.conf`.

## Probar la recepción desde el servidor

Envía un trap de prueba con la comunidad configurada, sin mostrarla, y revisa el log. Desde el propio servidor la IP de origen aparece como `172.16.238.1`; la de un equipo real debe ser la suya.

```sh
cd ~/zabbix-docker
C="docker compose --env-file .env --env-file server.env"
export COM=$($C exec -T zabbix-snmptraps awk '/^authCommunity/{print $3}' /etc/snmp/snmptrapd.conf)
docker run --rm -e COM alpine:3.22 sh -c 'apk add -q --no-cache net-snmp-tools >/dev/null && snmptrap -v 2c -c "$COM" 192.168.0.191:162 "" 1.3.6.1.6.3.1.1.5.3 1.3.6.1.2.1.2.2.1.1.1 i 1'
unset COM
$C exec zabbix-snmptraps tail -5 /var/lib/zabbix/snmptraps/snmptraps.log
```

## Cambiar la comunidad de traps

Respaldo, borrar `snmptraps/snmptrapd.conf`, ejecutar `./server_setup.sh` (pide la nueva comunidad sin mostrarla) y `zbx up -d --force-recreate zabbix-snmptraps`. Después, cambiarla en todos los equipos que envían traps.
