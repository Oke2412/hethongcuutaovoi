"""bot/handlers/document.py -- Handle document uploads (.txt, .md)."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user
from core.brain import brain

logger = logging.getLogger(__name__)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    filename = doc.file_name.lower() if doc.file_name else ""
    
    if not (filename.endswith('.txt') or filename.endswith('.md')):
        await message.reply_text("⚠️ Hiện tại tôi chỉ hỗ trợ phân tích file .txt hoặc .md.")
        return

    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        await message.reply_text("⚠️ File quá lớn. Vui lòng gửi file dưới 5MB.")
        return

    status_msg = await message.reply_text("⏳ Đang nạp tài liệu vào bộ não AI. Vui lòng chờ...")

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        byte_array = await tg_file.download_as_bytearray()
        
        try:
            content = byte_array.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = byte_array.decode('utf-16')
            except UnicodeDecodeError:
                try:
                    content = byte_array.decode('cp1258')
                except UnicodeDecodeError:
                    content = byte_array.decode('cp1252', errors='replace')
        
        if len(content.strip()) == 0:
            await status_msg.edit_text("⚠️ File trống.")
            return

        tg_user = update.effective_user
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
            
        prompt = f"[Tài liệu đính kèm: {doc.file_name}]\n{content}\n\nHãy phân tích tài liệu này và tự động lưu các thông tin quan trọng (dự án, năng lực, lịch trình) vào hệ thống bằng Tools."
        
        response = await brain.process_input(user_id=str(user.id), text_content=prompt)
        await status_msg.edit_text(response)

    except Exception as exc:
        logger.error(f"Error handling document: {exc}", exc_info=True)
        await status_msg.edit_text("⚠️ Đã xảy ra lỗi trong quá trình phân tích file.")

def build_document_handler() -> MessageHandler:
    return MessageHandler(filters.Document.ALL, handle_document)
