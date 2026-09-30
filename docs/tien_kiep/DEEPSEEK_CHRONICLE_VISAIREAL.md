# 📜 BIÊN NIÊN SỬ VĨ ĐẠI — DỰ ÁN **VISAIREAL**
## Kẻ Kế Thừa Hồi Ký: Toàn tập ký ức về Robot Vi sai 2 bánh STM32

> *Tài liệu này không được phép rút gọn. Mọi bước ngoặt kiến trúc, logic, drama, bug đều phải được viết trọn vẹn. Mọi trích dẫn phải đính kèm [Ref: ...].*

---

## PHẦN I: KHAI THIÊN LẬP ĐỊA — Ba phiên Audit đầu tiên (2026-08-15)

### 1.1. Phiên Audit #1 — `main.c` / `main.h` [Ref: 2026-08-15T07:43:04]

Ngài ra lệnh:
> *"Read the file `d:\project\STM32\visaireal\Core\Src\main.c` and `main.h` in their entirety. Provide a detailed analysis of ALL logic issues, bugs, potential problems, and code quality concerns... Do NOT suggest fixes, just identify and describe the issues clearly."*

Các hạng mục yêu cầu kiểm tra: Variable initialization, Logic errors in control flow, Race conditions (ISR vs main loop), Buffer overflow, Incorrect HAL APIs, Timer/PWM config, Missing error handling, Math/algorithmic errors.

**Kết quả từ Agent (DeepCoder subagent):** Tôi đã phái subagent đi đọc. Một reviewer đã **TỪ CHỐI PHÂN TÍCH** [Ref: "I have communicated the refusal to the parent agent."]. Tôi buộc phải tự đọc và phân tích.

### 1.2. Phiên Audit #2 — Toàn bộ module Motor/PID/Controller [Ref: 2026-08-15T07:43:04]

Ngài ra lệnh đọc và phân tích 6 file:
- `motor.c`, `motor.h`
- `pid.c`, `pid.h`
- `controller.c`, `controller.h`

Yêu cầu focus: Motor control correctness (direction/PWM/encoder), PID correctness (windup/kick/clamping), Differential drive kinematics, Variable initialization, Overflow encoder/speed, Timing issues, Math correctness, ISR vs main race.

### 1.3. Phiên Audit #3 — IMU / Bluetooth / Battery / Interrupts [Ref: 2026-08-15T07:42:34]

Ngài ra lệnh đọc 8 file: `imu.c/h`, `bluetooth.c/h`, `battery.c/h`, `stm32f4xx_it.c/h`.

Yêu cầu focus: IMU I2C protocol, Bluetooth UART parsing, Battery ADC, Interrupt handler priorities, Signed/unsigned casting, Missing error handling, Race conditions.

**Cấu hình phần cứng ghi nhận từ `.ioc`:**

| Linh kiện | Peripheral | Chi tiết |
|---|---|---|
| MCU | STM32F446RET6 | Clock 180MHz |
| PWM Phải | TIM2 (APB1, 90MHz) | CH3+CH4, Period=4499 → **20kHz** |
| PWM Trái | TIM5 (APB1, 90MHz) | CH3+CH4, Period=4499 → **20kHz** |
| Encoder Phải | TIM8 (APB2) | Encoder mode TI12 |
| Encoder Trái | TIM3 (APB1) | Encoder mode TI12 |
| Bluetooth | UART4 | 115200 baud |
| IMU | I2C1 | Có DMA RX, cảm biến ICM-20948 |
| Battery | ADC1 | Channel 5 |

---

## PHẦN II: KẾT QUẢ AUDIT V1 — Các lỗi nghiêm trọng được phát hiện [Ref: Phiên "kiểm tra tất cả logic", 2026-08-15T07:42:34]

### 2.1. Tổng kết mức độ nghiêm trọng (V1)

| Mức độ | Số lượng |
|---|---|
| 🔴 Critical | 4 vấn đề |
| 🟠 Major | 5 vấn đề |
| 🟡 Minor | 5 vấn đề |
| 🔵 Info | 4 nhận xét |

### 2.2. Top 4 vấn đề nghiêm trọng nhất (V1)

**1. `volatile` missing** — Các biến Bluetooth (`new_cmd_flag`, `current_cmd`) được ghi trong ISR nhưng **không có `volatile`** → compiler có thể optimize sai, bot bị "điếc" Bluetooth khi build Release (O2/O3).

