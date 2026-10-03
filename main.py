import os
import logging
import threading
import asyncio
from flask import Flask
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    BotCommand
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ----------------------------------------------------
# 0. إعداد خادم Flask لمنع الخمول على Render
# ----------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Maker Engine is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ----------------------------------------------------
# 1. إعداد المتغيرات وقواعد البيانات
# ----------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "894155326"))

users_db = set()
created_bots = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------------------------------------------
# 2. لوحة تحكم المطوّر الرئيسي (ADMIN_ID فقط)
# ----------------------------------------------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    admin_text = (
        "👑 **لوحة تحكم المالك الرئيسي**\n"
        "━━━━━━━ ⚙️ ━━━━━━━\n\n"
        "مرحباً بك في لوحة الإدارة الذكية الخاص بـ Bot Maker."
    )

    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="admin_stats")],
        [InlineKeyboardButton("📜 قائمة المستخدمين", callback_data="admin_users_list")],
        [InlineKeyboardButton("📢 إذاعة للمشاركين (محتكرة للادمن)", callback_data="admin_broadcast_all")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="Markdown")

# ----------------------------------------------------
# 3. صانع البوتات الرئيسي
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_db.add(user.id)

    if user.id == ADMIN_ID and context.args and context.args[0] == "admin":
        await admin_panel(update, context)
        return

    welcome_text = (
        f"✨ **أهلاً وسهلاً بك يا {user.first_name} في صانع بوتات التواصل!** 🌸✨\n\n"
        "🚀 **مميزات الخدمة:**\n"
        "✅ بدون حقوق ومجانية 100%\n"
        "⚡ بدون إعلانات مزعجة وسريعة الاستجابة\n\n"
        "📌 **اختر نوع البوت الذي تريد إنشاءه الآن:**"
    )

    # أزرار شفافة داخل الرسالة
    inline_keyboard = [
        [InlineKeyboardButton("🚀 اصنع بوتك بدون حقوق الآن", url="https://t.me/Contact_lbot")],
        [InlineKeyboardButton("1️⃣ صنع بوت مراسلة عادي (بلا ميزة الرسائل المجهولة)", callback_data="create_normal")],
        [InlineKeyboardButton("2️⃣ صنع بوت مراسلة عادي + ميزة المجهول 🕵️‍♂️", callback_data="create_anon")],
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    # أزرار سفلية دائمة (Reply Keyboard)
    reply_keyboard = [
        [KeyboardButton("🤖 إنشاء بوت جديد"), KeyboardButton("📢 إذاعة للمشاركين")]
    ]
    reply_markup_reply = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, persistent=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup_inline, parse_mode="Markdown")
    await update.message.reply_text("القائمة الرئيسية متوفرة بالأسفل 👇", reply_markup=reply_markup_reply)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in ["create_normal", "create_anon"]:
        context.user_data['bot_type'] = data
        text = (
            "⚙️ **خطوة إنشاء البوت:**\n\n"
            "يرجى إرسال **التوكن (Token)** الخاص ببوتك الآن من بوت فاذر (@BotFather).\n\n"
            "👇 إذا كنت لا تعرف كيفية جلب التوكن اضغط على الزر أسفله:"
        )
        keyboard = [[InlineKeyboardButton("❓ كيف أحصل على التوكن؟", callback_data="how_to_token")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "how_to_token":
        tutorial = (
            "📖 **طريقة الحصول على توكن من @BotFather:**\n\n"
            "1. ادخل إلى بوت فاذر الرسمي: @BotFather\n"
            "2. أرسل الأمر `/newbot`\n"
            "3. اكتب اسماً لبوتك ثم اختر يوزرنيم ينتهي بـ `bot`\n"
            "4. سيقوم BotFather بإرسال نص التوكن\n"
            "5. انسخ التوكن وأرسله هنا مباشرة!"
        )
        await query.message.reply_text(tutorial, parse_mode="Markdown")

    elif data == "admin_stats" and query.from_user.id == ADMIN_ID:
        await query.message.reply_text(f"📊 **عدد مستخدمي البوت الإجمالي:** `{len(users_db)}`", parse_mode="Markdown")

    elif data == "admin_users_list" and query.from_user.id == ADMIN_ID:
        users_str = "📜 **قائمة مستخدمي البوت:**\n\n"
        for uid in list(users_db)[:50]:
            users_str += f"• ID: `{uid}`\n"
        await query.message.reply_text(users_str, parse_mode="Markdown")

    elif data == "admin_broadcast_all":
        if query.from_user.id == ADMIN_ID:
            context.user_data['admin_action'] = 'broadcast_all'
            await query.message.reply_text("📢 أرسل الرسالة التي تريد إشعار جميع المستخدمين بها:")
        else:
            await query.message.reply_text("❌ ميزة الإذاعة محتكرة للأدمن الرئيسي فقط!")

async def handle_message_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # الأزرار السفلية
    if text == "🤖 إنشاء بوت جديد":
        await update.message.reply_text(
            "لإنشاء بوت جديد، قم بالتواصل مع صانع البوتات عبر الرابط الرسمي:\n👉 @Contact_lbot"
        )
        return

    elif text == "📢 إذاعة للمشاركين":
        if user_id == ADMIN_ID:
            context.user_data['admin_action'] = 'broadcast_all'
            await update.message.reply_text("📢 **أهلاً بك يا أدمن.** أرسل الآن نص الإذاعة لإرساله لجميع المستخدمين:")
        else:
            await update.message.reply_text("❌ عذراً، هذه الميزة محتكرة ومخصصة لمالك البوت الرئيسي فقط ولا يمكن استغلالها من البوتات الأخرى.")
        return

    # إجراء الإذاعة خاص بالأدمن فقط
    if context.user_data.get('admin_action') == 'broadcast_all':
        if user_id == ADMIN_ID:
            context.user_data['admin_action'] = None
            count = 0
            for u in users_db:
                try:
                    await context.bot.send_message(chat_id=u, text=f"📢 **إشعار من الإدارة:**\n\n{text}", parse_mode="Markdown")
                    count += 1
                except Exception:
                    pass
            await update.message.reply_text(f"✅ تم إرسال الإذاعة إلى {count} مستخدم.")
        else:
            await update.message.reply_text("❌ غير مصرح لك بالتنفيذ.")
        return

    # استقبال التوكن
    if ":" in text and len(text) > 20:
        bot_type = context.user_data.get('bot_type', 'create_normal')
        allow_anon = (bot_type == "create_anon")

        try:
            sub_app = Application.builder().token(text).build()
            setup_child_bot(sub_app, owner_id=user_id, allow_anonymous=allow_anon)

            await sub_app.initialize()
            await sub_app.start()
            await sub_app.updater.start_polling(drop_pending_updates=True)

            created_bots[text] = {
                'owner_id': user_id,
                'allow_anonymous': allow_anon,
                'app': sub_app
            }

            await update.message.reply_text(
                f"🎉 **تم إنشاء وتفعيل بوتك بنجاح!**\n\n"
                f"👤 **صاحب البوت (الأيدي):** `{user_id}`\n"
                f"🕵️‍♂️ **خاصية الرسائل المجهولة:** {'مفعلة ✅' if allow_anon else 'معطلة ❌'}\n\n"
                f"يمكنك الآن مشاركة رابط بوتك للبدء في استقبال الرسائل!",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء تشغيل البوت، تأكد من صحة التوكن!\n\nالتفاصيل: `{e}`", parse_mode="Markdown")

# ----------------------------------------------------
# 4. محرك البوت الفرعي (المصنوع)
# ----------------------------------------------------
def setup_child_bot(app: Application, owner_id: int, allow_anonymous: bool):

    async def child_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if user.id == owner_id:
            await update.message.reply_text(
                "👑 **أهلاً بك يا صاحب البوت!**\n"
                "هذا البوت جاهز لاستقبال الرسائل وتحويلها إليك مباشرة.\n"
                "عندما يراسلك أحد يمكنك الرد عليه بالضغط على **Reply (رد)** في التلغرام!"
            )
            return

        welcome_child = (
            f"✨ **أهلاً بك في بوت التواصل!**\n"
            "اختر طبيعة الرسالة التي تريد إرسالها لصاحب البوت:"
        )

        keyboard = [
            [InlineKeyboardButton("🚀 اصنع بوتك بدون حقوق الآن", url="https://t.me/Contact_lbot")],
            [InlineKeyboardButton("💬 إرسال رسالة عادية", callback_data="send_normal")],
        ]
        if allow_anonymous:
            keyboard.append([InlineKeyboardButton("🕵️‍♂️ إرسال رسالة مجهولة الهوية", callback_data="send_anon")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_child, reply_markup=reply_markup, parse_mode="Markdown")

    async def child_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "send_normal":
            context.user_data['msg_type'] = 'normal'
            await query.message.reply_text("✍️ اكتب رسالتك العادية الآن وسأقوم بنقلها:")
        elif data == "send_anon":
            context.user_data['msg_type'] = 'anon'
            await query.message.reply_text("🕵️‍♂️ اكتب رسالتك المجهولة الآن (لن يعرف المالك هويتك):")

    async def child_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if user.id == owner_id and update.message.reply_to_message:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
            target_id = None

            if "ID:" in reply_text:
                try:
                    target_id = int(reply_text.split("ID:")[1].split()[0].strip("`"))
                except Exception:
                    pass

            if target_id:
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"💬 **وصلك رد من صاحب البوت:**\n\n{update.message.text}",
                        parse_mode="Markdown"
                    )
                    await update.message.reply_text("✅ تم إرسال ردك بنجاح!")
                except Exception:
                    await update.message.reply_text("❌ متعذر إرسال الرد، ربما قام الشخص بحظر البوت.")
            else:
                await update.message.reply_text("❌ لم يتم التعرف على أيدي المرسل الأصلي.")
            return

        msg_type = context.user_data.get('msg_type', 'normal')

        if msg_type == 'normal':
            user_info = (
                f"📩 **رسالة جديدة عادية:**\n"
                f"👤 **الاسم:** {user.full_name}\n"
                f"🔗 **اليوزر:** @{user.username if user.username else 'لا يوجد'}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"-----------------------------\n"
                f"{update.message.text}"
            )
            await context.bot.send_message(chat_id=owner_id, text=user_info, parse_mode="Markdown")
            await update.message.reply_text("✅ تم إرسال رسالتك العادية بنجاح!")

        elif msg_type == 'anon':
            anon_info = (
                f"🕵️‍♂️ **رسالة جديدة (مجهولة الهوية):**\n"
                f"⚠️ *أرسل صاحب هذه الرسالة الهوية بشكل مخفي.*\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"-----------------------------\n"
                f"{update.message.text}"
            )
            await context.bot.send_message(chat_id=owner_id, text=anon_info, parse_mode="Markdown")
            await update.message.reply_text("✅ تم إرسال رسالتك المجهولة بنجاح!")

    app.add_handler(CommandHandler("start", child_start))
    app.add_handler(CallbackQueryHandler(child_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, child_message_handler))

# ----------------------------------------------------
# 5. تشغيل السيرفر والبوت معاً
# ----------------------------------------------------
async def main_async():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_master))

    print("🚀 تم تشغيل البوت وخادم الويب بنجاح...")

    async with app:
        await app.start()
        
        # ضبط أوامر البوت بأمان أثناء العمل
        try:
            commands = [
                BotCommand("start", "فتح القائمة الرئيسية"),
                BotCommand("admin", "فتح لوحة التحكم الإدارية"),
            ]
            await app.bot.set_my_commands(commands)
        except Exception as e:
            print(f"Warning setting commands: {e}")

        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
