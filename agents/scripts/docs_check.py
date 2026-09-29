"""Check the project documentation.

Usage:
  python3 agents/scripts/docs_check.py              (local, from any directory of the repository)
  printf '%s\\n' "$TOKEN" | agents/scripts/run_remote.sh -f docs/operacion/inventario.md \\
      docs_check.py --zabbix inventario.md          (compares the inventory with the hosts of Zabbix)

Local checks:
- Relative links of the project documents point to existing files, and their #anchors to existing headings.
- No references to removed documents (OPERACION.md, SERVER_DEPLOY.md).
- Every zabbix_templates/*.yaml is described in docs/operacion/plantillas.md.
- Every script of agents/scripts/ is listed in agents/scripts/README.md.
- Every procedure of docs/operacion/procedimientos/ is linked from docs/README.md.
Exit code 1 if something fails.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ["README.md", "AGENTS.md", "CLAUDE.md", "agents/scripts/README.md", "docs"]
SKIP = {"docs/upstream-zabbix-README.md"}
REMOVED = ["OPERACION.md", "SERVER_DEPLOY.md"]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def markdown_files():
    for entry in DOCS:
        path = ROOT / entry
        files = sorted(path.rglob("*.md")) if path.is_dir() else [path]
        yield from (f for f in files if str(f.relative_to(ROOT)) not in SKIP)


def slug(heading):
    """GitHub anchor of a heading."""
    text = re.sub(r"[`*_\[\]()]", "", heading.strip().lower())
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path):
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    return {slug(h) for h in re.findall(r"^#{1,6} (.+)$", text, re.M)}


def check_links(errors):
    for md in markdown_files():
        text = FENCE.sub("", md.read_text(encoding="utf-8"))
        rel = md.relative_to(ROOT)
        for target in LINK.findall(text):
            if re.match(r"[a-z]+:", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (md.parent / file_part).resolve() if file_part else md
            if not dest.exists():
                errors.append(f"{rel}: enlace roto -> {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                errors.append(f"{rel}: ancla inexistente -> {target}")
        for name in REMOVED:
            if name in text:
                errors.append(f"{rel}: menciona {name}, que ya no existe")


def check_listed(errors, files, document, what):
    text = (ROOT / document).read_text(encoding="utf-8")
    for f in files:
        if f.name not in text:
            errors.append(f"{document}: falta {what} {f.name}")


def check_zabbix(inventory):
    from zbx_api import api_from_stdin

    text = Path(inventory).read_text(encoding="utf-8")
    documented = set()
    for line in text.splitlines():
        if line.startswith("| ") and not line.startswith("| Host |"):
            documented.add(re.split(r"(?<!\\) \| ", line[2:])[0].replace("\\|", "|").strip())
    api = api_from_stdin()
    real = {h["name"] for h in api.call("host.get", {"output": ["name"]})}
    errors = [f"en Zabbix pero no en el inventario: {n}" for n in sorted(real - documented)]
    errors += [f"en el inventario pero no en Zabbix: {n}" for n in sorted(documented - real)]
    return errors, len(real)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zabbix", metavar="INVENTARIO", help="compare this inventory file with Zabbix (token on stdin)")
    args = parser.parse_args()

    if args.zabbix:
        errors, count = check_zabbix(args.zabbix)
        ok = f"inventario OK: {count} hosts coinciden con Zabbix"
    else:
        errors = []
        check_links(errors)
        check_listed(errors, sorted((ROOT / "zabbix_templates").glob("*.yaml")), "docs/operacion/plantillas.md", "la plantilla")
        scripts = [f for f in sorted((ROOT / "agents/scripts").iterdir()) if f.suffix in (".py", ".sh")]
        check_listed(errors, scripts, "agents/scripts/README.md", "el script")
        check_listed(errors, sorted((ROOT / "docs/operacion/procedimientos").glob("*.md")), "docs/README.md", "el procedimiento")
        ok = f"documentación OK ({len(list(markdown_files()))} ficheros)"
    for e in errors:
        print("ERROR", e)
    print(ok if not errors else f"{len(errors)} errores")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