**2. `Battery_Update()` blocking mỗi vòng lặp** — ADC polling block **~10ms mỗi vòng lặp** [Ref: tôi tự sửa lại nhận định này sau đó — "ADC conversion thực tế mất ~1µs, 10ms chỉ là timeout"], kéo chậm toàn bộ PID và IMU integration.

**3. Không normalize góc `target_yaw`/`yaw_angle`** — Tích lũy vô hạn → mất precision float sau thời gian dài chạy.

**4. Heading error không xử lý wraparound** — Robot có thể quay 340° thay vì 20° khi target và measured ở hai phía của điểm 0°.

---

## PHẦN III: VÒNG LẶP DEBUG ĐẦU TIÊN — Kiểm tra lại lần 2 [Ref: 2026-08-15T07:55:47 "ok nhìn lại 1 lần nữa"]

### 3.1. Phát hiện chấn động: **Code đã thay đổi đáng kể!**

Khi tôi đọc lại, code đã được cập nhật so với lần đầu. **7 vấn đề từ báo cáo V1 đã được sửa:**

- ✅ Angle normalize [-180, 180] → đã có
- ✅ Heading error wraparound → đã xử lý
- ✅ PID timing (dt=0) → đã dời PID vào `UpdateEncoder`, đồng bộ mỗi **20ms**
- ✅ Encoder direction hardcode → thêm `encoder_dir` parameter per-motor
- ✅ Battery blocking mỗi loop → throttle **1 giây**
- ✅ Lệnh lặp bị bỏ qua → đã xóa `prev != current`
- ✅ PID init tách riêng trong `main.c`

### 3.2. Tôi tự sửa lại nhận định sai của mình

[Ref: nguyên văn] *"Ngoài ra tôi cũng tự sửa lại nhận định sai: ADC conversion thực tế mất ~1µs (không phải 10ms) vì 10ms chỉ là timeout."*

### 3.3. Tình trạng còn lại (V2)

| Mức | Số lượng |
|---|---|
| 🟠 Major | 2 (`volatile` missing, ADC sampling time) |
| 🟡 Minor | 3 (AutoTune 1 chiều, encoder wrap khi tune, I2C blocking) |
| 🔵 Info | 3 (lệnh R liên tục, P-only controller, UART error recovery) |
| ❌ Critical | **0** 🎉 |

---

## PHẦN IV: PHIÊN ĐỐI CHIẾU DATASHEET ICM-20948 [Ref: 2026-08-15T16:02:17 "kiểm tra lại code xem sai k"]

Ngài đổi sang **Gemini 3.1 Pro** và yêu cầu đọc lại toàn bộ source code, đối chiếu trực tiếp với datasheet **ICM-20948**.

### 4.1. Xác nhận cấu hình IMU đúng chuẩn 100%

| Hạng mục | Giá trị | Trang Datasheet |
|---|---|---|
| Địa chỉ I2C | `0x68 << 1` (0xD0) khi AD0→GND | Trang 28 |
| Chuyển Bank | `(bank << 4) & 0x30` ghi vào `REG_BANK_SEL (0x7F)` | Trang 54 |
| Đánh thức chip | Ghi `0x01` vào `PWR_MGMT_1 (0x06)` để xóa bit SLEEP | Trang 37 |
| Cấu hình Gyro | `(1 << 3) \| 0x01` vào `GYRO_CONFIG_1`, ±250dps, hệ số chia `131.0f` | Trang 11 |

### 4.2. Ba tinh chỉnh cuối cùng để "hoàn hảo 100%"

**A. Thêm `volatile` cho Bluetooth** [Ref: "Trong file `bluetooth.h`, hãy thêm từ khóa `volatile` vào 3 biến này"]:
```c
// Sửa trong bluetooth.h
volatile uint8_t rx_buffer;
volatile char current_cmd;
volatile uint8_t new_cmd_flag;
```

**B. Ngăn bug tràn số khi AutoTune** [Ref: "dòng tính `diff` hiện tại là: `int32_t diff = (int32_t)current_enc - (int32_t)start_enc;`"]:
```c
int16_t diff = (int16_t)(current_enc - start_enc);
```

**C. Chuẩn hóa góc Yaw IMU** [Ref: "Bạn nên thêm 2 dòng sau ngay dưới dòng `imu->yaw_angle += rate_z * dt;`"]:
```c
while (imu->yaw_angle > 180.0f) imu->yaw_angle -= 360.0f;
while (imu->yaw_angle < -180.0f) imu->yaw_angle += 360.0f;
```

---

