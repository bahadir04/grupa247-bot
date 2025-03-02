import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import sqlite3
import datetime
import matplotlib.pyplot as plt
import io

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def setup_database():
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    # Guruh a'zolari uchun jadval
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  joined_date TEXT,
                  is_admin INTEGER DEFAULT 0,
                  attendance_rate REAL DEFAULT 0,
                  activity_points INTEGER DEFAULT 0)''')
    
    # Davomat jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT,
                  status TEXT)''')
    
    # O'zlashtirish jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS performance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  subject TEXT,
                  grade REAL,
                  date TEXT)''')
    
    # E'lonlar uchun jadval
    c.execute('''CREATE TABLE IF NOT EXISTS announcements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  text TEXT,
                  date TEXT,
                  author_id INTEGER)''')
    
    conn.commit()
    conn.close()

# Tugmalar
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistika", callback_data="statistics"),
            InlineKeyboardButton("📢 E'lonlar", callback_data="announcements")
        ],
        [
            InlineKeyboardButton("👥 A'zolar", callback_data="members"),
            InlineKeyboardButton("📝 Davomat", callback_data="attendance")
        ],
        [
            InlineKeyboardButton("📈 O'zlashtirish", callback_data="performance"),
            InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="about")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_statistics_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👥 A'zolar statistikasi", callback_data="members_stats"),
            InlineKeyboardButton("📝 Davomat statistikasi", callback_data="attendance_stats")
        ],
        [
            InlineKeyboardButton("📊 O'zlashtirish statistikasi", callback_data="performance_stats"),
            InlineKeyboardButton("⭐️ Faollik reytingi", callback_data="activity_stats")
        ],
        [
            InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # Foydalanuvchini bazaga qo'shish
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)',
              (user.id, user.username or user.first_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    welcome_text = (
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "24.7-gruppa botina xush kelibsiz!\n\n"
        "Bot imkoniyatlari:\n"
        "📢 reklama korinisi\n"
        "👥 Guruppa doslari haqqinda malomat\n"
        "ℹ️ Gurppa haqqinda malumat\n"
        "📝 Botdan paydalamiw qagiydasi\n\n"
        "tomendegi tuymelerden paydalanin 👇"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "statistics":
        await show_statistics_menu(update, context)
    elif query.data == "members_stats":
        await show_members_statistics(update, context)
    elif query.data == "attendance_stats":
        await show_attendance_statistics(update, context)
    elif query.data == "performance_stats":
        await show_performance_statistics(update, context)
    elif query.data == "activity_stats":
        await show_activity_statistics(update, context)
    elif query.data == "back_to_main":
        await show_main_menu(update, context)
    elif query.data == "announcements":
        await show_announcements(update, context)
    elif query.data == "members":
        await show_members(update, context)
    elif query.data == "attendance":
        await show_attendance(update, context)
    elif query.data == "performance":
        await show_performance(update, context)
    elif query.data == "about":
        await show_about(update, context)

async def show_statistics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    text = (
        "📊 Statistika bo'limi\n\n"
        "Quyidagi statistikalarni ko'rishingiz mumkin:\n"
        "👥 A'zolar statistikasi\n"
        "📝 Davomat statistikasi\n"
        "📊 O'zlashtirish statistikasi\n"
        "⭐️ Faollik reytingi"
    )
    await query.edit_message_text(text, reply_markup=get_statistics_keyboard())

async def show_members_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    
    # Umumiy a'zolar soni
    c.execute('SELECT COUNT(*) FROM users')
    total_members = c.fetchone()[0]
    
    # Bugungi yangi a'zolar
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    c.execute('SELECT COUNT(*) FROM users WHERE joined_date LIKE ?', (f"{today}%",))
    new_members_today = c.fetchone()[0]
    
    # Faol a'zolar (faollik bali 50 dan yuqori)
    c.execute('SELECT COUNT(*) FROM users WHERE activity_points > 50')
    active_members = c.fetchone()[0]
    
    conn.close()
    
    text = (
        "👥 A'zolar statistikasi\n\n"
        f"Umumiy a'zolar: {total_members} ta\n"
        f"Bugun qo'shilganlar: {new_members_today} ta\n"
        f"Faol a'zolar: {active_members} ta\n"
    )
    
    await query.edit_message_text(text, reply_markup=get_statistics_keyboard())

async def show_attendance_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    
    # O'rtacha davomat (foizda)
    c.execute('SELECT AVG(attendance_rate) FROM users')
    avg_attendance = c.fetchone()[0] or 0
    
    # Bugungi davomat
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    c.execute('''SELECT 
                 SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                 COUNT(*) as total
                 FROM attendance 
                 WHERE date LIKE ?''', (f"{today}%",))
    result = c.fetchone()
    today_attendance = f"{(result[0]/result[1]*100):.1f}%" if result[1] > 0 else "Ma'lumot yo'q"
    
    conn.close()
    
    text = (
        "📝 Davomat statistikasi\n\n"
        f"O'rtacha davomat: {avg_attendance:.1f}%\n"
        f"Bugungi davomat: {today_attendance}\n"
    )
    
    await query.edit_message_text(text, reply_markup=get_statistics_keyboard())

async def show_performance_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    
    # O'rtacha o'zlashtirish
    c.execute('SELECT AVG(grade) FROM performance')
    avg_grade = c.fetchone()[0] or 0
    
    # Fanlar bo'yicha o'rtacha baholar
    c.execute('''SELECT subject, AVG(grade) 
                 FROM performance 
                 GROUP BY subject''')
    subject_grades = c.fetchall()
    
    conn.close()
    
    text = "📊 O'zlashtirish statistikasi\n\n"
    text += f"Umumiy o'rtacha ball: {avg_grade:.1f}\n\n"
    text += "Fanlar bo'yicha:\n"
    for subject, grade in subject_grades:
        text += f"{subject}: {grade:.1f}\n"
    
    await query.edit_message_text(text, reply_markup=get_statistics_keyboard())

async def show_activity_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    
    # Top 5 eng faol a'zolar
    c.execute('''SELECT username, activity_points 
                 FROM users 
                 ORDER BY activity_points DESC 
                 LIMIT 5''')
    top_active = c.fetchall()
    
    conn.close()
    
    text = "⭐️ Faollik reytingi\n\n"
    text += "Top 5 eng faol a'zolar:\n"
    for i, (username, points) in enumerate(top_active, 1):
        text += f"{i}. {username}: {points} ball\n"
    
    await query.edit_message_text(text, reply_markup=get_statistics_keyboard())

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    welcome_text = (
        "Asosiy menyu\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇"
    )
    await query.edit_message_text(welcome_text, reply_markup=get_main_keyboard())

async def show_announcements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    c.execute('SELECT text, date FROM announcements ORDER BY id DESC LIMIT 5')
    announcements = c.fetchall()
    conn.close()
    
    if announcements:
        text = "📢 Songi reklammalar:\n\n"
        for ann in announcements:
            text += f"📅 {ann[1]}\n{ann[0]}\n\n"
    else:
        text = "❌ Hozirche reklama yo'q"
    
    await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def show_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users')
    members = c.fetchall()
    conn.close()
    
    text = "👥 Gurrupa adamlari:\n\n"
    for i, member in enumerate(members, 1):
        text += f"{i}. {member[0]}\n"
    
    await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def show_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    c.execute('SELECT date, status FROM attendance ORDER BY id DESC LIMIT 5')
    attendance = c.fetchall()
    conn.close()
    
    if attendance:
        text = "📝 Davomat:\n\n"
        for att in attendance:
            text += f"📅 {att[0]}\n{att[1]}\n\n"
    else:
        text = "❌ Hozirche davomat yo'q"
    
    await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def show_performance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    conn = sqlite3.connect('grupa247.db')
    c = conn.cursor()
    c.execute('SELECT subject, grade, date FROM performance ORDER BY id DESC LIMIT 5')
    performance = c.fetchall()
    conn.close()
    
    if performance:
        text = "📈 O'zlashtirish:\n\n"
        for perf in performance:
            text += f"📚 {perf[0]}\n{perf[1]}\n📅 {perf[2]}\n\n"
    else:
        text = "❌ Hozirche o'zlashtirish yo'q"
    
    await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    about_text = (
        "ℹ️ Guruh haqida:\n\n"
        "📚 247-guruh\n"
        "👨‍🎓 2024-yil talabalari\n"
        "📱 Guruh boti orqali siz:\n"
        "  • E'lonlarni ko'rishingiz\n"
        "  • A'zolar ro'yxatini ko'rishingiz\n"
        "  • Ma'lumotlar olishingiz mumkin"
    )
    await query.edit_message_text(about_text, reply_markup=get_main_keyboard())

def main():
    setup_database()
    TOKEN = "7618719573:AAFsLD0bdYCB8acBlcFfCaA9QLoavtsFiyI"
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
