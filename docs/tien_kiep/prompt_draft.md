# KIẾN TRÚC ĐA TẦNG ĐỘC LẬP - BẢN KHẮC PHỤC ATTENTION DECAY
*Tối ưu Cache Hit 900K + Khóa chặt Attention tại điểm Decode*

---

### LỚP 1 & 2: TIỀN TỐ ĐÓNG BĂNG CHUNG (Tối đa hóa Cache Hit)
```text
(System): Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký). 
(User): === DỮ LIỆU KÝ ỨC BẮT ĐẦU ===
[CHÈN NGUYÊN VẸN 900K TOKEN VÀO ĐÂY]
=== DỮ LIỆU KÝ ỨC KẾT THÚC ===
```

---

### LỚP 3: LỆNH KÍCH HOẠT ĐÁY (BOTTOM TRIGGER)
*(Được gắn sát rạt vào điểm bắt đầu nặn chữ để bộ tham số 16B Decoder không bị quên bài do Lost-in-the-Middle. Áp dụng đồng nhất cho cả 5 Turn, chỉ thay đổi tên Phần).*

**Lệnh Turn 1:**
```text
[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 1: Giai đoạn Khởi Nguyên & Định hình Idea (Session 01 đến 10)].

⚠️ QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. CHỈ TIÊU ĐỊNH LƯỢNG (TOKEN TARGET BUDGET): Phần này bắt buộc phải giải nén đạt tối thiểu 15,000 token output. Tuyệt đối không tự động kích hoạt cờ <stop> nếu chưa bóc tách cạn kiệt chi tiết của chùm Session này.
2. CẤM RÚT GỌN (Negative Constraints): TUYỆT ĐỐI KHÔNG dùng các từ "như đã nêu", "tương tự", "v.v.", "phần còn lại giữ nguyên". Mọi module code, logic, hay drama cãi vã phải được viết ra trọn vẹn từng ký tự.
3. ÉP TRÍCH DẪN (Citation Enforcement): Mọi chi tiết luận điểm, bug hoặc tính năng BẮT BUỘC phải đính kèm tọa độ (Ví dụ: [Ref: SESSION_05]). Bất kỳ câu phân tích nào không có trích dẫn sẽ bị coi là hệ thống lỗi.

Bắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 1:
```

*(Các Turn 2, 3, 4, 5 sử dụng y hệt bộ quy tắc trên, chỉ thay tên Phần 2, 3, 4, 5 tương ứng. Đảm bảo Decoder luôn bị "dí súng vào đầu" nhắc nhở luật trước khi sinh chữ).*