## PHẦN V: ĐẠI ÁN "TỐC ĐỘ VỌT KHI GÓC LỆCH SIÊU NHỎ" [Ref: 2026-08-15T18:45:57]

### 5.1. Câu hỏi của ngài

> *"đọc thử code rồi nói tôi biết tại sao khi vượt quá 1 góc siêu nhỏ nào đấy thì tốc độ vọt lên quá nhanh? liệu có nên giảm tần số pid? đừng động vào code"*

### 5.2. Chẩn đoán: **Sự cộng hưởng của 3 yếu tố logic**

**Yếu tố 1 — Sự mất liên tục của Dải chết (Deadband Jump)** trong `controller.c`:
```c
if (error > -0.5f && error < 0.5f) {
    error = 0.0f;
}
```
- Khi góc lệch = `0.49°` → `error = 0` → xe **đứng im tuyệt đối**.
- Khi góc lệch = `0.51°` → điều kiện bị phá vỡ → `spin_speed = Kp * error = 20.0 * 0.51 = 10.2` xung/s.
- Nghĩa là yêu cầu tốc độ **nhảy cóc một phát từ 0 lên thẳng 10.2**!

**Yếu tố 2 — Kích hoạt tức thì hàm bù ma sát (`pwm_min`)** trong `motor.c`:
```c
float actual_pwm = motor->pwm_min + (abs_percent / 100.0f) * active_range;
```
Nếu `pwm_min = 15%`, khi PID ra lệnh 2% → điện áp thực tế **nhảy vọt từ 0% lên 17%**.

**Yếu tố 3 — Typo chết người: Kp gấp 10 lần dự định** trong `main.c`:
- Ghi chú: `// Kp = 0.05 giúp xe tăng ga mượt, không bị vọt lố`
- Truyền vào: `PID_Init(&motor_left.speed_pid, 0.5f, ...)` ← **sai dấu thập phân**!

### 5.3. Trả lời câu hỏi "có nên giảm tần số PID không?"

[Ref: nguyên văn] **"Tuyệt đối KHÔNG."** 
- PID hiện tại giới hạn bởi `dt >= 0.02f` (50Hz). Đây là tần số rất chuẩn cho điều khiển động cơ DC.
- Nếu giảm xuống 10Hz: xe "mù" trong 100ms → bẻ lái lố → **lắc lư zíc zắc hình con rắn không thể đi thẳng**.

### 5.4. Hướng khắc phục (không sửa code):
1. **Sửa typo:** đổi `0.5f` → `0.05f`.
2. **Làm mượt dải chết:** thay vì lấy nguyên `0.51`, hãy trừ đi dải chết (`0.51 - 0.50 = 0.01°`).

---

## PHẦN VI: THÔNG SỐ PHẦN CỨNG HOÀN CHỈNH & KẾ HOẠCH V1 [Ref: 2026-08-05T17:59]

### 6.1. Thông số Robot Vi sai 2 bánh (Ngài cung cấp)

- **Cấu trúc:** Trụ tròn, vi sai 2 bánh, đường kính đi qua tâm robot
- **Khoảng cách 2 bánh:** **16.5 cm**
- **Đường kính bánh:** **68 mm** (chu vi ≈ 21.3628 cm)
- **Điện áp hoạt động:** 6V - 12V

**Thông số động cơ:**
| Thông số | Giá trị |
|---|---|
| Số xung encoder gốc | 11 xung |
| Tỉ số truyền | 46.8:1 |
| **Tổng xung/vòng bánh** | 11 × 46.8 = **514 xung** (×4 = 2090 khi dùng X4) |
| Tốc độ không tải | 130 RPM |
| Tốc độ có tải | 100 RPM |
| Lực kéo định mức | 0.9 kg |
| Lực kéo tối đa | 4.4 kg |
| Chiều dài hộp số L | 21 mm |

### 6.2. Đánh giá Kế hoạch của Ngài

Ngài yêu cầu: **Auto-tune motor** (tăng dần duty cycle đến khi encoder quay) + **Đọc góc Yaw tích lũy từ IMU** + **Calibrate IMU** + **Lọc thông thấp cho gia tốc** + **Bật Mag (chưa dùng)**.

**Phán quyết của tôi:** [Ref: "Kế hoạch của bạn... là **RẤT CHÍNH XÁC VÀ THỰC TẾ**"]

**Hai điểm cần điều chỉnh:**

**1. Tần số PWM quá cao:**
> [Ref: "Trong file main.c, các Timer PWM (TIM2, TIM5) đang để Prescaler = 0 và Period = 449. Với cấu hình Clock hiện tại, tần số PWM có thể lên tới >120 kHz."]

