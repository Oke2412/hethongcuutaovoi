
### [2026-09-07 02:26] — Cấu hình Docker Neo4j & Nhận thức Thời gian thực
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** viết xong docker chưa? / nó biết xem giờ không / brainstorm với gg ra GraphRAG Neo4j
**Kết quả / Quyết định:**
- Nâng cấp `docker-compose.yml`: Bổ sung Container `neo4j` để chuẩn bị cho kiến trúc GraphRAG (Mạng Đồ thị Ký ức). Đồng thời mount volume cho `chroma_db` để lưu trữ Vector offline không bị mất khi restart.
- Nâng cấp Nhận thức Thời gian (`core/llm.py`): Inject trực tiếp `datetime.now()` vào đầu System Prompt mỗi khi gọi LLM. Giờ đây Raphael đã hoàn toàn nhận thức được Thời gian và Ngày tháng thực tế để đưa ra cảnh báo chính xác (vd: "Đã 23h, yêu cầu đi ngủ").
- Thay đổi chuẩn Log: Từ phiên bản này, lịch sử Prompt sẽ được lưu thành các file độc lập trong thư mục `docs/prompt_history/` để tránh Git Conflict khi chạy nhiều Agent song song.
- Đã push nhánh `feature/graphrag-and-docker`.
**Files thay đổi:** docker-compose.yml, core/llm.py, docs/prompt_history/20260907_0226_graphrag_docker.md
---
