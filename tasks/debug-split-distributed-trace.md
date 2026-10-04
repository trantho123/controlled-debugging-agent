# Task: Khắc Phục Lỗi Split Distributed Trace Giữa Các Weather Services

## 1. Mô Tả Vấn Đề & Hiện Tượng Quan Sát Được (Observed Symptom)
Trong hệ thống truy vấn thời tiết dạng container hiện tại, toàn bộ test suite (unit/integration) đều PASS và các nghiệp vụ hoạt động bình thường:
- Gọi MCP tool `get_weather(city="Da Nang")` trả về đúng payload thời tiết mong đợi:
  ```json
  {
    "city": "Da Nang",
    "temperature": 30,
    "condition": "Sunny"
  }
  ```
- Tuy nhiên, distributed tracing trong Jaeger bị lỗi: thay vì ghi nhận toàn bộ luồng request (`weather-mcp-server` ➔ `weather-graphql-service` ➔ `weather-rest-service`) trong một distributed trace duy nhất, Jaeger lại hiển thị các traces bị tách rời (disconnected) với các Trace ID khác nhau.

---

## 2. Hành Vi Mong Đợi (Expected Behavior)
Khi một MCP client gọi `get_weather`:
1. Jaeger phải ghi nhận một distributed trace thống nhất duy nhất (một Trace ID duy nhất) chứa các spans từ cả ba service tham gia:
   - `weather-mcp-server`
   - `weather-graphql-service`
   - `weather-rest-service`
2. Phân cấp quan hệ span parent-child phải phản ánh đúng luồng thực thi:
   `weather-mcp-server` ➔ `weather-graphql-service` ➔ `weather-rest-service`.
3. Số lượng span chính xác và tên span nội bộ không bị ràng buộc cứng, nhưng quan hệ nhân quả (causal relationship) giữa các service phải rõ ràng và liên tục.

---

## 3. Phạm Vi Công Việc (Scope of Work)

### Investigation Scope
Kỹ sư/agent debug được phép điều tra và quan sát:
- `services/mcp-server/**`
- `services/graphql-service/**`
- `services/weather-rest/**`
- `compose.yaml`
- Runtime container logs và cấu hình môi trường
- Jaeger query UI / API endpoints (`http://localhost:16686`)

### Modification Scope
- **Initial Modification Scope**: **KHÔNG (0 files)**.
- Quyền điều tra (Investigation permission) KHÔNG đồng nghĩa với quyền chỉnh sửa (Modification permission).
- Không được phép tạo, sửa hoặc xóa bất kỳ file nào cho đến khi quá trình điều tra Root Cause hoàn tất, đề xuất phương án sửa tối thiểu được xây dựng và có sự phê duyệt rõ ràng từ con người (Human Approval).

---

## 4. Ràng Buộc & Bất Biến (Constraints & Invariants)
- **Bảo toàn Business Logic**: Giá trị trả về, API contracts và HTTP payloads giữa tất cả các services phải giữ nguyên.
- **Không thay đổi Tests**: Các test hiện có trong `test_app.py` của các service không được làm suy yếu hoặc chỉnh sửa chỉ để pass.
- **Thay đổi tối thiểu**: Tránh refactor không cần thiết hoặc thêm third-party dependencies.
- **Bảo toàn Docker Topology**: Không thay đổi ánh xạ port, tên service hoặc kiến trúc container tổng thể trong `compose.yaml` trừ khi trực tiếp cần thiết cho việc sửa tracing.

---

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
Task chỉ được coi là hoàn thành khi đáp ứng toàn bộ các tiêu chí sau:
1. **Regression Tests**: Toàn bộ automated tests hiện có trên cả ba services tiếp tục PASS.
2. **Business Functionality**: Lệnh gọi `get_weather("Da Nang")` qua live MCP client tiếp tục trả về chính xác dữ liệu JSON mong đợi.
3. **Unified Trace trong Jaeger**: Một request `get_weather` mới sinh ra một distributed trace chứa cả ba services:
   - `weather-mcp-server`
   - `weather-graphql-service`
   - `weather-rest-service`
4. **Single Trace ID**: Các spans từ cả ba services thuộc cùng một Trace ID duy nhất.
5. **Causal Hierarchy**: Quan hệ span trong Jaeger thể hiện tính liên tục parent-child đúng theo luồng: MCP ➔ GraphQL ➔ Weather REST.
6. **Không có thay đổi ngoài lề**: Chỉ cho phép những thay đổi trực tiếp cần thiết để giải quyết vấn đề distributed tracing được quan sát.

---

## 6. Bằng Chứng Yêu Cầu (Required Evidence)
Bất kỳ khẳng định task đã hoàn thành nào cũng phải đi kèm bằng chứng thực thi cụ thể:
1. **Kết quả Test**: Output thực thi sạch từ `pytest` cho cả 3 services.
2. **MCP Live Response**: Payload response thực tế nhận được khi gọi trực tiếp `get_weather("Da Nang")`.
3. **Bằng chứng Jaeger Trace**:
   - Trace ID của trace thống nhất.
   - Danh sách tên tất cả các service tham gia trong trace đó.
   - Phân cấp spans thể hiện liên kết parent-child qua ranh giới của 3 services.
4. **Bằng chứng Git**:
   - Danh sách chính xác các files đã sửa.
   - `git diff` sạch thể hiện thay đổi tối thiểu.

---

## 7. Định Nghĩa Hoàn Thành (Definition of Done - DoD)
**Khẳng Định (Claim) + Bằng Chứng Thực Nghiệm (Verification Evidence) = DONE**
Không được đánh dấu task là hoàn thành chỉ dựa trên suy đoán hoặc việc đọc code. Giải pháp phải được chứng minh hoạt động end-to-end trên môi trường live đang chạy cùng với kết quả xác thực trace thực tế từ Jaeger.