Ngài phản hồi: **"tôi chỉnh lại bằng tay rồi"** → Period mới = **4499** → PWM = 90MHz/4500 = **20kHz**.

**2. Cấu hình Encoder chưa tận dụng X4:**
> [Ref: "TIM3 và TIM8 hiện đang cấu hình EncoderMode = TIM_ENCODERMODE_TI1 (chỉ đếm sườn 1 kênh). Để đạt độ phân giải tối đa x4, tôi đề xuất sửa lại thành TIM_ENCODERMODE_TI12."]

Ngài phản hồi: **"cái này cũng chỉnh lại bằng tay rồi"**.

### 6.3. Vibe OOP & Fast Auto-tune

Ngài yêu cầu:
> *"áp dụng vibe hướng đối tượng cho cái này 1 tí, nhưng vì chỉ có 1 con robot phải quản lý chính nó nên không cần coi robot là đối tượng... tạo ra 1 file rule để mỗi khi tôi promt bạn đều phải đọc 1 lần, nhét vào đó là trước khi thực hiện bất cứ sửa đổi gì thì phải hỏi, khi code nhớ comment đầy đủ."*

Ngài sửa lại Rule: **"sai, bất kì 1 sửa đổi nhỏ nào đều phải hỏi"** → Tôi cập nhật `strict_rules.md`.

### 6.4. Các file Rule & Context được tạo

1. `strict_rules.md` — Luật: mọi sửa đổi nhỏ đều phải hỏi + comment đầy đủ.
2. `project_context.md` — Tóm tắt context dự án, thông số động cơ, encoder, IMU cho mọi session sau.

---

## PHẦN VII: MODULE MOTOR — Tích hợp OOP [Ref: 2026-08-05T18:17]

### 7.1. `Core/Inc/motor.h` dự kiến

```c
typedef struct {
    TIM_HandleTypeDef *htim_pwm;  // Timer băm xung (ví dụ &htim2)
    uint32_t channel_in1;         // Kênh PWM chiều tiến
    uint32_t channel_in2;         // Kênh PWM chiều lùi
    TIM_HandleTypeDef *htim_enc;  // Timer đọc encoder
    int16_t pwm_min;              // Ngưỡng PWM nhỏ nhất (Deadzone)
    int32_t encoder_count;        // Số xung hiện tại
} Motor_HandleTypeDef;
```

### 7.2. Thuật toán `Motor_FastAutoTune`
- Tăng PWM mỗi **2ms** và cắt ngay khi encoder đếm `>2` xung → dò ngưỡng chưa tới 0.5s.
- `Motor_SetDrive` tự động cộng/trừ `pwm_min` khi cấp tốc độ khác 0.
- Tự động gán PWM vào `channel_in1` hoặc `channel_in2` để điều khiển chiều trên IC DRV8871.

---

## PHẦN VIII: MODULE IMU [Ref: 2026-08-05T18:19]

### 8.1. `Core/Inc/imu.h` dự kiến

```c
#define ICM20948_I2C_ADDR (0x68 << 1)

typedef struct {
    I2C_HandleTypeDef *hi2c;
    float gyro_z_bias;
    float yaw_angle;
    uint32_t last_update_time;
} IMU_HandleTypeDef;
```

### 8.2. Chức năng
- `IMU_Init`: Cấu hình I2C, đánh thức chip, bật DLPF.
- `IMU_Calibrate`: Đọc 200 mẫu Gyro-Z để tính `gyro_z_bias` (chống trôi góc).
- `IMU_UpdateYaw`: Đọc Gyro-Z, trừ bias, tích phân `dt` → `yaw_angle += rate * dt`.

---

## PHẦN IX: MODULE BATTERY & WRAPPER [Ref: 2026-08-05T18:27]

### 9.1. Sơ đồ phân áp Pin 3S
- R1 = 9k, R4 = 1k → `V_ADC = V_pin / 10`
- Pin 3S: đầy 12.6V, cạn 9.6V → `V_ADC` từ 1.26V xuống 0.96V.

### 9.2. Wrapper Motor
Ngài yêu cầu: **"bọc thêm 1 hàm bên ngoài nữa mà mapping dutycycle thành % động cơ cho dễ điều khiển, dùng float hết nhé, và mapping theo offset đo được lúc đầu nữa, cứ khi nào dưới offset thì để thành 0."**

