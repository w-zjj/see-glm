#!/usr/bin/env python3
"""Generate platform adapters from one shared Skill template."""
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ADAPTERS = ROOT / "adapters"
TEMPLATE = ADAPTERS / "SKILL.template.md"
METADATA = ADAPTERS / "metadata.json"


def render(name, metadata, template):
    if any(line.strip() == "---" for line in metadata["frontmatter"]):
        raise ValueError(
            f"{name} frontmatter must not include YAML delimiters; "
            "the template provides them"
        )
    frontmatter = "\n".join(metadata["frontmatter"])
    installation = "\n".join(metadata["install"])
    return (
        template.replace("{{FRONTMATTER}}", frontmatter)
        .replace("{{INSTALLATION}}", installation)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    template = TEMPLATE.read_text(encoding="utf-8")
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    expected_names = {
        "zcode",
        "trae",
        "claude",
        "codex",
        "deepseek-harness",
        "workbuddy",
        "opencode",
    }
    if set(metadata) != expected_names:
        raise SystemExit("adapter metadata must define exactly seven supported adapters")

    mismatches = []
    for name, config in metadata.items():
        output = ADAPTERS / name / "SKILL.md"
        rendered = render(name, config, template)
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                mismatches.append(str(output))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")

    if mismatches:
        raise SystemExit("generated adapter docs are out of date:\n" + "\n".join(mismatches))


if __name__ == "__main__":
    main()
