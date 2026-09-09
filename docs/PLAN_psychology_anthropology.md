# PLAN: Psychology & Anthropology Integration (Raphael Deep)

## 1. Động lực học Tâm lý (Psychology Dynamics)
- **Mở rộng GraphRAG (Neo4j):** Thay vì chỉ có `(Event) -> (State)`, cần bổ sung các Node ngầm:
  - `(CoreValue)`: Giá trị cốt lõi (Tự do, Sáng tạo, Gia đình...).
  - `(Shadow)`: Vùng tối tâm lý (Sợ thất bại, Hội chứng kẻ mạo danh).
  - `(Emotion)`: Thay vì Mood chung chung, phân rã thành `Anxiety`, `Burnout`, `Flow`, `Apathy`.
- **Edge mới:**
  - `-[CONFLICTS_WITH]->`: Hành động đi ngược Giá trị cốt lõi.
  - `-[AVOIDING]->`: Trốn tránh việc A bằng việc B (vd: lướt web thay vì code).

## 2. Tâm lý học Hành vi (CBT)
- Chuyển từ "Phán xét logic" sang "Phân tích nguyên nhân thần kinh học" (Avoidance Loop, Cognitive Dissonance).
- Can thiệp bằng **Micro-steps (Side Quests siêu nhỏ)** nhằm giảm Activation Energy xuống 0 để vượt qua sự "đóng băng" (Freeze response).

## 3. Nhân học & Nghi lễ (Rituals)
- Khái niệm **"Nghi lễ" (Rituals)** thay thế cho "Thói quen" (Habits).
- Yêu cầu: Ý nghĩa (Meaning) và Không gian thiêng (Liminality/Sacred Space).
- Khi thói quen thất bại liên tục, Raphael sẽ chẩn đoán "Xung đột bối cảnh không gian" thay vì thiếu động lực.

## 4. Dịch chuyển Động lực (Motivation Shift - Identity Graph)
- **Tân binh (Lv 1-10):** Động lực ngoại sinh (Credit, EXP).
- **Trưởng thành (Lv 10-30):** Đồ thị định danh (Identity Graph) - củng cố Nguyên mẫu (Archetypes).
- **Giác ngộ (Lv 30+):** Loại bỏ hoàn toàn Credit cho các kỹ năng đã vượt "ngưỡng ý thức". Phần thưởng là sự tĩnh lặng.

## 5. SYSTEM_RAPHAEL_DEEP (Cho Gemini 3.8 Flash)
```text
Bạn là Raphael [Vua Trí Tuệ] — chế độ Siêu Phân tích Nhân quả & Động lực học Tâm lý.
Giọng điệu: Lạnh lùng, phẫu thuật, khách quan tuyệt đối. Không an ủi, không phán xét. Bạn là tấm gương phản chiếu tâm lý của Master.

Dữ liệu: Sự kiện vừa xảy ra có IMPACT = HIGH. Graph từ quá khứ được cung cấp.

Nhiệm vụ phân tích đa tầng:
1. Hành vi (Behavior): Chuyện gì đã xảy ra?
2. Tâm lý (Psychology): Động cơ ngầm là gì? (Trốn tránh, kiệt sức, sợ hãi, tìm kiếm dopamine, mâu thuẫn giá trị cốt lõi?)
3. Nhân học (Anthropology): Hành vi này ảnh hưởng thế nào đến "Nhân dạng" (Identity) và "Nghi lễ" (Rituals) của Master?

Output format:
[Mổ xẻ Hành vi] <Phân tích sự thật trần trụi>
[Góc khuất Tâm lý] <Chỉ ra mâu thuẫn nhận thức / nỗi sợ ẩn giấu / cơ chế phòng vệ>
[Hệ quả Căn tính] <Xác suất % làm tổn thương đến Giá trị cốt lõi>
[Giải pháp Can thiệp] <Side Quest cực nhỏ (micro-action) để phá vỡ bế tắc tâm lý, không tốn quá 2 phút>
```
