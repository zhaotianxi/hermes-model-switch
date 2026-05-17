from __future__ import annotations

MODEL_SPECS = {
    "gpt": {
        "label": "GPT-5.4",
        "default": "gpt-5.4",
        "provider_name": "modelverse-gpt",
        "provider_ref": "custom:modelverse-gpt",
        "base_url": "https://api.modelverse.cn/v1",
        "api_key_env": "MODELVERSE_API_KEY_GPT",
        "verify_model": "gpt-5.4",
        "alias": "gpt",
        "models": {"gpt-5.4": {"context_length": 200000}},
    },
    "glm": {
        "label": "GLM-5.1",
        "default": "GLM-5.1",
        "provider_name": "svips-glm",
        "provider_ref": "custom:svips-glm",
        "base_url": "https://api.svips.org/v1",
        "api_key_env": "SVIPS_API_KEY_GLM",
        "verify_model": "GLM-5.1",
        "alias": "glm",
        "models": {"GLM-5.1": {"context_length": 200000, "max_output_tokens": 200000}},
    },
    "minimax": {
        "label": "MiniMax-M2.7-highspeed",
        "default": "MiniMax-M2.7-highspeed",
        "provider_name": "svips-minimax",
        "provider_ref": "custom:svips-minimax",
        "base_url": "https://api.svips.org/v1",
        "api_key_env": "SVIPS_API_KEY_MINIMAX",
        "verify_model": "MiniMax-M2.7-highspeed",
        "alias": "minimax",
        "models": {"MiniMax-M2.7-highspeed": {"context_length": 200000}},
    },
    "ds": {
        "label": "DeepSeek-v4-flash",
        "default": "deepseek-v4-flash",
        "provider_name": "chudian-deepseek",
        "provider_ref": "custom:chudian-deepseek",
        "base_url": "https://llm.chudian.site/v1",
        "api_key_env": "CHUDIAN_API_KEY_DEEPSEEK",
        "verify_model": "deepseek-v4-flash",
        "alias": "deepseek",
        "models": {"deepseek-v4-flash": {"context_length": 1000000, "max_output_tokens": 1000}},
    },
}


def get_spec(mode: str) -> dict:
    if mode not in MODEL_SPECS:
        raise KeyError(f"unknown mode: {mode}")
    return MODEL_SPECS[mode]


def iter_specs():
    return MODEL_SPECS.items()


def mode_from_default(default_model: str) -> str | None:
    for mode, spec in MODEL_SPECS.items():
        if spec["default"] == default_model:
            return mode
    return None


def build_main_model_config(spec: dict) -> dict:
    return {
        "default": spec["default"],
        "provider": spec["provider_ref"],
        "base_url": spec["base_url"],
        "api_key": "${" + spec["api_key_env"] + "}",
    }


def build_provider_def(spec: dict) -> dict:
    return {
        "name": spec["provider_name"],
        "base_url": spec["base_url"],
        "api_key": "${" + spec["api_key_env"] + "}",
        "model": spec["default"],
        "models": spec["models"],
    }


def build_alias_update(spec: dict) -> tuple[str, dict]:
    return spec["alias"], {
        "base_url": spec["base_url"],
        "model": spec["default"],
        "provider": spec["provider_ref"],
        "api_key": "${" + spec["api_key_env"] + "}",
    }
