"""Import template YAML files (zabbix_templates/*.yaml) into Zabbix.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_templates/X.yaml zbx_import_template.py X.yaml [--delete-missing] [--dry-run]

--delete-missing removes items, triggers, discovery rules and prototypes that are no longer in the file.
"""
import argparse
import re

from zbx_api import api_from_stdin, import_template


def template_names(yaml_text):
    return re.findall(r"^\s+template: '?([^'\n]+)'?$", yaml_text, re.MULTILINE)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--delete-missing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        names = template_names(text)
        if args.dry_run:
            print(f"Se importaría {path}: {names} (delete missing: {args.delete_missing})")
            continue
        import_template(api, text, args.delete_missing)
        print(f"Importado {path}: {names}")


if __name__ == "__main__":
    main()
