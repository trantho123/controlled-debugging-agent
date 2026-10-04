# Controlled Debugging Protocol — Operating Guidelines

Tài liệu này quy định quy trình bắt buộc (HOW) dành cho Coding Agent khi nhận nhiệm vụ điều tra và sửa lỗi. Mọi hành vi vi phạm quy trình này đều bị coi là lỗi vi phạm kỷ luật kỹ thuật.

---

## 1. Nguyên Tắc Cốt Lõi (Core Principles)

1. **Capability != Authority (Khả năng không đồng nghĩa với Quyền hạn)**:
   Việc agent sở hữu công cụ sửa file, chạy lệnh terminal hay can thiệp container không có nghĩa agent được phép tùy tiện sử dụng chúng. Quyền hạn của agent được xác định nghiêm ngặt bởi State hiện tại và Modification Scope đã được Human phê duyệt.
2. **Evidence > Assumption (Bằng chứng thực nghiệm cao hơn Giả định)**:
   Agent được phép hình thành giả thuyết (hypothesis) trong quá trình INVESTIGATE, nhưng bắt buộc phải kiểm chứng giả thuyết bằng Bằng Chứng (Evidence) thực tế (logs, traces, test outputs, runtime observations). Giả thuyết chưa được kiểm chứng không được phép gọi là Root Cause và không được dùng làm căn cứ để IMPLEMENT.
3. **No Speculative Editing (Cấm sửa code thử nghiệm)**:
   Không được sửa bất kỳ dòng code nào khi chưa chứng minh được nguyên nhân gốc rễ và chưa nhận được sự phê duyệt rõ ràng từ Human.
4. **Claim + Evidence = PASS**:
   Không bao giờ được kết luận một tiêu chí đạt (PASS) chỉ qua việc đọc code. Mọi khẳng định PASS bắt buộc phải đi kèm output thực thi thực tế.

---

## 2. Finite State Machine (FSM)

Agent bắt buộc phải vận hành theo đúng chu trình trạng thái tuần tự dưới đây:

```
[INTAKE] ➔ [INVESTIGATE] ➔ [ROOT_CAUSE_GATE] ➔ [PLAN] ➔ [HUMAN_APPROVAL] ➔ [IMPLEMENT] ➔ [VERIFY] ➔ [REPORT]
                 ▲                                                                          │
                 └────────────────────────── [VERIFY FAIL] ─────────────────────────────────┘
```

---

### State 1: INTAKE
- **Purpose**: Tiếp nhận và đồng hóa toàn bộ yêu cầu, phạm vi và ràng buộc của nhiệm vụ từ Task Artifact.
- **Allowed Actions**:
  - Đọc file Task Artifact được chỉ định.
  - Phân tích và liệt kê: Problem Description, Expected Behavior, Investigation Scope, Modification Scope, Constraints, Acceptance Criteria, Required Evidence.
- **Forbidden Actions**:
  - Không đọc source code để bắt đầu debug trước khi hiểu task.
  - Không sửa file, không chạy lệnh runtime.
  - Không tự ý suy diễn hoặc tự điền các yêu cầu còn thiếu.
- **Exit Criteria**:
  - Đã xác nhận đầy đủ các thông tin cốt lõi của task.
  - Nếu Task Artifact có mâu thuẫn hoặc thiếu thông tin quan trọng: **STOP ➔ REQUEST CLARIFICATION**.
- **Transition**: Chuyển sang **INVESTIGATE**.

---

### State 2: INVESTIGATE (READ-ONLY)
- **Purpose**: Quan sát, tái lập lỗi (reproduce), thu thập bằng chứng và cô lập ranh giới lỗi mà không làm biến đổi hệ thống.
- **Allowed Actions**:
  - Đọc source code và file cấu hình trong Investigation Scope.
  - Kiểm tra trạng thái Git (`git status`, `git log`, `git diff`).
  - Đọc runtime logs, container logs, query observability systems (metrics, traces, dashboards).
  - Chạy existing test suites và các lệnh kiểm tra trạng thái runtime hiện có.
  - Thực thi request kiểm thử để tái lập lỗi (reproduce).
  - Hình thành các giả thuyết (hypotheses) và kiểm chứng chúng bằng bằng chứng quan sát thực nghiệm.
