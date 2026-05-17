from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from hermes_model_switch.config_io import save_yaml


@pytest.fixture()
def hermes_dir(tmp_path: Path) -> Path:
    root = tmp_path / ".hermes"
    root.mkdir()
    (root / ".env").write_text(
        "MODELVERSE_API_KEY_GPT=test-gpt\n"
        "SVIPS_API_KEY_GLM=test-glm\n"
        "SVIPS_API_KEY_MINIMAX=test-minimax\n"
        "CHUDIAN_API_KEY_DEEPSEEK=test-ds\n",
        encoding="utf-8",
    )
    save_yaml(
        root / "config.yaml",
        {
            "model": {
                "default": "gpt-5.4",
                "provider": "custom:modelverse-gpt",
                "base_url": "https://api.modelverse.cn/v1",
                "api_key": "${MODELVERSE_API_KEY_GPT}",
            },
            "custom_providers": [
                {
                    "name": "modelverse-gpt",
                    "base_url": "https://api.modelverse.cn/v1",
                    "api_key": "${MODELVERSE_API_KEY_GPT}",
                    "model": "gpt-5.4",
                    "models": {"gpt-5.4": {"context_length": 200000}},
                }
            ],
            "model_aliases": {
                "gpt": {
                    "provider": "custom:modelverse-gpt",
                    "base_url": "https://api.modelverse.cn/v1",
                    "model": "gpt-5.4",
                    "api_key": "${MODELVERSE_API_KEY_GPT}",
                }
            },
        },
    )
    return root
