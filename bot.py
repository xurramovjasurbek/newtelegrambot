import os
import json
from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split()))

TESTS_DIR = "tests"
ANSWERS_FILE = "answers.json"
os.makedirs(TESTS_DIR, exist_ok=True)

user_data = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ismingizni kiriting:")
    user_data[update.effective_user.id] = {"state": "waiting_name"}

# Ism qabul qilish
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_data.get(uid, {}).get("state") == "waiting_name":
        user_data[uid]["name"] = update.message.text
        user_data[uid]["state"] = "ready"
        await update.message.reply_text(f"Salom, {update.message.text}!
/testlar ni ko‘rish uchun buyrug‘ni bering.")

# /testlar
async def testlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = os.listdir(TESTS_DIR)
    if not files:
        await update.message.reply_text("Testlar mavjud emas.")
        return
    msg = "📚 Mavjud testlar:\n"
    for i, file in enumerate(files, 1):
        msg += f"{i}. {file}\n"
    await update.message.reply_text(msg)

# /test 1
async def send_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        return await update.message.reply_text("Foydalanish: /test 1")
    try:
        idx = int(args[0]) - 1
        file = os.listdir(TESTS_DIR)[idx]
        with open(os.path.join(TESTS_DIR, file), "rb") as f:
            await update.message.reply_document(document=InputFile(f), filename=file)
    except:
        await update.message.reply_text("❌ Test topilmadi.")

# /javob ABCDA...
async def javob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = user_data.get(uid, {}).get("name")
    if not name:
        return await update.message.reply_text("Avval /start orqali ismingizni kiriting.")
    if not context.args:
        return await update.message.reply_text("Foydalanish: /javob ABCDA...")

    user_ans = "".join(context.args).upper()
    try:
        with open(ANSWERS_FILE, "r") as f:
            answers = json.load(f)
        key = list(answers.values())[0]
        correct = sum(1 for u, a in zip(user_ans, key) if u == a)
        percent = round(correct / len(key) * 100)
        await update.message.reply_text(f"{name}, natijangiz: {correct}/{len(key)} ({percent}%)")
    except:
        await update.message.reply_text("❌ Javoblarni tekshirishda xatolik yuz berdi.")

# Admin fayl yuklaydi
async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    document = update.message.document
    file_name = document.file_name
    file = await document.get_file()
    await file.download_to_drive(os.path.join(TESTS_DIR, file_name))
    await update.message.reply_text(f"✅ {file_name} yuklandi.")

# Bot ishga tushurish
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("testlar", testlar))
    app.add_handler(CommandHandler("test", send_test))
    app.add_handler(CommandHandler("javob", javob))
    app.add_handler(MessageHandler(filters.Document.ALL, upload_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == '__main__':
    main()
