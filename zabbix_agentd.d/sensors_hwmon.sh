#!/bin/sh
# Temperature sensors of the host from Linux hwmon (/sys/class/hwmon).
# Sensor drivers are loaded on the host by lm-sensors (sensors-detect).
# Usage:
#   sensors_hwmon.sh discovery                 LLD JSON with {#CHIP}, {#DEVICE}, {#SENSOR}, {#LABEL}
#   sensors_hwmon.sh temp <chip> <device> <tempN>   temperature in °C
# hwmonN numbering may change on reboot, sensors are identified by chip name and device.

HWMON=/sys/class/hwmon
# Decimal point independent of locale
LC_ALL=C
export LC_ALL

device_id() {
    if [ -e "$1/device" ]; then
        basename "$(readlink -f "$1/device")"
    else
        echo virtual
    fi
}

json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

case "${1:-}" in
    discovery)
        sep=""
        printf '['
        for d in "$HWMON"/hwmon*; do
            [ -r "$d/name" ] || continue
            chip=$(cat "$d/name")
            device=$(device_id "$d")
            for input in "$d"/temp*_input; do
                [ -r "$input" ] || continue
                sensor=$(basename "$input" _input)
                label=$sensor
                [ -r "$d/${sensor}_label" ] && label=$(cat "$d/${sensor}_label")
                printf '%s{"{#CHIP}":"%s","{#DEVICE}":"%s","{#SENSOR}":"%s","{#LABEL}":"%s"}' \
                    "$sep" "$(json_escape "$chip")" "$(json_escape "$device")" "$sensor" "$(json_escape "$label")"
                sep=","
            done
        done
        printf ']\n'
        ;;
    temp)
        case "${4:-}" in
            temp[0-9]*) ;;
            *) echo "Invalid sensor: ${4:-}" >&2; exit 1 ;;
        esac
        for d in "$HWMON"/hwmon*; do
            [ "$(cat "$d/name" 2>/dev/null)" = "${2:-}" ] || continue
            [ "$(device_id "$d")" = "${3:-}" ] || continue
            awk '{ printf "%.1f\n", $1 / 1000 }' "$d/${4}_input"
            exit
        done
        echo "Sensor not found: ${2:-} ${3:-} ${4:-}" >&2
        exit 1
        ;;
    *)
        echo "Usage: $0 discovery|temp <chip> <device> <tempN>" >&2
        exit 1
        ;;
esac