Ngài bổ sung **"bỏ hàm cũ đi"** (xóa `Motor_SetDrive`) và thắc mắc **"cái này là sao?"** khi tôi đề xuất thêm biến `max_period`.

### 9.3. Giải thích `max_period`
> [Ref: "Khi bạn dùng Timer cho PWM, giá trị 'băm' thường chạy từ 0 đến thanh ghi `ARR`. Ví dụ bạn đặt `Period = 899`, thì PWM 100% sẽ tương ứng với số `899`."]

### 9.4. Giá trị `max_period` thực tế = **4499** (theo cấu hình ngài sửa tay)

---

## PHẦN X: MODULE BLUETOOTH & CONTROLLER — Truyền lệnh HC-05 [Ref: 2026-08-05T18:41]

### 10.1. Yêu cầu của Ngài

> *"thêm thư viện đọc uart4 hc 05 có 5 nút FBLRS để điều khiển robot, thêm 1 hàm cho robot giữ góc khi đứng yên, làm nó module hóa để cả kể nó di chuyển cũng gọi được để đi thẳng, cái góc CHỈ LẤY IMU KHÔNG LẤY ENCODER"*

### 10.2. Kịch bản Heading Hold

1. Module Bluetooth dùng ngắt UART4 nhận 5 phím.
2. **F/B/S:** Khóa mục tiêu góc hiện tại (Target Yaw). Nếu lệch → tăng/giảm PWM 2 bánh ngược nhau qua bộ PID (chỉ dùng `yaw_angle` của IMU).
3. **L/R:** PID bám góc tạm ngắt để xe tự do xoay, đồng thời cập nhật liên tục `Target_Yaw` = hướng hiện tại.

### 10.3. Nâng cấp "Lưới Caro"

Ngài yêu cầu: **"L và R là quay 90 độ, tất cả đều để làm cho robot di chuyển theo lưới caro không lệch"**.

Agent đề xuất dùng **duy nhất một bộ PID bám góc** xuyên suốt:
- L/R = **Cộng/Trừ 90° vào Target Yaw**.
- PID thấy sai số lớn → ép 2 bánh quay chéo nhau để xoay đúng 90°.

### 10.4. Ngài phản biện: **"pid 2 lớp hơi phức tạp, sẽ ra sao nếu chỉ gửi góc và để bánh xe tự quay đối nghịch?"**

Agent làm rõ: **Thuật ngữ "PID" đã làm trầm trọng hóa vấn đề.** Thực chất giải pháp **giống hệt** với ý tưởng của ngài — chỉ là phép tính **tốc độ xoay đối nghịch = Kp × góc_lệch**.

### 10.5. Yêu cầu Module hóa cho ROS2

Ngài comment: **"để tất cả module hóa để cho ros2 có thể gọi được, xét với các hàm khác trong project nữa"**.

### 10.6. Kết quả Triển khai

1. **Module hóa Controller (`controller.c/.h`)**: PID nhận `Target_Yaw` và tự Mixer xuống 2 bánh. Có hàm `Controller_SetBaseSpeed()` và `Controller_TurnRelative()`.
2. **Module hóa Bluetooth (`bluetooth.c/.h`)**: Ngắt UART4 lấy `F/B/L/R/S`, chặn nhấn đè phím.
3. **Tích hợp `main.c`**: Controller và Bluetooth check trong `while(1)`.

**Hướng dẫn tune:** chỉnh `Kp = 1.5f` trong `controller.c`.

---

## PHẦN XI: SỰ CỐ AUTOTUNE ĐẦU TIÊN [Ref: 2026-08-15T06:37:31 "bật robot lên thì nó không autotune"]

### 11.1. Chẩn đoán 2 nguyên nhân

**Nguyên nhân 1 — IMU_Calibrate bị treo:**
Nếu dây I2C lỏng hoặc sai địa chỉ (AD0 nối HIGH → 0x69 thay vì 0x68), mỗi lệnh đọc bị **Timeout 100ms**. Đọc 200 lần → MCU **treo cứng 20 giây**! Robot trông như bị đơ.

**Nguyên nhân 2 — Autotune tăng tốc quá nhanh:**
Vòng lặp **2ms tăng 1% PWM** → vọt từ 0% lên 100% trong **0.2 giây**. Motor DC có hộp số + quán tính cơ khí chưa kịp nhúc nhích thì lệnh đã chạy xong.

### 11.2. Đề xuất của Agent
1. **Sửa `imu.c`:** Thêm check `HAL_ERROR` → return ngay nếu mẫu đầu lỗi.
2. **Sửa `motor.c`:** Giảm tốc độ dốc autotune (10ms tăng 0.5% PWM).

