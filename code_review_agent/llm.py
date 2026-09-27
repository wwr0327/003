"""Standard-library client for a Chat Completions compatible model service."""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class ModelError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ChatClient:
    def __init__(self, api_key, base_url, model, timeout=60, retries=2, opener=None, sleep=time.sleep):
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("LLM_BASE_URL 必须是无认证信息、查询参数或片段的 HTTP(S) 地址")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("远程模型服务必须使用 HTTPS")
        if not api_key.strip() or not model.strip():
            raise ValueError("请设置 LLM_API_KEY 和 LLM_MODEL")
        self.api_key, self.model = api_key, model
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.timeout, self.retries = timeout, retries
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.sleep = sleep

    @classmethod
    def from_env(cls):
        return cls(os.getenv("LLM_API_KEY", ""), os.getenv("LLM_BASE_URL", ""),
                   os.getenv("LLM_MODEL", ""))

    def complete(self, messages, tools):
        payload = json.dumps({"model": self.model, "messages": messages,
                              "tools": tools, "tool_choice": "auto"}).encode("utf-8")
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(self.url, data=payload, headers={
                "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise ModelError("模型响应过大")
                result = json.loads(raw)
                choice = result["choices"][0]
                if choice.get("finish_reason") in {"length", "content_filter"}:
                    raise ModelError("模型响应被截断或过滤，请缩小问题范围")
                message = choice["message"]
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    raise ValueError("invalid message")
                return {k: message[k] for k in ("role", "content", "tool_calls") if k in message}
            except urllib.error.HTTPError as exc:
                retryable = exc.code in {408, 429, 500, 502, 503, 504}
                exc.close()
                if not retryable or attempt == self.retries:
                    raise ModelError(f"模型服务返回 HTTP {exc.code}，请检查配置、额度或服务状态") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == self.retries:
                    raise ModelError("模型网络请求失败或超时，请检查网络和服务地址") from None
            except (ValueError, KeyError, IndexError, TypeError):
                raise ModelError("模型响应格式无效，需要支持工具调用的 Chat Completions 接口") from None
            self.sleep(min(2 ** attempt, 8))
