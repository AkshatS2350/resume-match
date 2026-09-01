"""Export the public OpenAPI document and generated TypeScript contract surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from resumematch.api.app import app  # noqa: E402


def main() -> None:
    document = app.openapi()
    schema_path = ROOT / "docs" / "schemas" / "openapi.json"
    types_path = ROOT / "web" / "src" / "lib" / "api" / "generated" / "openapi.ts"
    schema_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    components = document.get("components", {}).get("schemas", {})
    declarations = ["// Generated from docs/schemas/openapi.json. Do not edit.", ""]
    for name in sorted(components):
        schema = components[name]
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        declarations.append(f"export interface {name} {{")
        for field in sorted(properties):
            value = properties[field]
            primitive = {"string": "string", "integer": "number", "boolean": "boolean"}.get(
                value.get("type"), "unknown"
            )
            optional = "" if field in required else "?"
            declarations.append(f"  {field}{optional}: {primitive};")
        declarations.append("}")
        declarations.append("")
    types_path.write_text("\n".join(declarations), encoding="utf-8")


if __name__ == "__main__":
    main()