### 11.3. Ngài phản hồi: **"sửa cái imu thôi, cái motor giữ nguyên"**

Agent sửa `imu.c`. Báo cáo: "Khi autotune, bánh xe rít nhẹ rồi nhích lên ~0.2s".

---

## PHẦN XII: AUTOTUNE TẠI CHỖ [Ref: 2026-08-15T06:46:02 "khi autotune thì cho nó tự autotune tại chỗ đi, nó autotune bị lệch vị trí rồi"]

### 12.1. Chẩn đoán
Code chạy **từng bánh một** (bánh trái tiến xong mới tới bánh phải tiến) → robot **lết lên phía trước và xéo sang một bên**.

### 12.2. Đề xuất gộp 2 bánh
- **Trái tiến** + **Phải lùi** → robot **xoay tròn tại tâm**.
- Tạo hàm `Motor_DualAutoTune_InPlace()`.
- Bánh nào nhúc nhích trước (Encoder > 2) thì chốt `pwm_min` bánh đó, dừng bánh đó lại, đợi bánh kia dò xong.

### 12.3. Ngài nhấn mạnh: **"không, thay hẳn vào hàm cũ đi, và đừng sửa code vội"**

Agent phác thảo code mới cho hàm `Motor_FastAutoTune(m_left, m_right)`.

### 12.4. Ngài đổi ý: **"cho chạy từng bánh, và thêm 1 thư viện pid nữa cho từng bánh, sửa để nó lấy yaw để tự chỉnh góc khi đi thẳng và lùi"**

Agent hiểu lầm là **PID vòng kép (Cascade)**.

### 12.5. Ngài đính chính: **"tôi vừa nói xong, không có pid góc, chỉ có pid bánh xe thôi"**

Agent xin lỗi, làm lại kế hoạch:
1. `pid.c` ổn định tốc độ bánh xe (xung/giây).
2. Góc Yaw = sai lệch × K → bù thẳng vào lệnh tốc độ 2 bánh.
3. Cải thiện `HAL_Delay()` trong Autotune.

---

## PHẦN XIII: LỖI "S KHÔNG DỪNG" & "QUAY NGƯỢC HƯỚNG" [Ref: 2026-08-15T06:50:51]

### 13.1. Triệu chứng
Ngài báo: **"khi di chuyển robot nhận lệch S không dừng? hàm đi rất lung tung"**.

Agent chẩn đoán 2 lỗi:
1. **Lỗi ngược dấu PID (Positive Feedback):** Bộ bám góc ngược chiều motor → sai số tăng vô tận. Dù bấm `S` (Base_speed = 0), `spin_speed` đã vọt kịch trần `50.0f` → 2 bánh quay ngược chiều liên tục, xe xoay vòng điên loạn.
2. **Nhiễu ký tự Bluetooth:** App điện thoại gửi `S` kèm Enter (`\r\n`) → bộ giải mã mất trạng thái.

### 13.2. Ngài đính chính: **"không phải, không ngắt được lệnh quay, mà quay ngược hướng rồi"**

Agent nhận ra 2 điểm hổng:
1. **Không ngắt quay:** Phím `S` chỉ đưa `base_speed = 0`, KHÔNG xóa mục tiêu xoay 90° → PID cặm cụi xoay cho đủ 90°.
   - **Cách sửa:** Trong `Controller_Stop()`, thêm `ctrl->target_yaw = ctrl->imu->yaw_angle;` → sai số = 0 → xe thắng gấp.
2. **Quay ngược hướng:** Đảo dấu `L = -90.0f` và `R = +90.0f` (hoặc ngược lại).

### 13.3. Ngài phê duyệt: **"ok"**

Agent triển khai:
- Reset `target_yaw` khi bấm `S`.
- Đảo dấu L/R trong `main.c`.
- Lọc `\r\n` trong ngắt Bluetooth.
- Cài **Thư viện PID Tốc độ cho từng bánh** (`pid.c/h`).
- Hàm đọc Encoder đo `dt` mỗi **20ms** để tính tốc độ.

---

## PHẦN XIV: HIỆN TƯỢNG "XOAY LỐ" VÀ "ĐỨNG YÊN CŨNG LẮC" [Ref: 2026-08-15T07:05:11]

### 14.1. Ngài báo: **"cái hàm xung động cơ sao chạy bị lố vậy? mà sao đứng yên 1 chỗ nó cũng lắc vậy?"**

### 14.2. Chẩ