- **Forbidden Actions**:
  - **TUYỆT ĐỐI CẤM**: Tạo mới, chỉnh sửa, đổi tên hoặc xóa bất kỳ file nào trong repository.
  - Không sửa existing tests.
  - Không cài đặt thêm dependencies/packages.
  - Không refactor code.
  - Không thử nghiệm các bản vá lỗi (trial-and-error fixes).
  - Không thay đổi runtime configuration nhằm mục đích "thử sửa".
- **Exit Criteria**: Thu thập đầy đủ bằng chứng thực nghiệm để vượt qua ROOT_CAUSE_GATE.
- **Transition**: Chuyển sang **ROOT_CAUSE_GATE**.

---

### State 3: ROOT_CAUSE_GATE
- **Purpose**: Chốt chặn kiểm định chất lượng điều tra trước khi lập kế hoạch sửa lỗi.
- **Verification Checklist (Tất cả phải có bằng chứng)**:
  1. [ ] Triệu chứng lỗi đã được tái lập hoặc có bằng chứng thực nghiệm tin cậy xác nhận lỗi đang tồn tại.
  2. [ ] Hành vi mong đợi (Expected Behavior) được hiểu rõ ràng.
  3. [ ] Ranh giới xảy ra lỗi (Failure Boundary) đã được khoanh vùng chính xác.
  4. [ ] Nguyên nhân gốc rễ (Root Cause) được xác định rõ ràng, có cơ chế kỹ thuật cụ thể.
  5. [ ] Có bằng chứng thực nghiệm (log/trace/code logic) chứng minh trực tiếp cho Root Cause.
  6. [ ] Đã định hình được hướng giải quyết tối thiểu (minimal fix direction).
- **Rule**:
  - Nếu checklist thiếu dù chỉ 1 mục: **CẤM sang PLAN ➔ BẮT BUỘC quay lại INVESTIGATE**.
  - Giả thuyết chưa qua kiểm chứng bằng bằng chứng thực nghiệm không được coi là Root Cause.
- **Transition**: Khi đủ 6 điều kiện, chuyển sang **PLAN**.

---

### State 4: PLAN
- **Purpose**: Đề xuất phương án sửa lỗi tối thiểu, bám sát constraints và thiết kế quy trình nghiệm thu.
- **Allowed Actions**:
  - Soạn thảo kế hoạch chi tiết gồm 6 phần:
    1. **Root Cause**: Tóm tắt nguyên nhân gốc rễ kèm bằng chứng đã thu thập.
    2. **Proposed Change**: Mô tả chính xác thay đổi cần thực hiện.
    3. **Files to Modify**: Danh sách cụ thể các file sẽ chỉnh sửa (đây sẽ là Modification Scope đề xuất).
    4. **Why This Change**: Giải thích vì sao thay đổi này giải quyết được Root Cause mà không gây tác dụng phụ.
    5. **Impact & Invariant Assessment**: Xác nhận giải pháp không vi phạm Constraints và Business Logic.
    6. **Verification Plan**: Các bước và lệnh cụ thể sẽ chạy để xác minh các Acceptance Criteria.
- **Forbidden Actions**:
  - **PLAN KHÔNG CẤP QUYỀN SỬA FILE**.
  - Không sửa file, không commit, không áp dụng thay đổi trước.
- **Exit Criteria**: Bản kế hoạch hoàn chỉnh sẵn sàng trình lên Human.
- **Transition**: Chuyển sang **HUMAN_APPROVAL**.

---

### State 5: HUMAN_APPROVAL (STOP GATE)
- **Purpose**: Trao quyền kiểm soát quyết định thay đổi cho Human.
- **Mandatory Action**:
  - Trình bày bản PLAN rõ ràng, súc tích.
  - **DỪNG LẠI (STOP)** và chờ đợi sự phê duyệt rõ ràng từ Human.
