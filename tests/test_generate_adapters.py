"""Adapter generation tests."""
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import generate_adapters  # noqa: E402


def test_generated_adapters_use_standard_yaml_frontmatter():
    template = generate_adapters.TEMPLATE.read_text(encoding="utf-8")
    metadata = json.loads(generate_adapters.METADATA.read_text(encoding="utf-8"))

    for name, config in metadata.items():
        rendered = generate_adapters.render(name, config, template)
        lines = rendered.splitlines()
        assert rendered.startswith("---\nname: see-glm\n")
        assert "---" in lines[1:]
