
### [2026-09-08 12:56] — Triển khai Spatial Context Engine (Máy Trạng Thái Không Gian)
**Agent:** Antigravity
**Mục tiêu:** Xử lý tình trạng spam Side Quest khi bật Live Location, lọc nhiễu dừng đèn đỏ/nghỉ mệt, và tiết kiệm 99% chi phí gọi Gemini Pro.
**Chi tiết triển khai:**
1. Thêm model `SpatialState` vào `db/models.py` để lưu trữ Tọa độ cuối, Thời gian ping cuối, và Trạng thái Di chuyển (TRANSITING, STATIONARY, WAITING).
2. Viết thuật toán `haversine` và `process_location` tại `core/spatial.py`. Thuật toán tính vận tốc (km/h) giữa 2 ping. Nếu tốc độ = 0 nhưng đang đi giữa đường (< 3 phút) => Bỏ qua (Đèn đỏ). Nếu dừng > 3 phút => Bắn Event `ARRIVED_WAYPOINT`.
3. Sửa `location.py` để chỉ gọi `evaluate_and_generate_side_quest_async` khi `process_location` trả về một Event ý nghĩa, thay vì gọi mù quáng mỗi lần có ping.
4. Nâng cấp Prompt trong `core/llm.py`: Vẫn dùng `Gemini 3.1 Pro`, nhưng ra lệnh cứng: Không làm phiền khi ở "Nhà", và Chủ động nhắn tin hỏi User về mục đích nếu đến một "Địa điểm Lạ" (Chưa có trong Mem0).
**Files thay đổi:** db/models.py, core/spatial.py, bot/handlers/location.py, core/llm.py
