"""
Module prompt_management - Thành viên 2: Tracing & Prompt Versioning
Nhiệm vụ: Quản lý version, label và lấy prompt template từ Langfuse hoặc fallback về prompt local.
Hỗ trợ rollback version qua biến môi trường LANGFUSE_PROMPT_LABEL.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Template prompt mặc định dùng local
DEFAULT_PROMPT_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"


@dataclass(frozen=True)
class ResolvedPrompt:
    """Đội chứa thông tin prompt đã được giải mã (name, label, version, source)."""
    text: str
    name: str
    label: str
    version: str
    source: str
    managed_prompt: Any | None = None
    fetch_error: str | None = None


def _compile_local_prompt(*, feature: str, docs: list[str], message: str) -> str:
    """Tạo prompt text từ template local khi không kết nối được Langfuse."""
    return (
        DEFAULT_PROMPT_TEMPLATE.replace("{{feature}}", feature)
        .replace("{{docs}}", "\n".join(docs))
        .replace("{{message}}", message)
    )


def resolve_prompt(
    client: Any,
    *,
    feature: str,
    docs: list[str],
    message: str,
    enabled: bool,
) -> ResolvedPrompt:
    """
    Xác định và biên dịch prompt template.
    1. Đọc name & label từ biến môi trường (mặc định: LANGFUSE_PROMPT_NAME=day13-chat, LANGFUSE_PROMPT_LABEL=production).
    2. Nếu enabled=True, gọi client.get_prompt(...) từ Langfuse.
    3. Nếu gặp lỗi hoặc Langfuse báo fallback, chuyển sang dùng prompt local và ghi rõ source/fetch_error.
    """
    name = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    label = os.getenv("LANGFUSE_PROMPT_LABEL", "production")
    text = _compile_local_prompt(feature=feature, docs=docs, message=message)

    if enabled:
        try:
            # Lấy prompt managed từ Langfuse dựa trên name và label
            managed_prompt = client.get_prompt(
                name,
                label=label,
                type="text",
                fallback=DEFAULT_PROMPT_TEMPLATE,
                cache_ttl_seconds=60,
                fetch_timeout_seconds=2,
                max_retries=0,
            )
            # Kiểm tra nếu SDK trả về fallback
            if getattr(managed_prompt, "is_fallback", False):
                return ResolvedPrompt(
                    text=text,
                    name=name,
                    label=label,
                    version="local-v1",
                    source="local-fallback",
                    fetch_error="LangfuseFallback",
                )
            # Biên dịch prompt lấy từ Langfuse thành công
            return ResolvedPrompt(
                text=managed_prompt.compile(
                    feature=feature,
                    docs="\n".join(docs),
                    message=message,
                ),
                name=name,
                label=label,
                version=str(managed_prompt.version),
                source="langfuse",
                managed_prompt=managed_prompt,
            )
        except Exception as exc:  # Langfuse là dependency ngoài; app phải có fallback local
            return ResolvedPrompt(
                text=text,
                name=name,
                label=label,
                version="local-v1",
                source="local-fallback",
                fetch_error=type(exc).__name__,
            )

    # Khi không bật Tracing
    return ResolvedPrompt(
        text=text,
        name=name,
        label=label,
        version="local-v1",
        source="local",
    )

