---
name: create-agent-tui
description: Scaffolds a complete agent TUI in TypeScript using @openrouter/agent — like create-react-app for terminal agents. Generates a customizable terminal interface with three input styles, four tool display modes, ASCII banners, streaming output, session persistence, and configurable tools. Use when building an agent, creating a TUI, scaffolding an agent project, or building a coding assistant.
---

# Create Agent TUI (OpenRouter Agent SDK)

Kỹ năng này cung cấp kiến thức về cách xây dựng một hệ thống Agent tương tác qua dòng lệnh (TUI) bằng TypeScript sử dụng `@openrouter/agent` SDK.

## 1. Tổng quan Kiến Trúc
SDK của OpenRouter tập trung vào việc quản lý vòng lặp nội tại (inner loop) của Agent:
- Quản lý cuộc gọi Model (callModel).
- Khai báo và thực thi Tools.
- Quản lý điều kiện dừng (stop conditions).
- Quản lý trạng thái hội thoại (conversation state) tự động.

Kiến trúc TUI thường được chia thành 3 lớp (3-layer separation):
1. **Model Layer**: Kết nối OpenRouter API, phân tích dữ liệu trả về.
2. **Tool Layer**: Chứa các Server Tools (do OpenRouter thực thi như Web Search, Bash) và Client Tools (do local machine thực thi như Read File, Run Script).
3. **UI/Shell Layer**: Giao diện dòng lệnh (TUI) hỗ trợ hiển thị luồng dữ liệu (streaming output), theo dõi trạng thái Tool (loader, tool display modes), và quản lý session bằng file JSONL.

## 2. Server Tools vs Client Tools
- **Server Tools**: Các Tool được OpenRouter hỗ trợ sẵn mà Agent không cần code logic thực thi (chỉ cần truyền tên `openrouter:web_search`, `openrouter:datetime`).
- **Client Tools**: Các Tool tự định nghĩa bằng `@openrouter/agent/tool` (VD: Đọc file, Ghi file). Trình thực thi (Executor) sẽ hứng request từ Model và chạy hàm callback trên máy local.

## 3. Slash Commands & Input Styles
Hỗ trợ các lệnh điều hướng trực tiếp:
- `/model`: Chuyển đổi mô hình (ví dụ: `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`).
- `/new`: Khởi tạo session mới.
- Các Input Styles: `block`, `bordered`, `plain`.

## 4. Ứng dụng vào hệ thống Amazing Nobel
Hiện tại Amazing Nobel đang chạy bằng **Python (FastAPI)** và không thể xài trực tiếp npm package `@openrouter/agent`.
Tuy nhiên, chúng ta có thể:
1. **Khởi tạo TUI riêng lẻ**: Chạy song song một công cụ dòng lệnh (TUI) bằng TypeScript/Node.js để tương tác với Server hoặc thao tác với Database chung.
2. **Học hỏi tư duy thiết kế (Agent Loop)**: Tự mô phỏng lại cơ chế `callModel`, tự động lưu trạng thái bằng JSONL/Mem0, thiết kế lớp Tool Calling tách biệt và hiển thị UI loader tương tự trên Python.
3. **Chuyển đổi Backend sang TS (Không khuyến khích)**: Trừ khi ngài muốn đập đi xây lại toàn bộ codebase Python sang TypeScript.
