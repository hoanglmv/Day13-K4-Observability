"""
Module tracing - Thành viên 2: Tracing & Prompt Versioning
Nhiệm vụ: Cấu hình và tích hợp Langfuse Tracing SDK vào ứng dụng.
Cung cấp fallback an toàn với _DummyClient khi môi trường chưa cấu hình key.
"""

from __future__ import annotations

import os
from typing import Any

# Khởi tạo SDK Langfuse. Nếu chưa cài đặt package, dùng Dummy class để ứng dụng không bị crash.
try:
    # pyrefly: ignore [missing-import]
    from langfuse import get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    # Decorator giả định khi không có Langfuse SDK
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    # Dummy Client giả lập các hàm cập nhật trace/generation của Langfuse
    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    """Lấy Langfuse client instance hiện tại."""
    return get_client()


def tracing_enabled() -> bool:
    """
    Kiểm tra xem Tracing có hợp lệ không.
    Điều kiện: SDK đã được cài đặt VÀ có đầy đủ cả PUBLIC_KEY và SECRET_KEY trong môi trường.
    """
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )

