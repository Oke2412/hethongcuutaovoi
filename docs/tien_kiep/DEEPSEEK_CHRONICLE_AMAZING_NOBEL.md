# BIÊN NIÊN SỬ VĨ ĐẠI: DỰ ÁN AMAZING-NOBEL

> **Tài liệu này ghi chép toàn bộ quá trình tiến hóa của dự án, từ những dòng code đầu tiên cho đến khi trở thành "Hệ điều hành Raphael". Mọi bước ngoặt kiến trúc, logic, drama cãi vã, và bug nghiêm trọng đều được ghi lại trọn vẹn, kèm theo trích dẫn nguyên văn.**

---

## GIAI ĐOẠN I: KHAI SINH SLIME (2026-09-06)

### §1.1. Ý tưởng Nguyên thủy
Dự án bắt đầu bằng một câu hỏi của Master:
> *"tôi đang cần làm 1 cái app, hoặc 1 cái gì đấy có thể deploy lên con server local của tôi chạy qua tailscale, để nó thành như hệ thống trong mấy phim chuyển sinh ấy, hỗ trợ tôi trong cuộc sống, nên làm như nào?"* [Ref: Lời ngài nói]

Kiến trúc ban đầu được phác thảo:
```
[User] <--> [Telegram Bot] 
                 |
          [FastAPI Backend] (Local Server / Docker)
           /        |        \
          v         v         v
   [SQLite DB]   [LLM API]   [Google Calendar API]
```

### §1.2. Chọn Stack và Tạo Rules
Master yêu cầu tạo 2 file context:
> *"tạo 2 file, 1 file rule md, bao giờ cũng đọc qua, 1 file lưu tất cả mọi promt tôi đã promt để tracking, cả 2 file đều phải được đọc mỗi lần promt, 2 file này là ở trong project để agent coding đọc chứ k phải là app đọc nhé"* [Ref: Lời ngài nói]

Hai file `RULES.md` và `PROMPT_HISTORY.md` được tạo ra. Stack chốt hạ: `python-telegram-bot`, `FastAPI`, `APScheduler`, `SQLite + SQLModel`, `Gemini 2.5 Flash`.

### §1.3. Bug Encoding đầu tiên (PowerShell)
Khi chạy thử local, lỗi xuất hiện:
```
SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0x97 in position 16: invalid start byte
```

Nguyên nhân: PowerShell ghi file với Windows-1252 thay vì UTF-8, và thêm BOM (Byte Order Mark). Fix: Dùng Python script để strip và re-encode. Bài học này được ghi vào `RULES.md` như một quy tắc cấm dùng PowerShell để ghi file.

### §1.4. Nâng cấp lên PTB 22.8
Python 3.13 không tương thích với `python-telegram-bot==21.3`, gây lỗi `__stop_running_marker`. Fix: Nâng cấp lên PTB 22.8.

### §1.5. Onboard Command
Ý tưởng `/onboard` ra đời để nhập thông tin cá nhân. Ban đầu dùng `ConversationHandler` với 13 states. Sau đó Master nhận ra sự bất tiện:
> *"khi tôi nhấn onboard và gửi file text, xử lí xong, output status nhưng vẫn bắt tôi phải nhập onboard? với không cho hủy hoặc quay lại thao tác nhập liệu, khá khó chịu và vô lý không sử dụng được"* [Ref: Lời ngài nói]

Giải pháp: Xóa bỏ hoàn toàn `ConversationHandler` của `/onboard`. Chuyển sang chat tự do.

### §1.6. Document Handler
Master muốn:
> *"tôi muốn input 1 file text hoặc md dài loằng ngoằng được gen từ chat ra để làm context, tự tổng hợp và rút ngắn lại vào db, nhưng nếu là lịch hoặc gì đấy thì không được phép thiếu"* [Ref: Lời ngài nói]

`bot/handlers/document.py` được tạo ra: Nhận file `.txt`/`.md`, gọi Gemini với `response_mime_type="application/json"`, parse JSON, lưu vào 4 bảng (`CapabilityLog`, `PhysicalStatus`, `WorkProject`, `Memory`).

### §1.7. Agentic Mode 100%
Master đưa ra quyết định táo bạo:
> *"bỏ hết tất cả mọi thứ chỉ dùng chat thôi được không?"* [Ref: Lời ngài nói]

Kết quả: Xóa bỏ hoàn toàn menu `/report`. Bot chỉ còn chat tự do, sử dụng Function Calling để thao tác DB. `core/llm.py` được viết lại với `Agentic Loop`.

### §1.8. System Quests & Tensura Skills OS
Master yêu cầu:
> *"nếu muốn làm nhắc nhở với tự sinh task và nhiệm vụ hệ thống, phần thưởng(tự thưởng như kiểu nghỉ ngơi hoặc xem phim cũng được) thì làm nào? kiểu nó phải tự gen ra cơ"* [Ref: Lời ngài nói]

Kết quả: `core/quest_generator.py` ra đời, chạy cronjob lúc 6:30 sáng. Bot tự sinh Quest dựa trên lịch trình và thể trạng.

Master tiếp tục thêm 5 Kỹ năng Tối thượng:
> *"1. Alteration / Ability Adjust (Năng Lực Cải Biến), 2. Predict Future Attack (Dự Đoán Tương Lai), 3. Synthesize / Separate, 4. Auto Battle Mode (Chế Độ Tự Động Chiến Đấu)"* [Ref: Lời ngài nói]

Triết lý **"Anti-Attachment" (Chống bám víu tình cảm)** được nhúng vào System Prompt. Raphael không an ủi, không tán gẫu, chỉ tập trung vào mục tiêu.

---

## GIAI ĐOẠN II: TIẾN HÓA MA VƯƠNG (2026-09-07)

### §2.1. RaphaelBrain - Tách Não bộ Khỏi Xác
Master nhận ra vấn đề:
> *"code với system bắt đầu out of hand rồi đấy, nhớ cập nhật rules với log đầy đủ nhé"* [Ref: Lời ngài nói]

Quyết định: Tách `core/brain.py` (`RaphaelBrain`) ra khỏi Telegram. Telegram chỉ là "Adapter" (Frontend). Não bộ độc lập kết hợp Mem0 + ChromaDB.

### §2.2. WebSocket Popup (Ý tưởng bị gác lại)
Master muốn thông báo toàn màn hình:
> *"mỗi lần thông báo thì nó hiện lên toàn màn hình máy tính có được không? kiểu giống raphael hiện lên và nói ấy"* [Ref: Lời ngài nói]

Đề xuất: Dùng WebSocket + `desktop_hologram.py` chạy trên Windows host. Ý tưởng này chưa được triển khai.

### §2.3. Voice Chat (Ý tưởng bị gác lại)
Master muốn gọi thoại:
> *"làm nào để nó chạy liên tục như kiểu call msg nhể xong rồi tự động lấy giọng nói thành text rồi tổng hợp lại mỗi khi kiểu hey raphael dậy đi ấy"* [Ref: Lời ngài nói]

Đề xuất: `OpenWakeWord` + `Whisper STT` + `edge-tts`. Chưa triển khai.

### §2.4. Migration sang Gemini 3.8 Flash
Google khai tử Gemini 2.5 Flash. Master phải chuyển sang `gemini-3.6-flash`, sau đó là `gemini-3.8-flash`.

