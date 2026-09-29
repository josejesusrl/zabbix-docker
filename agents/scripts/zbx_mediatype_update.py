"""Update a media type from files in zabbix_media/: webhook script, message templates and selected parameters.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_media/telegram/telegram.js -f zabbix_media/telegram/message_templates.json \\
      zbx_mediatype_update.py --name Telegram --script telegram.js --templates message_templates.json \\
      --param api_parse_mode=html [--dry-run]

- --script: replaces the webhook script.
- --templates: JSON {"message_templates": [{eventsource, recovery, subject, message}, ...]}. Only the
  listed (eventsource, recovery) pairs are replaced; the other templates of the media type are kept.
- --param NAME=VALUE: changes only those parameters. Other parameters, including secrets such as the
  bot token, are sent back unchanged and never printed.
"""
import argparse
import json

from zbx_api import api_from_stdin

TEMPLATE_KEY = ("eventsource", "recovery")


def key_value(text):
    name, sep, value = text.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError(f"expected NAME=VALUE: {text}")
    return name, value


def merge_templates(current, new):
    by_key = {tuple(t[k] for k in TEMPLATE_KEY): t for t in current}
    for t in new:
        by_key[(str(t["eventsource"]), str(t["recovery"]))] = t
    return [{k: t[k] for k in ("eventsource", "recovery", "subject", "message")} for t in by_key.values()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True)
    parser.add_argument("--script")
    parser.add_argument("--templates")
    parser.add_argument("--param", nargs="*", type=key_value, default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    media = api.call("mediatype.get", {"filter": {"name": [args.name]}, "output": ["mediatypeid", "name", "parameters", "script"],
                                       "selectMessageTemplates": "extend"})[0]
    update = {"mediatypeid": media["mediatypeid"]}
    if args.script:
        with open(args.script, encoding="utf-8") as f:
            update["script"] = f.read()
        print(f"script: {len(media['script'])} -> {len(update['script'])} caracteres")
    if args.templates:
        with open(args.templates, encoding="utf-8") as f:
            new = json.load(f)["message_templates"]
        update["message_templates"] = merge_templates(media["message_templates"], new)
        print(f"plantillas: {len(new)} reemplazadas, {len(update['message_templates'])} en total")
    if args.param:
        changes = dict(args.param)
        names = {p["name"] for p in media["parameters"]}
        missing = set(changes) - names
        if missing:
            raise SystemExit(f"unknown parameters: {', '.join(sorted(missing))}")
        update["parameters"] = [{"name": p["name"], "value": changes.get(p["name"], p["value"])} for p in media["parameters"]]
        print("parámetros cambiados:", ", ".join(f"{k}={v}" for k, v in changes.items()))
    if not args.dry_run:
        api.call("mediatype.update", update)
        print(f"Medio '{media['name']}' actualizado")


if __name__ == "__main__":
    main()
