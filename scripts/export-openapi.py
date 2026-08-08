"""Export the FastAPI schema without starting a server or using a network."""

from __future__ import annotations

import json
from pathlib import Path

from secure_cloud_platform.api import create_app

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output = ROOT / "web" / "openapi.json"
    schema = create_app().openapi()
    output.write_text(
        json.dumps(schema, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