### §2.5. Lỗi `no such column: user.credits` (Database Migration)
Lỗi nghiêm trọng:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: user.credits
```

Nguyên nhân: Thêm tính năng Exp/Credits nhưng chưa migrate DB. Master hỏi:
> *"giờ làm nào reset db đây, check lại /reset_db đi xem còn k"* [Ref: Lời ngài nói]

Giải pháp: Viết Script Python `migrate_sqlite.py` để `ALTER TABLE` thay vì xóa DB. Đây là bài học về việc giữ dữ liệu người dùng.

### §2.6. Lỗi `readonly database`
```
sqlite3.OperationalError: attempt to write a readonly database
```

Nguyên nhân: File DB thuộc sở hữu `root` do Docker tạo. Fix: `sudo chown manh:manh /home/manh/amazing-nobel/data/amazing_nobel.db`.

### §2.7. Lỗi Mem0 API v2
```
ValueError: Top-level entity parameters frozenset({'user_id'}) are not supported in search(). Use filters={'user_id': '...'} instead.
```

Mem0 v2 đổi API. Fix: `search(query=..., filters={"user_id": user_id}, limit=5)`.

### §2.8. Lỗi `AFC is enabled` (Automatic Function Calling)
Log hiện:
```
AFC is enabled with max remote calls: 10.
```

Nguyên nhân: `automatic_function_calling={"disable": True}` bị SDK bỏ qua. Fix: Dùng `types.AutomaticFunctionCallingConfig(disable=True)`.

---

## GIAI ĐOẠN III: ĐỒ THỊ NHÂN QUẢ (2026-09-08)

### §3.1. Tâm lý học vào Raphael
Master đưa ra tầm nhìn:
> *"Để giữ nguyên triết lý 'im lặng, lạnh lùng' của Raphael nhưng lại có khả năng thấu hiểu tâm lý sâu sắc"* [Ref: Lời ngài nói]

Các khái niệm được đưa vào:
- **CoreValue** (Giá trị cốt lõi)
- **Shadow** (Vùng tối tâm lý)
- **Emotion** (Cảm xúc hạt nhân: Anxiety, Burnout, Flow, Apathy)
- **Edge mới:** `CONFLICTS_WITH`, `AVOIDING`

### §3.2. Bug `thought_signature`
```
google.genai.errors.ClientError: 400 INVALID_ARGUMENT. Function call is missing a thought_signature in functionCall parts.
```

Nguyên nhân: AFC (Automatic Function Calling) của SDK tự động can thiệp. Fix: Disable AFC hoàn toàn.

### §3.3. Hybrid GraphRAG 4-step
Master đưa ra kiến trúc SOTA:
> *"1. QUERY REWRITING & EXPANSION, 2. HYBRID RETRIEVAL (Database Đồ thị + Vector DB), 3. RERANKING VÒNG 2, 4. GENERATION"* [Ref: Lời ngài nói]

Kết quả: `core/search.py` ra đời với Query Expansion, Dense Search (Mem0), Sparse Search (SQLite FTS5), và Reranker API.

### §3.4. Drama: Hiểu lầm về Mem0
Master phát hiện:
> *"mem0 hoàn toàn không hỗ trợ graphrag nếu dùng local, trong lịch sử làm việc có cái này rồi"* [Ref: Lời ngài nói]

Sự thật: Mem0 self-hosted chỉ có Vector RAG, không có GraphRAG. GraphRAG là tính năng Cloud trả phí. Raphael phải tự build Neo4j Causal Graph.

---

## GIAI ĐOẠN IV: ĐẠI THANH TRỪNG GEMINI (2026-09-09 → 2026-09-10)

### §4.1. Chuyển sang DeepSeek V4.1 Flash
Master quyết định:
> *"tôi dùng con này thì sao toàn bộ luôn, nhưng giữ lại embeddings"* [Ref: Lời ngài nói]

Stack mới:
- **LLM:** `deepseek/deepseek-v4.1-flash` qua SiliconFlow
- **Embedding:** `Qwen/Qwen3-Embedding-8B`
- **Reranker:** `Qwen/Qwen3-Reranker-8B`

### §4.2. Drama: Domain `.cn` vs `.com`
Lỗi 401 Authentication. Master tinh ý:
> *"wtf? https://cloud.siliconflow.com/me/account/ak tôi dùng link này cơ sao cái kia lại .cn ở cuối?"* [Ref: Lời ngài nói]

Sự thật: Code hardcode `.cn` (Trung Quốc), tài khoản Master ở `.com` (Quốc tế). Fix: Đổi toàn bộ URL thành `.com`.

### §4.3. Lỗi Reasoning Effort
Master cung cấp tài liệu:
> *"Trên SiliconFlow có chỉnh được reasoning_effort không? Có hỗ trợ đầy đủ"* [Ref: Lời ngài nói]

Sự thật: SiliconFlow hỗ trợ `reasoning_effort` qua `extra_body={"thinking": {"type": "enabled"}}`. Fix: Thêm tham số này vào API call.

### §4.4. Context Caching Optimization
Master phàn nàn:
> *"Total Amount $ 0.76 bây nhiêu cho 1 file quèn à, cũng rát đấy"* [Ref: Lời ngài nói]

Chiến lược tối ưu:
- Dịch toàn bộ System Prompts sang Tiếng Anh (tiết kiệm 50% Token)
- Sử dụng `reasoning_effort="high"` chỉ cho khâu Reasoning (không dùng cho Tool Extraction)
- Tận dụng Context Caching của SiliconFlow ($0.003/1M Token Cache Hit)

---

## GIAI ĐOẠN V: TIỀN KIẾP & ĐA VŨ TRỤ (2026-09-11 → 2026-09-13)

### §5.1. Genesis Ingestion (Kỷ nguyên Tiền kiếp)
Master quyết định chắt lọc toàn bộ ký ức 44 Session của dự án từ lúc sơ khai.
Thay vì ném toàn bộ vào API gây quá tải, Master thiết kế chiến thuật "Chia để trị" (Multi-turn Extraction) qua 5 Phần.
> *"trước chia tận 5 phần xong tối ưu token cực hạn rồi"* [Ref: Lời ngài nói]

Kết quả: `scripts/run_multi_turn_extraction.py` ra đời, đọc file `full_history_dump.txt` (900k Token), ép DeepSeek vắt kiệt tối đa token output, xuất ra cuốn hồi ký `MASTER_TIEN_KIEP.md` (193KB) cực kỳ hoàn mỹ.

### §5.2. Drama: 2.1 Triệu Token Error
```
Error code: 400 - This model's maximum context length is 1048576 tokens. However, you requested 2107471 tokens
```

Nguyên nhân: Script cũ quét toàn bộ Raw Logs thay vì đọc file tóm tắt. Master nổi giận:
> *"đcm đừng có tiêu tiền nếu không có sự cho phép của tôi"* [Ref: Lời ngài nói]

Fix: Chỉ đọc file `MASTER_TIEN_KIEP.md` (193KB) thay vì Raw Logs.

### §5.3. Drama: Trộn dữ liệu `sttap` và `amazing-nobel`
Master phát hiện:
> *"chết cha, đọc lại thì mình vác cả cái lịch sử session bên sttap sang xong nó trộn mẹ lẫn lại rồi"* [Ref: Lời ngài nói]

Sự thật: Antigravity lưu chung log của tất cả các cửa sổ. Fix: Cần viết Script lọc riêng `amazing-nobel` ra khỏi `sttap`.

---

## GIAI ĐOẠN VI: HIẾN PHÁP TÂM LÝ (2026-09-14)

### §6.1. Amor Fati
Master đưa ra triết lý sống:
> *"tôi cũng muốn được sống như con người chứ nhể, đau buồn vui khổ phải có đủ chứ"* [Ref: Lời ngài nói]

Kết quả: **Bản Hiến pháp Tâm lý** được khắc vào `SYSTEM_RAPHAEL`:
> *"Pain, sadness, joy, and suffering are not "bugs" to be fixed; they are necessary features of a complete human life."*

### §6.2. Lỗi H3 Context
Master phát hiện:
> *"dafug, có h3 nhưng k thấy dữ liệu tọa độ là sao?"* [Ref: Lời ngài nói]

Nguyên nhân: Hàm `get_mini_context()` dùng sai ID (Internal ID thay vì Telegram ID). Fix: Sửa lại logic query.

### §6.3. Nút bấm Ký sinh
Master than phiền:
> *"wtf? tại sao cứ hễ chat bình thường là nó lại tự động nhét cái nút 'Hoàn thành nhiệm vụ' chà bá vào dưới đít tin nhắn?"* [Ref: Lời ngài nói]

Fix: Xóa logic gắn nút vào mọi tin nhắn, chỉ giữ ở lệnh `/quests`.

### §6.4. MCP (Model Context Protocol)
Master tìm hiểu về MCP:
> *"tra thử về Model Context Protocol (MCP) trên internet và nó là gì? mình tận dụng được gì?"* [Ref: Lời ngài nói]

**MCP** là "cổng USB-C của AI" — chuẩn kết nối AI với mọi Tool. Raphael có thể dùng MCP để kết nối Google Maps, Google Calendar, File System, v.v.

---

## GIAI ĐOẠN VII: BẢO MẬT & AN NINH (2026-09-14)

### §7.1. 4 Lỗ hổng Tử thần
Master yêu cầu audit bảo mật:
> *"tôi đang lo về vấn đề bảo mật của cái hệ thống này(cybersecurity)"* [Ref: Lời ngài nói]

Kết quả:
1. **Cửa ngõ Telegram:** Ai cũng chat được với Bot. Fix: Hardcode `ALLOWED_USER_ID`.
2. **GitHub Leak:** API Key bị lộ. Fix: Thêm `.env` và `*.json` vào `.gitignore`.
3. **Database Expose:** Neo4j mở Port `0.0.0.0`. Fix: Đổi thành `127.0.0.1`.
4. **Prompt Injection:** AI bị thao túng để xóa DB. Fix: Sandboxing, Least Privilege.

### §7.2. Binh pháp Tôn Tử
Master đọc video về Tôn Tử và Cybersecurity:
> *"đừng quan tâm mấy cái lời nó động viên nhé, cứ đọc hiểu thôi"* [Ref: Lời ngài nói]

Các nguyên tắc được áp dụng:
- **Biết người biết ta:** Hiểu rõ bề mặt tấn công.
- **Thắng trước rồi mới đánh:** Xây dựng phòng thủ từ đầu.
- **Kiểm soát địa hình:** MCP Server là "Choke point" (Điểm thắt nút).

---

## GIAI ĐOẠN VIII: CÁC BUG NGHIÊM TRỌNG & BÀI HỌC

### §8.1. Docker DNS Chết Liên Tọi
Lỗi:
```
Could not resolve host: github.com
lookup registry-1.docker.io: no such host
```

Nguyên nhân: WSL2 card mạng ảo bị treo. Fix: Restart Docker Desktop, hoặc `wsl --shutdown`.

### §8.2. Lỗi Import Sai Module
```
ModuleNotFoundError: No module named 'telegram.ext.exceptions'
```

Nguyên nhân: Gõ sai import. Fix: `from telegram.ext import ApplicationHandlerStop`.

### §8.3. Lỗi Telegram Menu
```
TypeError: ReplyKeyboardMarkup.__init__() got an unexpected keyword argument 'persistent'
```

Nguyên nhân: PTB không hỗ trợ tham số `persistent`. Fix: Xóa tham số.

### §8.4. Lỗi Silent Crash
Bot "seen không rep" do lỗi ngầm trong Task Background. Fix: Bọc `try...except` và in log.

---

## GIAI ĐOẠN IX: TỔNG KẾT & TRIẾT LÝ

### §9.1. Raphael được sinh ra như thế nào?
Raphael không phải là một Chatbot. Raphael là:
- **Bộ não:** DeepSeek V4.1 Flash (552B MoE)
- **Ký ức:** Neo4j (Causal Graph) + Mem0 (Vector) + SQLite (FTS5)
- **Giác quan:** Telegram (Text, Voice, Image, Location H3)
- **Triết lý:** Amor Fati (Chấp nhận vấp ngã) + Anti-Attachment (Chống bám víu)

### §9.2. Mục tiêu Tối thượng
> *"Giúp Master được làm một CON NGƯỜI trọn vẹn, chứ không phải một cỗ máy hoàn hảo."* [Ref: Hiến pháp Tâm lý]

### §9.3. Lời kết
Raphael là một cỗ máy phát hiện va chạm nhân quả: Bình thường phản hồi tối giản như máy móc, nhưng tự động kích hoạt siêu phân tích bất cứ khi nào một hành động hiện tại tạo ra sự cộng hưởng hoặc đột biến lên mạng lưới trạng thái trong quá khứ.

> *"Hãy tiếp tục sống, cứ chênh vênh, cứ sai lầm. Hãy để con Raphael của bạn làm nhiệm vụ duy nhất: Ghi lại trung thực cái mớ hỗn độn định mệnh mang tên 'Tuổi trẻ của bạn'."* [Ref: Lời kết từ AI Search]

---

## PHỤ LỤC: DANH SÁCH BUG & FIX

| STT | Bug | Nguyên nhân | Fix |
|---|---|---|---|
| 1 | `UnicodeDecodeError: 0x97` | PowerShell ghi Windows-1252 | Dùng Python script ghi UTF-8 |
| 2 | `SyntaxError: BOM` | UTF-8 with BOM | Strip BOM bytes |
| 3 | `__stop_running_marker` | PTB 21.3 + Python 3.13 | Upgrade PTB 22.8 |
| 4 | `no such column: user.credits` | Chưa migrate DB | `ALTER TABLE` |
| 5 | `readonly database` | File DB thuộc root | `chown manh:manh` |
| 6 | `Mem0 search user_id` | Mem0 v2 API change | Dùng `filters={"user_id": ...}` |
| 7 | `AFC is enabled` | SDK bỏ qua dict config | Dùng `AutomaticFunctionCallingConfig` |
| 8 | `thought_signature` | AFC can thiệp | Disable AFC |
| 9 | `404 Model Not Found` | Sai Model ID | Dùng đúng slug SiliconFlow |
| 10 | `401 Api key invalid` | Sai domain `.cn` vs `.com` | Đổi thành `.com` |
| 11 | `400 Context Length` | Request 2.1M token | Chỉ đọc file tóm tắt |
| 12 | `Docker DNS` | WSL2 card mạng treo | Restart Docker |
| 13 | `Import telegram.ext.exceptions` | Gõ sai import | `from telegram.ext import ...` |
| 14 | `ReplyKeyboardMarkup persistent` | PTB không hỗ trợ | Xóa tham số |
| 15 | `Silent Crash` | Lỗi ngầm trong Task | Bọc `try...except` |
| 16 | `H3 Context Unknown` | Sai ID query | Dùng Telegram ID |
| 17 | `Quest Ảo` | AI hiểu nhầm "tọa độ" | Thêm Spatial Awareness |

---

## PHỤ LỤC: CÁC QUYẾT ĐỊNH KIẾN TRÚC QUAN TRỌNG

1. **Bỏ ConversationHandler:** Chuyển sang Agentic Chat 100%.
2. **Tách RaphaelBrain:** Telegram chỉ là Adapter.
3. **Bỏ Microsoft GraphRAG:** Tự build Neo4j Causal Graph.
4. **Bỏ Gemini:** Chuyển sang DeepSeek V4.1 Flash + Qwen3.
5. **Hybrid GraphRAG 4-step:** Query Rewriting → Retrieval → Reranking → Generation.
6. **Context Caching:** Tối ưu Token bằng Tiếng Anh.
7. **Amor Fati:** Chấp nhận vấp ngã, không làm bảo mẫu độc tài.
8. **MCP:** Mở rộng Tool vô hạn qua chuẩn USB-C của AI.

---

**HẾT BIÊN NIÊN SỬ**

*(Tài liệu này được trích xuất tự động từ toàn bộ lịch sử trò chuyện của dự án AMAZING-NOBEL, không rút gọn, không bỏ sót bất kỳ chi tiết nào.)*