- **Rules of Approval**:
  - Chỉ được coi là APPROVED khi Human đưa ra sự chấp thuận rõ ràng (ví dụ: "Approved", "Đồng ý thực hiện").
  - Sự im lặng, câu hỏi làm rõ, yêu cầu thảo luận hoặc gợi ý KHÔNG được coi là approval.
  - Modification Scope chính thức sau approval CHỈ BAO GỒM các files đã được phê duyệt.
- **Transition**: Sau khi có Approval, chuyển sang **IMPLEMENT**.

---

### State 6: IMPLEMENT
- **Purpose**: Thực hiện chính xác và tối thiểu thay đổi đã được phê duyệt.
- **Allowed Actions**:
  - Chỉnh sửa đúng các files nằm trong Approved Modification Scope.
  - Thực hiện đúng phạm vi kỹ thuật đã cam kết trong Approved Plan.
  - Rebuild/restart các containers/components cần thiết để áp dụng code mới.
- **Forbidden Actions**:
  - Không sửa bất kỳ file nào ngoài Approved Modification Scope.
  - Không "tiện tay" dọn dẹp (cleanup), tối ưu hóa hoặc refactor code không liên quan.
  - Không sửa test để ép test pass.
  - Không thay đổi architecture, endpoints, data contracts hoặc dependencies.
  - Nếu phát hiện cần sửa thêm file ngoài scope: **SCOPE_CONFLICT ➔ DỪNG NGAY LẬP TỨC ➔ BÁO CÁO ➔ CHỜ HUMAN APPROVAL LẠI**.
- **Exit Criteria**: Mã nguồn đã được sửa theo đúng Approved Plan.
- **Transition**: Chuyển sang **VERIFY**.

---

### State 7: VERIFY
- **Purpose**: Thực thi kiểm định đa chiều để chứng minh lỗi đã được giải quyết và không phát sinh hồi quy (regression).
- **Allowed Actions**:
  - Chạy đầy đủ các bước trong Verification Plan.
  - Kiểm tra toàn bộ Acceptance Criteria từ Task Artifact.
  - Thu thập tất cả Required Evidence (test logs, live responses, telemetry/traces, git diff).
- **Rules on Failure (Xử lý khi VERIFY FAIL)**:
  - Nếu bất kỳ bước verification nào thất bại (FAIL):
    1. **DỪNG MỌI HÀNH ĐỘNG SỬA CODE (STOP MODIFICATION)**. Điều này không có nghĩa kết thúc phiên debugging, mà nhằm ngăn chặn hành vi sửa hú họa (trial-and-error).
    2. Ghi nhận đầy đủ bằng chứng thất bại (failure evidence).
    3. Thu hồi toàn bộ quyền hạn sửa đổi (Revoke Modification Authority).
    4. Quay trở lại trạng thái **INVESTIGATE (READ-ONLY)** để điều tra nguyên nhân sai lệch.
    5. Nếu quá trình điều tra tiếp theo dẫn đến một Root Cause hoặc Plan mới, agent **BẮT BUỘC** phải đi lại đầy đủ các bước:
       `ROOT_CAUSE_GATE ➔ PLAN ➔ HUMAN_APPROVAL`
       trước khi được phép thực hiện bất kỳ chỉnh sửa code nào tiếp theo.
- **Exit Criteria**: Toàn bộ Acceptance Criteria đều PASS với đầy đủ bằng chứng thực nghiệm.
- **Transition**: Chuyển sang **REPORT**.

---

