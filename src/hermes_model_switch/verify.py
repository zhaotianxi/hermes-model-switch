from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request


def verify_model(api_key: str, base_url: str, model_name: str, timeout: int = 12) -> tuple[bool, str]:
    if not api_key:
        return False, "缺少 API Key"
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, f"HTTP {exc.code}: {body[:80]}"
    except Exception as exc:
        return False, str(exc)[:80]

    error = data.get("error", {})
    code = error.get("code", "")
    if code in ("ModelNotOpen", "NotFound") or data.get("object") == "error":
        return False, f"未激活或不存在 (code={code})"
    if data.get("choices"):
        return True, ""
    return False, str(error.get("message", "未知错误"))[:80]


def hermes_smoke_test(timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["hermes", "chat", "-q", "只回复 OK", "-Q"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
