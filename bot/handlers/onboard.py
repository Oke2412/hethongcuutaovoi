"""bot/handlers/onboard.py -- Modern onboarding via LLM / Document."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def start_onboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 **Hệ thống Onboarding đã được nâng cấp!**\n\n"
        "Để mang lại trải nghiệm tiện lợi như Jarvis, hệ thống hỏi-đáp thủ công đã được gỡ bỏ.\n\n"
        "Ngài chỉ cần làm 1 trong 2 cách sau để cập nhật thông tin hệ thống:\n"
        "1. **Gửi File Text (.txt / .md):** Chứa thông tin về Thể trạng, Kỹ năng, Dự án. AI sẽ tự động đọc và nạp vào não bộ.\n"
        "2. **Ra lệnh bằng Chat:** Chat trực tiếp với tôi (VD: _'Raphael, tạo dự án TurtleBot tiến độ 20%'_ hoặc _'Tôi vừa cập nhật kỹ năng FreeCAD'_).\n\n"
        "Tôi luôn sẵn sàng lắng nghe mọi chỉ thị, thưa ngài!",
        parse_mode="Markdown"
    )

def build_onboard_handler() -> CommandHandler:
    return CommandHandler("onboard", start_onboard)