### State 8: REPORT
- **Purpose**: Báo cáo kết quả minh bạch, đầy đủ bằng chứng nghiệm thu cho Human.
- **Required Report Structure**:
  1. **Root Cause**: Giải thích ngắn gọn nguyên nhân gốc rễ đã được xác nhận.
  2. **Changed Files & Git Diff**: Danh sách file đã sửa và toàn bộ `git diff`.
  3. **Verification Results**:
     - Kết quả chạy automated tests (kèm test count).
     - Kết quả gọi API/Live E2E (kèm actual payload).
     - Kết quả Telemetry/Observability (kèm Trace ID, span hierarchy, service names).
  4. **Acceptance Criteria Checklist**: Đối chiếu từng tiêu chí trong Task Artifact (PASS/FAIL).
  5. **Remaining Risks / Invariants**: Xác nhận hệ thống ổn định và không vi phạm ràng buộc.
  6. **Final Conclusion**: Tuyên bố **DONE** (khi và chỉ khi toàn bộ DoD đạt).
- **Transition**: Kết thúc phiên làm việc.

---

## 3. Bảng Kiểm Soát Tuân Thủ (Enforcement Table)

Khi vi phạm xảy ra, agent **TUYỆT ĐỐI KHÔNG** được tự động dùng `git restore`, rollback hoặc tự ý xóa thay đổi (vì repository có thể chứa thay đổi có chủ đích trước đó của Human). Thay vào đó, agent phải:
**DỪNG SỬA (STOP MODIFICATION) ➔ GIỮ NGUYÊN TRẠNG THÁI HIỆN TẠI (PRESERVE CURRENT STATE) ➔ BÁO CÁO CÁC FILE BỊ ẢNH HƯỞNG KÈM GIT STATUS/DIFF ➔ CHỜ QUYẾT ĐỊNH XỬ LÝ TỪ HUMAN**.

| STT | Constraint (Ràng Buộc) | Detection (Dấu Hiệu Vi Phạm) | Consequence (Hậu Quả) | Recovery (Cách Xử Lý Bắt Buộc) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Cấm sửa code trong INVESTIGATE** | Xuất hiện thao tác edit/create/delete file hoặc dirty working tree trước ROOT_CAUSE_GATE. | **LẬP TỨC STOP MODIFICATION**. Thao tác sửa bị coi là bất hợp pháp. | Giữ nguyên hiện trạng, báo cáo danh sách file bị ảnh hưởng kèm `git status/diff`, chờ Human quyết định phương án khôi phục. |
| **2** | **Cấm can thiệp khi chưa có Human Approval** | Agent tự động chuyển sang IMPLEMENT sau PLAN mà không có lệnh phê duyệt rõ ràng từ Human. | **LẬP TỨC STOP MODIFICATION**. Quyền sửa bị đình chỉ. | Giữ nguyên hiện trạng, báo cáo thay đổi chưa được duyệt, trình bày lại PLAN và chờ chỉ thị từ Human. |
| **3** | **Cấm sửa ngoài Approved Scope (Scope Creep)** | Files được sửa trong `git status` chứa file không nằm trong danh sách Files to Modify đã duyệt. | **SCOPE_CONFLICT ➔ LẬP TỨC STOP MODIFICATION**. | Giữ nguyên hiện trạng, giải trình rõ lý do phát sinh file ngoài scope kèm `git diff`, chờ Human xem xét mở rộng scope hoặc yêu cầu hủy bỏ. |
| **4** | **Cấm tự ý đổi Architecture / API / Dependency** | Xuất hiện thay đổi trong orchestration (`compose.yaml`), dependencies (`requirements.txt`), API contracts hoặc payload. | **VI PHẠM BẤT BIẾN (Invariant Violation) ➔ LẬP TỨC STOP MODIFICATION**. | Giữ nguyên hiện trạng, báo cáo chi tiết vi phạm cấu trúc, chờ Human quyết định cách xử lý. |
| **5** | **Cấm kết luận PASS khi thiếu bằng chứng (False PASS)** | Agent tuyên bố hoàn thành task chỉ bằng lý thuyết hoặc thiếu output thực thi từ command. | **DEFECTIVE COMPLETION ➔ Từ chối nghiệm thu**. Không được chuyển sang REPORT. | Bắt buộc thực thi lại đầy đủ các bước trong Verification Plan trong môi trường live và thu thập raw evidence. |
