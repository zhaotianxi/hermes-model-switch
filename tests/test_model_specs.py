from hermes_model_switch.model_specs import (
    build_alias_update,
    build_main_model_config,
    build_provider_def,
    mode_from_default,
)


def test_mode_from_default():
    assert mode_from_default("gpt-5.4") == "gpt"
    assert mode_from_default("GLM-5.1") == "glm"
    assert mode_from_default("missing") is None


def test_builders_are_consistent():
    main = build_main_model_config({
        "default": "gpt-5.4",
        "provider_ref": "custom:modelverse-gpt",
        "base_url": "https://api.modelverse.cn/v1",
        "api_key_env": "MODELVERSE_API_KEY_GPT",
    })
    provider = build_provider_def({
        "provider_name": "modelverse-gpt",
        "base_url": "https://api.modelverse.cn/v1",
        "api_key_env": "MODELVERSE_API_KEY_GPT",
        "default": "gpt-5.4",
        "models": {"gpt-5.4": {"context_length": 1}},
    })
    alias_key, alias_value = build_alias_update({
        "alias": "gpt",
        "base_url": "https://api.modelverse.cn/v1",
        "default": "gpt-5.4",
        "provider_ref": "custom:modelverse-gpt",
        "api_key_env": "MODELVERSE_API_KEY_GPT",
    })
    assert main["default"] == provider["model"] == alias_value["model"]
    assert alias_key == "gpt"
