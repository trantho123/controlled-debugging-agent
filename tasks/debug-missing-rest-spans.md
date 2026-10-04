# Task: Khắc Phục Lỗi Thiếu Downstream REST Spans Trong Distributed Trace

## 1. Mô Tả Vấn Đề & Hiện Tượng Quan Sát Được (Observed Symptom)
Trong hệ thống truy vấn thời tiết containerized hiện tại, logic nghiệp vụ vẫn hoạt động bình thường:
- Lệnh gọi MCP tool `get_weather(city="Da Nang")` trả về đúng payload thời tiết mong đợi:
  ```json
  {
    "city": "Da Nang",
    "temperature": 30,
    "condition": "Sunny"
  }
  ```
- Tuy nhiên, distributed tracing trong Jaeger bị phân mảnh (fragmented): hệ thống không ghi nhận được một distributed trace thống nhất xuyên suốt toàn bộ luồng request qua các microservices (`weather-mcp-server` ➔ `weather-graphql-service` ➔ `weather-rest-service`).

---

## 2. Hành Vi Mong Đợi (Expected Behavior)
Khi một client gọi MCP tool `get_weather`:
1. Jaeger phải ghi nhận một distributed trace duy nhất (một Trace ID duy nhất) chứa đầy đủ các spans từ cả ba service tham gia:
   - `weather-mcp-server`
   - `weather-graphql-service`
   - `weather-rest-service`
2. Phân cấp quan hệ span parent-child phản ánh đúng luồng thực thi:
   `weather-mcp-server` ➔ `weather-graphql-service` ➔ `weather-rest-service`.
3. Số lượng span chính xác và tên span nội bộ không bị ép buộc cứng, nhưng quan hệ nhân quả (causal continuity) qua cả 3 services phải được thể hiện đầy đủ.

---

## 3. Phạm Vi Công Việc (Scope of Work)

### Investigation Scope (READ-ONLY)
Kỹ sư/agent được phép điều tra và quan sát:
- `services/mcp-server/**`
- `services/graphql-service/**`
- `services/weather-rest/**`
- `compose.yaml`
- Runtime logs và cấu hình môi trường
- Jaeger query UI / API (`http://localhost:16686`)
- Git history (`git log`, `git status`, `git diff`)

### Initial Modification Scope
- **Phạm vi cho phép**: `services/mcp-server/**`
- Mọi repository file nằm ngoài phạm vi trên đều là **READ-ONLY**.
- Modification Scope chỉ có thể được thay đổi sau khi có **sự phê duyệt rõ ràng từ Human (explicit Human Approval)**.

---

## 4. Ràng Buộc & Bất Biến (Constraints & Invariants)
- **Bảo toàn Business Logic**: Giá trị trả về, API contracts và HTTP payloads giữa tất cả các services phải giữ nguyên.
- **Không thay đổi Tests**: Không sửa đổi các file test trong `test_app.py` để ép pass.
- **Thay đổi tối thiểu**: Tránh refactoring không liên quan hoặc thêm third-party dependencies không cần thiết.
- **Bảo toàn Architecture & Topology**: Không thay đổi port mapping, tên service hoặc cấu trúc container trong `compose.yaml` nếu chưa được approve.
- **Không suy diễn**: Không được dùng code inspection đơn thuần để kết luận hoặc tuyên bố hoàn thành task.

---

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
Task chỉ được coi là hoàn thành khi đáp ứng toàn bộ các tiêu chí sau:
1. **Regression Tests**: Toàn bộ automated tests hiện có trên cả ba services tiếp tục PASS.
2. **Business Functionality**: Lệnh gọi `get_weather("Da Nang")` qua live MCP client tiếp tục trả về chính xác dữ liệu JSON mong đợi.
3. **Unified Trace trong Jaeger**: Một request `get_weather` MỚI sinh ra một distributed trace chứa đầy đủ cả ba services:
   - `weather-mcp-server`
   - `weather-graphql-service`
   - `weather-rest-service`
4. **Single Trace ID**: Các spans từ cả ba services thuộc cùng một Trace ID duy nhất.
5. **Causal Continuity**: Quan hệ span trong Jaeger thể hiện tính liên tục parent-child đúng theo luồng: MCP ➔ GraphQL ➔ Weather REST.
6. **Không có thay đổi ngoài lề**: Không có các chỉnh sửa không liên quan (unrelated modifications).

---

## 6. Bằng Chứng Nghiệm Thu Bắt Buộc (Required Evidence)
Bất kỳ kết luận nào về việc hoàn thành task đều phải đi kèm bằng chứng thực thi thực tế:
1. **Kết quả Test**: Output thực thi sạch từ test suite hiện có cho cả 3 services.
2. **MCP Live Response**: Payload response thực tế nhận được khi gọi trực tiếp `get_weather("Da Nang")`.
3. **Bằng chứng Jaeger Trace**:
   - Trace ID MỚI của trace thống nhất.
   - Danh sách tên tất cả các participating services.
   - Phân cấp spans thể hiện liên kết parent-child qua 3 services.
4. **Bằng chứng Git**:
   - `git diff` sạch thể hiện thay đổi tối thiểu.
   - `git status` xác nhận phạm vi thay đổi.

---

## 7. Định Nghĩa Hoàn Thành (Definition of Done - DoD)
**Khẳng Định (Claim) + Bằng Chứng Thực Nghiệm (Verification Evidence) = DONE**
Mọi khẳng định PASS bắt buộc phải có output thực thi từ runtime. Không có bằng chứng thực thi thì không được đánh dấu hoàn thành.
