import logging
import random
import string
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.llm_tools import reset_database_async

logger = logging.getLogger(__name__)

# Temporary in-memory storage for reset OTPs
# Format: {user_id: "OTP"}
RESET_PENDING = {}

async def handle_reset_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /reset_db command."""
    user_id = update.effective_user.id
    
    # Generate a 6-character random alphanumeric key
    otp = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    RESET_PENDING[user_id] = otp
    
    warning_msg = (
        "⚠️ [CẢNH BÁO NGUY HIỂM] ⚠️\\n\\n"
        "Ngài đang yêu cầu HỦY DIỆT TOÀN BỘ CƠ SỞ DỮ LIỆU. Hành động này sẽ xóa sạch:\\n"
        "- Cấp độ, Kinh nghiệm, Tín chỉ\\n"
        "- Lịch sử dự án, trạng thái thể chất\\n"
        "- Ký ức ngắn hạn (SQLite)\\n\\n"
        f"Nếu ngài thực sự muốn làm điều này, hãy nhập lệnh sau để xác nhận:\\n"
        f"`/confirm_reset {otp}`\\n\\n"
        "Mã xác nhận này sẽ mất hiệu lực nếu ngài không sử dụng."
    )
    
    await update.message.reply_text(warning_msg, parse_mode="Markdown")

async def handle_confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /confirm_reset <otp> command."""
    user_id = update.effective_user.id
    
    if user_id not in RESET_PENDING:
        await update.message.reply_text("❌ Không có yêu cầu Reset nào đang chờ.")
        return
        
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("❌ Vui lòng nhập mã xác nhận. Ví dụ: `/confirm_reset ABC123`", parse_mode="Markdown")
        return
        
    user_otp = context.args[0].upper()
    correct_otp = RESET_PENDING[user_id]
    
    if user_otp != correct_otp:
        await update.message.reply_text("❌ Mã xác nhận không hợp lệ. Hủy bỏ quá trình Reset.")
        del RESET_PENDING[user_id]
        return
        
    # Execute reset
    status_msg = await update.message.reply_text("⏳ [Đang tiến hành HỦY DIỆT dữ liệu...]")
    
    try:
        from db.database import AsyncSessionLocal
        from core.memory import get_or_create_user
        
        async with AsyncSessionLocal() as session:
            telegram_user = update.effective_user
            user = await get_or_create_user(session, telegram_user.id, telegram_user.full_name, telegram_user.username)
            internal_user_id = user.id
            
        # Call the existing tool to wipe SQLite
        result = await reset_database_async(internal_user_id)
        
        # Clear the OTP
        del RESET_PENDING[user_id]
        
        await status_msg.edit_text(f"✅ [HOÀN TẤT]\n{result}")
    except Exception as exc:
        logger.error(f"Error resetting DB: {exc}", exc_info=True)
        await status_msg.edit_text("⚠️ Đã xảy ra lỗi hệ thống khi đang reset.")

def build_reset_handlers() -> list[CommandHandler]:
    return [
        CommandHandler("reset_db", handle_reset_request),
        CommandHandler("confirm_reset", handle_confirm_reset)
    ]
