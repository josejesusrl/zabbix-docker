# Mimosa C5C by SNMP

> **Fichero:** `zabbix_templates/mimosa_c5c.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** radios Mimosa C5C (y familia B5/C5) en enlaces PTP, con SNMPv2. Se usa **junto con** la oficial *Network Generic Device by SNMP*, que aporta interfaces con tráfico de 64 bits, ping, disponibilidad SNMP y reinicios, y con *Switch port changes by SNMP* para el puerto Ethernet del radio.
**Recoge:** estado y uptime del enlace, modo (AP/estación), potencia RX/TX total, potencia RX, ruido y SNR por polarización (H/V), velocidad PHY, MCS y EVM por stream, tasa de errores de paquete (PER) TX/RX, frecuencia, ancho de canal, temperatura, firmware y número de serie.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Wireless link is disconnected | High | El enlace radio cae | Al reconectar |
| Wireless link was re-established | Warning | El enlace lleva menos de `{$MIMOSA.LINK.UPTIME.MIN}` s (600) conectado: hubo un corte | Solo, pasados 10 min |
| Very low RX power | High | Potencia RX total < `{$MIMOSA.RX.POWER.MIN.CRIT}` durante 10 min | Solo |
| Low RX power | Warning | < `{$MIMOSA.RX.POWER.MIN.WARN}` durante 10 min. Silenciado si hay crítico | Solo |
| RX chain imbalance | Warning | Diferencia H/V > `{$MIMOSA.CHAIN.DIFF.MAX}` (6 dB) durante 30 min: cable, conector o alineación | Solo |
| Low SNR | Warning | SNR de alguna cadena < `{$MIMOSA.SNR.MIN.WARN}` (12 dB) durante 15 min | Solo |
| High noise | Warning | Ruido > `{$MIMOSA.NOISE.MAX.WARN}` (-85 dBm) durante 15 min: interferencia | Solo |
| High packet error rate | Warning | PER TX o RX > `{$MIMOSA.PER.MAX.WARN}` (10 %) durante 15 min | Solo |
| Low TX PHY rate / Low RX PHY rate | High | Velocidad PHY total (suma de los 2 streams) de ese sentido < `{$MIMOSA.PHY.MIN.WARN}` (200 Mbps) durante 10 min: la modulación cayó y el troncal perdió capacidad | Solo, al recuperarse |
| Temperature is high / critical | Warning / High | > `{$MIMOSA.TEMP.MAX.WARN}` (70 °C) / `{$MIMOSA.TEMP.MAX.CRIT}` (80 °C) durante 5 min | Solo |
| Firmware version has changed | Information | Cambio de firmware (solo registro, no notifica) | Sola |

Los triggers de potencia, SNR, ruido, desequilibrio, PER y velocidad PHY se silencian mientras el enlace está caído. Cada extremo vigila su TX y su RX, así que con los dos hosts se cubren ambos sentidos del enlace desde el emisor y desde el receptor. Se usa la velocidad PHY por sentido y no la velocidad de `wifi0`, que es una sola cifra sin dirección.
**Umbrales de potencia por enlace:** `{$MIMOSA.RX.POWER.MIN.WARN}` ≈ señal de diseño − 6 dB y `CRIT` ≈ diseño − 11 dB. Para `Lk_Trunk_01_A` (diseño -65 dBm): -71 / -76.
