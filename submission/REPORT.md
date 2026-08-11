# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Group Observability
- Repository URL: https://github.com/hoanglmv/Day13-K4-Observability
- Commit SHA cuối: 9c88e4b
- Thành viên và vai trò:
  - Thành viên 1 - Nguyễn Đăng Tuyên (2A202601622): Logging, correlation ID và PII (`app/logging_config.py`, `app/middleware.py`, `app/main.py`, `app/pii.py`)
  - Thành viên 2 - Vũ Ngọc Hùng (2A202601722): Tracing và Prompt Versioning (`app/tracing.py`, `app/prompt_management.py`, `app/agent.py`, Langfuse)
  - Thành viên 3 - Lê Mai Việt Hoàng (2A202601230): Dashboard, SLO, Alert và tổng hợp báo cáo (`config/dashboard.yaml`, `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`, `submission/REPORT.md`)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: >= 10 traces
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `config/dashboard.yaml` (Validator 6/6 panels đạt chuẩn contract)

## 3. Logging và tracing

- Evidence correlation ID: Header `X-Correlation-ID` và trường `correlation_id` được truyền xuyên suốt trong JSON log.
- Evidence PII redaction: Thông tin nhạy cảm (Email, Phone, Card Number) được che mờ (redact) qua `app/pii.py`.
- Evidence trace waterfall: Langfuse Tracing thể hiện chi tiết luồng span từ API middleware -> Agent -> LLM Call / RAG Retrieval.
- Giải thích một span đáng chú ý: Span `agent_execution` theo dõi toàn bộ chu kỳ xử lý của AI agent bao gồm prompt retrieval, execution và quality score calculation.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `v1` (label: `production`)
- Version/label candidate: `v2` (label: `candidate`)
- Trace ID của mỗi version: Trace ID liên kết đúng metadata `prompt_name`, `prompt_label`, `prompt_version`.
- Bằng chứng đổi label hoặc rollback: Minh hoạ thao tác đổi label `production` từ `v2` về `v1` trên Langfuse console khi phát hiện sự cố.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ (6/6 panel có trong dashboard contract).
- Evidence dashboard:
  - Panel 1: Latency percentiles (P50, P95, P99, threshold P95 <= 3000ms).
  - Panel 2: Request traffic (count, rate per minute).
  - Panel 3: Error rate and breakdown (error rate pct <= 2%, breakdown theo error_type).
  - Panel 4: Cost over time (sum by 1m, total budget <= 2.5 USD).
  - Panel 5: Input and output tokens (tokens_in, tokens_out, threshold sum <= 50,000 tokens).
  - Panel 6: Quality proxy (mean quality score >= 0.75).
- SLO đã chọn và lý do:
  - `latency_p95_ms` <= 3000ms: Đảm bảo thời gian phản hồi ứng dụng AI mượt mà cho trải nghiệm người dùng.
  - `error_rate_pct` <= 2%: Giữ tính ổn định và khả dụng cao cho hệ thống API.
  - `daily_cost_usd` <= 2.5 USD: Kiểm soát ngân sách gọi dịch vụ LLM trong hạn mức cho phép.
  - `quality_score_avg` >= 0.75: Đảm bảo độ chính xác và giá trị hữu ích của câu trả lời sinh bởi AI.
- Alert rules và runbook: Đã hoàn thiện cấu hình 3 alert rules trong `config/alert_rules.yaml` và hướng dẫn xử lý sự cố chi tiết trong `docs/alerts.md` cho các trường hợp `HighLatencyP95`, `HighErrorRate`, và `LowQualityScore`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: Latency P95 tăng đột biến vượt ngưỡng 2000ms (đạt ~2651ms) đối với feature `monitoring` trong quá trình load test challenge.
- Trace ID liên quan: Trace ID `req-abc99f97` (Langfuse trace ghi nhận span `rag_retrieval` bị nghẽn kéo dài 2500ms).
- Log line/correlation ID liên quan: `correlation_id`: `req-abc99f97` | Log line: `{"service": "api", "latency_ms": 2651, "tokens_in": 45, "tokens_out": 162, "cost_usd": 0.002565, "quality_score": 0.9, "payload": {"answer_preview": "Starter answer..."}, "event": "response_sent", "user_id_hash": "6b83e74c0874", "env": "dev", "model": "claude-sonnet-4-5", "correlation_id": "req-abc99f97", "feature": "monitoring", "session_id": "k4-challenge-s04", "level": "info", "ts": "2026-08-11T10:19:06.556730Z"}`
- Root cause: Cổ chai truy xuất dữ liệu RAG (`rag_slow` incident injection trong `app/mock_rag.py` làm tăng độ trễ 2500ms ở bước `rag_retrieval` cho các query thuộc feature `monitoring`).
- Fix action: Tắt incident `rag_slow` qua endpoint `/incidents/rag_slow/disable` (chạy `python scripts/inject_incident.py --disable`), đưa độ trễ span `rag_retrieval` trở lại mức bình thường (<10ms).
- Preventive measure: Bổ sung Circuit Breaker cho RAG retrieval, thiết lập timeout tối đa cho span `rag_retrieval` (ví dụ 1000ms), áp dụng caching kết quả retrieval cho các truy vấn phổ biến và kích hoạt Alert Rule `HighLatencyP95` khi P95 latency vượt ngưỡng 2000ms.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Đăng Tuyên (2A202601622) | Logging, correlation ID & PII redaction | Commit trên branch `hoanglmv` | Cách cấu hình structlog dạng JSON, truyền correlation ID qua FastAPI middleware và che thông tin nhạy cảm (PII) bằng regex. |
| Vũ Ngọc Hùng (2A202601722) | Tracing & Prompt Versioning | Commit trên branch `hoanglmv` | Cách tích hợp Langfuse Tracing SDK, gắn metadata vào trace và quản lý/rollback prompt version linh hoạt với label. |
| Lê Mai Việt Hoàng (2A202601230) | Dashboard, SLO, Alert Rules, Runbook & Báo cáo tổng hợp | Commit trên branch `hoanglmv` | Cách thiết kế Dashboard 6 nhóm chỉ số, định nghĩa SLO/SLI chuẩn, viết Alert Rules theo triệu chứng (symptom-based) và quy trình điều tra vết sự cố theo luồng Metrics → Traces → Logs. |




