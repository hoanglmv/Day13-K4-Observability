# Runbook và Hướng dẫn Xử lý Alert

Mỗi alert được thiết kế dựa trên triệu chứng ảnh hưởng trực tiếp tới người dùng và chỉ số SLO (symptom-based), quy định rõ các bước điều tra theo luồng **Metrics → Traces → Logs**.

---

## Alert 1: HighLatencyP95

- **Tên:** HighLatencyP95
- **Severity:** Warning
- **SLI/SLO liên quan:** `latency_p95_ms` (Objective <= 3000ms, Target 99.5%)
- **Điều kiện và thời gian duy trì:** `p95(latency_ms) > 3000ms` duy trì trong 5 phút liên tục.
- **Ảnh hưởng tới người dùng:** Người dùng gặp phản hồi rất chậm từ ứng dụng AI, có thể bị timeout giao diện hoặc trải nghiệm suy giảm nặng.
- **Ba bước kiểm tra đầu tiên:**
  1. **Metrics:** Kiểm tra panel `Latency percentiles` trên Dashboard để xác nhận chỉ số P95 vượt ngưỡng 3000ms và theo dõi biểu đồ traffic/concurrency.
  2. **Traces:** Mở Langfuse Tracing, lọc các trace có tổng duration lớn hơn 3000ms. So sánh thời gian thực thi của từng span (`agent_execution`, `rag_retrieval`, `llm_call`) để khoanh vùng bottleneck.
  3. **Logs:** Tra cứu JSON log theo `correlation_id` của các request bị chậm trong `data/logs.jsonl`, kiểm tra chi tiết tham số đầu vào và thông điệp cảnh báo/retry.
- **Mitigation tạm thời:**
  - Nếu sự cố do tính năng RAG bị nghẽn (`rag_slow`), tạm thời tắt tính năng hoặc điều chỉnh số lượng retrieved documents.
  - Nếu do Prompt Candidate mới gây tốn thời gian sinh từ, thực hiện rollback prompt về phiên bản `production` trước đó.
  - Điều chỉnh hạ rate limit hoặc tăng tài nguyên xử lý API.
- **Owner:** `@devops-oncall`

---

## Alert 2: HighErrorRate

- **Tên:** HighErrorRate
- **Severity:** Critical
- **SLI/SLO liên quan:** `error_rate_pct` (Objective <= 2%, Target 99.0%)
- **Điều kiện và thời gian duy trì:** `error_rate_pct > 2%` duy trì trong 5 phút liên tục.
- **Ảnh hưởng tới người dùng:** Người dùng liên tục gặp câu trả lời lỗi HTTP 5xx, timeout hoặc thông báo gián đoạn dịch vụ.
- **Ba bước kiểm tra đầu tiên:**
  1. **Metrics:** Kiểm tra panel `Error rate and breakdown` trên Dashboard để biết tỷ lệ lỗi tổng thể và phân loại `error_type` chính (VD: `llm_timeout`, `pii_redaction_failure`, `validation_error`).
  2. **Traces:** Mở Langfuse Tracing, lọc các trace gắn tag `status=ERROR` để xem chi tiết nơi xảy ra exception và luồng gọi downstream.
  3. **Logs:** Tra cứu các sự kiện `request_failed` trong `data/logs.jsonl` bằng `correlation_id` để kiểm tra stack trace và nguyên nhân gốc.
- **Mitigation tạm thời:**
  - Chuyển hướng kết nối sang provider LLM dự phòng nếu downstream API gặp sự cố.
  - Bật chế độ degraded mode (trả về fallback response chuẩn thay vì báo lỗi hệ thống 500).
- **Owner:** `@devops-oncall`

---

## Alert 3: LowQualityScore

- **Tên:** LowQualityScore
- **Severity:** Warning
- **SLI/SLO liên quan:** `quality_score_avg` (Objective >= 0.75, Target 95.0%)
- **Điều kiện và thời gian duy trì:** `mean(quality_score) < 0.75` duy trì trong 15 phút liên tục.
- **Ảnh hưởng tới người dùng:** Chất lượng câu trả lời từ AI suy giảm rõ rệt, kết quả không đáp ứng được yêu cầu hoặc chứa thông tin sai lệch.
- **Ba bước kiểm tra đầu tiên:**
  1. **Metrics:** Kiểm tra panel `Quality proxy` trên Dashboard để đánh giá xu hướng suy giảm điểm chất lượng trung bình.
  2. **Traces:** Kiểm tra Langfuse Prompt Management để kiểm tra xem vừa có đợt cập nhật prompt version / label mới nào được triển khai hay không.
  3. **Logs:** So sánh thông tin metadata trong trace và log (`prompt_name`, `prompt_label`, `prompt_version`) giữa các request có điểm chất lượng cao và thấp để xác nhận root cause.
- **Mitigation tạm thời:**
  - Thực hiện rollback ngay lập tức label `production` về `prompt_version` cũ có điểm chất lượng ổn định.
  - Cập nhật thêm validation guardrails cho câu trả lời của AI.
- **Owner:** `@ai-team`

