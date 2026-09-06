"""bot/handlers/document.py -- Handle document uploads (.txt, .md) to extract context."""
import os
import json
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
import google.generativeai as genai

from config import settings
from db.database import AsyncSessionLocal
from db.models import CapabilityLog, Memory, PhysicalStatus, WorkProject
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

PROMPT_EXTRACT = """Bạn là trợ lý phân tích dữ liệu cá nhân.
Người dùng vừa tải lên một tài liệu chứa thông tin về bản thân họ.
Hãy đọc tài liệu và trích xuất thông tin thành định dạng JSON đúng cấu trúc sau:
{
  "physical_status": {
    "energy": 7,
    "mood": 7,
    "health": 7,
    "sleep_hours": 7.0,
    "notes": "Ghi chú về thể trạng, cân nặng, chiều cao, chấn thương..."
  },
  "capabilities": [
    {"domain": "Tên kỹ năng", "current_level": 7.0, "max_ever": 10.0, "unit": "đơn vị (nếu có)"}
  ],
  "projects": [
    {"name": "Tên dự án hoặc công việc", "progress_percent": 50}
  ],
  "memories": [
    "Lịch trình, thời gian biểu, mục tiêu, hoặc các thông tin quan trọng khác. Mỗi ý là một chuỗi string độc lập."
  ]
}

LƯU Ý QUAN TRỌNG:
- Trả về CHỈ JSON, không có markdown block ```json hay text nào khác.
- Nếu không có thông tin cho một phần, hãy để giá trị null (với physical_status) hoặc mảng rỗng [] (với capabilities, projects, memories).
- Đặc biệt chú ý BẢO TOÀN LỊCH TRÌNH VÀ THỜI GIAN BIỂU, hãy chia nhỏ mỗi mục lịch trình thành một chuỗi string riêng trong mảng memories.

VĂN BẢN TÀI LIỆU CẦN XỬ LÝ:
"""

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    filename = doc.file_name.lower() if doc.file_name else ""
    
    if not (filename.endswith('.txt') or filename.endswith('.md')):
        await message.reply_text("⚠️ Hiện tại tôi chỉ hỗ trợ phân tích file .txt hoặc .md.")
        return

    # Check file size (limit to 5MB to avoid overwhelming API or timeout)
    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        await message.reply_text("⚠️ File quá lớn. Vui lòng gửi file dưới 5MB.")
        return

    status_msg = await message.reply_text("⏳ Đang tải file và phân tích nội dung. Vui lòng chờ...")

    try:
        # Download file
        tg_file = await context.bot.get_file(doc.file_id)
        byte_array = await tg_file.download_as_bytearray()
        # Try different encodings for Windows txt files
        try:
            content = byte_array.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Notepad's "Unicode" format
                content = byte_array.decode('utf-16')
            except UnicodeDecodeError:
                # Vietnamese Windows or generic fallback
                try:
                    content = byte_array.decode('cp1258')
                except UnicodeDecodeError:
                    content = byte_array.decode('cp1252', errors='replace')
        
        if len(content.strip()) == 0:
            await status_msg.edit_text("⚠️ File trống.")
            return

        # Call Gemini LLM
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-3.8-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = PROMPT_EXTRACT + "\n" + content
        response = model.generate_content(prompt)
        result_json = response.text.strip()
        
        try:
            parsed_data = json.loads(result_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Gemini: {result_json}")
            await status_msg.edit_text("⚠️ Lỗi trích xuất dữ liệu từ AI. Hãy thử lại.")
            return

        # Save to Database
        tg_user = update.effective_user
        stats = {"caps": 0, "projs": 0, "mems": 0, "phys": False}
        
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
            
            # Physical Status
            phys_data = parsed_data.get("physical_status")
            if phys_data:
                session.add(PhysicalStatus(
                    user_id=user.id,
                    energy=phys_data.get("energy") if phys_data.get("energy") is not None else 5,
                    mood=phys_data.get("mood") if phys_data.get("mood") is not None else 5,
                    health=phys_data.get("health") if phys_data.get("health") is not None else 5,
                    sleep_hours=phys_data.get("sleep_hours") if phys_data.get("sleep_hours") is not None else 0.0,
                    notes=phys_data.get("notes") or ""
                ))
                stats["phys"] = True
                
            # Capabilities
            caps_data = parsed_data.get("capabilities", [])
            for cap in caps_data:
                session.add(CapabilityLog(
                    user_id=user.id,
                    domain=cap.get("domain") or "Unknown",
                    current_level=cap.get("current_level") if cap.get("current_level") is not None else 0.0,
                    max_ever=cap.get("max_ever") if cap.get("max_ever") is not None else 0.0,
                    unit=cap.get("unit") or ""
                ))
                stats["caps"] += 1
                
            # Projects
            projs_data = parsed_data.get("projects", [])
            for proj in projs_data:
                session.add(WorkProject(
                    user_id=user.id,
                    name=proj.get("name") or "Unknown",
                    progress_percent=proj.get("progress_percent") if proj.get("progress_percent") is not None else 0,
                    updated_at=datetime.utcnow()
                ))
                stats["projs"] += 1
                
            # Memories
            mems_data = parsed_data.get("memories", [])
            for mem in mems_data:
                if isinstance(mem, str) and len(mem.strip()) > 0:
                    session.add(Memory(user_id=user.id, content=mem.strip(), importance=10))
                    stats["mems"] += 1
                    
            await session.commit()
            
        # Send summary
        summary_lines = ["✅ **Đã phân tích và lưu file thành công!**", ""]
        if stats["phys"]:
            summary_lines.append("• Đã cập nhật 1 bản ghi Thể trạng.")
        if stats["caps"] > 0:
            summary_lines.append(f"• Đã lưu {stats['caps']} lĩnh vực Năng lực.")
        if stats["projs"] > 0:
            summary_lines.append(f"• Đã lưu {stats['projs']} Dự án.")
        if stats["mems"] > 0:
            summary_lines.append(f"• Đã lưu {stats['mems']} mục thông tin quan trọng/lịch trình (Memory).")
            
        await status_msg.edit_text("\n".join(summary_lines), parse_mode="Markdown")

    except Exception as exc:
        logger.error(f"Error handling document: {exc}", exc_info=True)
        await status_msg.edit_text("⚠️ Đã xảy ra lỗi trong quá trình phân tích file.")

def build_document_handler() -> MessageHandler:
    return MessageHandler(filters.Document.ALL, handle_document)
