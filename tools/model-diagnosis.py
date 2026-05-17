#!/usr/bin/env python3
"""
批量诊断 API Key 可用性
用法: python3 model-diagnosis.py

输出每个 key 的：✅可用 / ❌未激活 / ⚠️其他错误
依赖: 标准库 (subprocess, json, time, os)
"""
import subprocess, json, time, os

def get_env_key(var_name):
    """从 ~/.hermes/.env 读取真实 key"""
    env_file = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_file):
        for line in open(env_file, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, _, v = line.partition('=')
            if k.strip() == var_name:
                return v.strip()
    return ''


def test_model(key, model, base_url, timeout=10):
    """测试单个模型是否可用"""
    chat_url = base_url.rstrip('/') + '/chat/completions'
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5
    })
    try:
        r = subprocess.run(
            ["curl", "-s", chat_url,
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "-d", payload,
             "--max-time", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 5
        )
        j = json.loads(r.stdout.strip())
        err = j.get("error", {})
        code = err.get("code", "")

        if j.get("choices") or j.get("object") == "chat.completion":
            return "✅ 可用", ""
        if code in ("ModelNotOpen", "NotFound"):
            return "❌ 未激活", code
        if code:
            return f"⚠️ {code}", err.get("message", "")[:60]
        return "⚠️ 未知错误", r.stdout[:80]
    except subprocess.TimeoutExpired:
        return "❌ 超时", ""
    except Exception as e:
        return f"⚠️ {type(e).__name__}", str(e)[:60]


def diagnose_key(key, base_url, key_label=""):
    """诊断单个 key 的所有模型"""
    label = key_label or key[:20] + "..."
    # 先尝试获取模型列表
    models_url = base_url.rstrip('/') + '/models'
    try:
        r = subprocess.run(
            ["curl", "-s", models_url,
             "-H", f"Authorization: Bearer {key}",
             "--max-time", "10"],
            capture_output=True, text=True, timeout=15
        )
        model_list = []
        try:
            data = json.loads(r.stdout.strip())
            model_list = [m["id"] for m in data.get("data", [])]
        except:
            pass
    except:
        model_list = []

    if not model_list:
        print(f"\n[{label}] 无法获取模型列表，尝试用已知模型探测...")
        # fallback：用已知模型名探测
        known = {
            "GLM-5.1": ("GLM-5.1",),
            "MiniMax-M2.7-highspeed": ("MiniMax-M2.7-highspeed",),
            "gpt-5.4": ("gpt-5.4",),
            "deepseek-v4-flash": ("deepseek-v4-flash",),
        }
        results = []
        for mname, (m,) in known.items():
            status, detail = test_model(key, m, base_url)
            results.append((m, status, detail))
            time.sleep(0.2)
    else:
        results = []
        for m in model_list:
            status, detail = test_model(key, m, base_url)
            results.append((m, status, detail))
            time.sleep(0.15)

    # 打印结果
    available = [(m, s) for m, s, d in results if "✅" in s]
    inactive  = [(m, s) for m, s, d in results if "❌" in s]
    other     = [(m, s, d) for m, s, d in results if "✅" not in s and "❌" not in s]

    print(f"\n{'='*80}")
    print(f"Key: {label}")
    print(f"Base URL: {base_url}")
    print(f"{'='*80}")
    for m, s, *rest in [(m, s, d) for m, s, d in results]:
        detail = rest[0] if rest else ""
        print(f"  [{s:<12}] {m:<50} {detail}")
    print(f"\n✅ 可用: {len(available)} | ❌ 未激活: {len(inactive)} | ⚠️ 其他: {len(other)}")

    return available, inactive, other


def main():
    import yaml
    config_path = os.path.expanduser("~/.hermes/config.yaml")

    keys = []
    if os.path.exists(config_path):
        try:
            conf = yaml.safe_load(open(config_path))
            for prov in conf.get("custom_providers", []):
                api_key_raw = prov.get("api_key", "")
                base_url    = prov.get("base_url", "")
                name        = prov.get("name", "")
                if not api_key_raw or not base_url:
                    continue
                # 解析 env 变量引用
                import re
                m = re.search(r'\$\{([^}]+)\}', api_key_raw)
                if m:
                    real_key = get_env_key(m.group(1))
                else:
                    real_key = api_key_raw
                keys.append((real_key, base_url, name))
        except Exception as e:
            print(f"读取配置失败: {e}")

    if not keys:
        print("未找到 API key，请检查 config.yaml 中的 custom_providers")
        return

    for key, base_url, label in keys:
        diagnose_key(key, base_url, label)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
