"""模型发现服务：从 API 端点获取可用模型列表"""

import json
import threading
from typing import List, Optional

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin

# 请求超时（秒）
DISCOVERY_TIMEOUT = 5

# 缓存：endpoint -> (models list, error message or None)
_cache: dict = {}
_cache_lock = threading.Lock()


def _normalize_endpoint(endpoint: str) -> str:
    """确保 endpoint 以 / 结尾，便于拼接路径"""
    s = (endpoint or "").strip().rstrip("/")
    return s if s else ""


def _parse_models_from_response(data) -> List[str]:
    """从 API 响应中解析模型 ID 列表"""
    if data is None:
        return []
    if isinstance(data, list):
        return [str(m) if not isinstance(m, dict) else (m.get("id") or m.get("model_id") or str(m)) for m in data if m]
    if isinstance(data, dict):
        # OpenAI: {"data": [{"id": "gpt-4"}, ...]}
        if "data" in data and isinstance(data["data"], list):
            return _parse_models_from_response(data["data"])
        # 自定义: {"models": ["m1", "m2"]}
        if "models" in data and isinstance(data["models"], list):
            return [str(m) for m in data["models"] if m]
        # 单键为列表
        for key in ("data", "models", "model_list"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                if items and isinstance(items[0], dict):
                    return [str(x.get("id") or x.get("model_id") or x) for x in items if x]
                return [str(x) for x in items if x]
    return []


def _fetch_url(url: str, api_key: str) -> Optional[dict]:
    """同步 GET 请求，返回解析后的 JSON 或 None"""
    try:
        req = Request(url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=DISCOVERY_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body) if body.strip() else None
    except (URLError, HTTPError, json.JSONDecodeError, OSError):
        return None


def get_models_sync(
    endpoint: str,
    api_key: str,
    use_cache: bool = True,
    models_url: Optional[str] = None,
) -> List[str]:
    """
    同步获取端点可用模型列表。
    若提供 models_url 则优先请求该 URL（可为完整 URL 或相对路径如 /v1/models）；
    否则尝试 /v1/models 和 /models。
    支持缓存。
    """
    base = _normalize_endpoint(endpoint)
    if not base or not (api_key or "").strip():
        return []

    custom_url = (models_url or "").strip()
    if custom_url:
        if custom_url.startswith("http://") or custom_url.startswith("https://"):
            paths_to_try = [custom_url]
        else:
            path = custom_url if custom_url.startswith("/") else f"/{custom_url}"
            paths_to_try = [f"{base.rstrip('/')}{path}"]
    else:
        if base.rstrip("/").endswith("/v1"):
            paths_to_try = [f"{base.rstrip('/')}/models"]
        else:
            paths_to_try = [f"{base}/v1/models", f"{base}/models"]

    cache_key = f"{base}|{bool(api_key)}|{custom_url}"
    if use_cache:
        with _cache_lock:
            if cache_key in _cache:
                models, _ = _cache[cache_key]
                return list(models) if models is not None else []

    models = []
    for path in paths_to_try:
        data = _fetch_url(path, api_key)
        if data is not None:
            models = _parse_models_from_response(data)
            if models:
                break

    with _cache_lock:
        _cache[cache_key] = (models, None)

    return list(models)


def invalidate_cache(endpoint: Optional[str] = None):
    """清除缓存。endpoint 为 None 时清空全部。"""
    with _cache_lock:
        if endpoint is None:
            _cache.clear()
        else:
            base = _normalize_endpoint(endpoint)
            keys = [k for k in _cache if k.startswith(base + "|")]
            for k in keys:
                del _cache[k]
