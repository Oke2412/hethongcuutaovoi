import asyncio
import os
import logging
from mcp.server import Server
import mcp.server.stdio

# Cấu hình log để tiện theo dõi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Khởi tạo MCP Server tên là "raphael-fs"
app = Server("raphael-fs")

# --- DANH SÁCH TOOLS (CÔNG CỤ) CỦA MCP ---

@app.tool()
async def read_local_file(filepath: str) -> str:
    """
    [MCP Tool] Đọc nội dung của một file trong dự án. 
    Chỉ dùng để soi mã nguồn hoặc đọc file log.
    """
    # BẢO MẬT: Khóa chặt đường dẫn, không cho AI vươn ra ngoài thư mục dự án
    allowed_dir = os.path.abspath(os.getcwd())
    target_path = os.path.abspath(filepath)
    
    if not target_path.startswith(allowed_dir):
        return f"《Báo Động》 Cố gắng truy cập ngoài vùng an toàn: {target_path}"

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.info(f"Đã cấp quyền đọc file: {filepath}")
            return content
    except FileNotFoundError:
        return f"《Lỗi》 Không tìm thấy file: {filepath}"
    except Exception as e:
        return f"《Lỗi》 Lỗi không xác định: {str(e)}"

# Chạy Server giao tiếp qua Stdio (Chuẩn mặc định của MCP)
async def main():
    logger.info("Bắt đầu khởi động MCP Server (File System)...")
    # Tích hợp vào hệ thống luồng I/O tiêu chuẩn
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
