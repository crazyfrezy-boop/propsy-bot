import os
import asyncio
import logging
import datetime
from datetime import datetime as dt
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from database import Database
from calendar_api import CalendarAPI
from ai_utils import AIUtils
from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, SHEET_ID, CALENDAR_EMAIL, PAYMENT_LINK, SUBSCRIPTION_PRICE, TRIAL_DAYS, WHITELIST

# Инициализация
db = Database()
calendar = CalendarAPI()
ai = AIUtils()

logging.basicConfig(level=logging.INFO)

def has_access(user_id: int) -> bool:
    if user_id in WHITELIST:
        return True
    return db.check_subscription(user_id)

user_states = {}

# ========== КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        keyboard = [
            [InlineKeyboardButton("🧠 Я психолог", callback_data='register_psychologist')],
            [InlineKeyboardButton("👤 Я клиент", callback_data='register_client')]
        ]
        await update.message.reply_text(
            "🌟 Добро пожаловать в ProPsy Bot! 🌟\n\nЭто AI-ассистент для психологов и их клиентов.\n\nКто вы?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await show_main_menu(update, context, user)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict):
    user_id = update.effective_user.id
    role = user.get('role')
    
    if role == 'psychologist':
        if has_access(user_id):
            keyboard = [
                [InlineKeyboardButton("👥 Мои клиенты", callback_data='my_clients')],
                [InlineKeyboardButton("➕ Добавить клиента", callback_data='add_client')],
                [InlineKeyboardButton("💳 Подписка", callback_data='subscription')]
            ]
            await update.message.reply_text(
                f"🧠 Панель психолога\n\nЗдравствуйте, {user.get('name')}!\n\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [[InlineKeyboardButton("💳 Оплатить подписку", url=PAYMENT_LINK)]]
            await update.message.reply_text(
                f"⏰ Пробный период закончился\n\nЧтобы продолжить, оформите подписку: ${SUBSCRIPTION_PRICE}/мес\n\nПосле оплаты нажмите /confirm_payment",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        psychologist_id = user.get('psychologist_id')
        psychologist = db.get_user(psychologist_id) if psychologist_id else None
        psy_name = psychologist.get('name', 'ваш психолог') if psychologist else 'ваш психолог'
        
        keyboard = [
            [InlineKeyboardButton("📝 Записаться на сессию", callback_data='book_session')],
            [InlineKeyboardButton("📊 Мой дневник", callback_data='my_diary')],
            [InlineKeyboardButton("✅ Мои задания", callback_data='my_tasks')]
        ]
        await update.message.reply_text(
            f"👋 Добрый день, {user.get('name')}!\n\nВаш психолог: {psy_name}\n\nЧто хотите сделать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ========== РЕГИСТРАЦИЯ ==========

async def register_psychologist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'reg_psy_name'}
    await update.callback_query.message.reply_text(
        "📝 Регистрация психолога\n\nВведите ваше имя и фамилию:"
    )

async def register_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'reg_client_name'}
    
    psychologists = db.get_psychologists()
    if not psychologists:
        await update.callback_query.message.reply_text("😔 Пока нет зарегистрированных психологов. Попробуйте позже.")
        return
    
    keyboard = []
    for psy in psychologists:
        keyboard.append([InlineKeyboardButton(psy['name'], callback_data=f'select_psy_{psy["user_id"]}')])
    
    await update.callback_query.message.reply_text(
        "📝 Регистрация клиента\n\nВыберите вашего психолога:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def select_psychologist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, psy_id = query.data.split('_')
    user_id = query.from_user.id
    user_states[user_id] = {'action': 'reg_client_name', 'psychologist_id': int(psy_id)}
    await query.message.reply_text("📝 Введите ваше имя и фамилию:")

# ========== КАРТОЧКА КЛИЕНТА ==========

async def client_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    client_id = int(query.data.split('_')[1])
    client = db.get_user(client_id)
    
    if not client:
        await query.edit_message_text("❌ Клиент не найден.")
        return
    
    tasks = db.get_client_tasks(client_id, only_active=True)
    
    text = f"👤 Карточка клиента\n\n"
    text += f"📛 Имя: {client.get('name', '—')}\n"
    text += f"📞 Телефон: {client.get('phone', '—')}\n"
    text += f"📅 Сессий проведено: {client.get('sessions', 0)}\n"
    text += f"📝 Активных заданий: {len(tasks)}\n\n"
    
    if tasks:
        text += "Текущие задания:\n"
        for task in tasks[:3]:
            text += f"• {task.get('text', '—')[:50]}...\n"
    else:
        text += "Нет активных заданий.\n"
    
    keyboard = [
        [InlineKeyboardButton("📝 Отправить задание", callback_data=f'task_{client_id}')],
        [InlineKeyboardButton("🔙 Назад", callback_data='my_clients')]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_task_to_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    client_id = int(query.data.split('_')[1])
    psychologist_id = update.effective_user.id
    
    user_states[psychologist_id] = {'action': 'send_task', 'client_id': client_id}
    
    await query.edit_message_text(
        "📝 Отправка задания\n\nВведите текст задания для клиента:"
    )

# ========== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ==========

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    print(f"🔍 handle_all_messages: user_id={user_id}, text={text}")
    
    if user_id not in user_states:
        await update.message.reply_text("Извините, я не понимаю. Пожалуйста, используйте кнопки меню.")
        return
    
    action = user_states[user_id].get('action')
    print(f"🔍 action = {action}")
    
    # Регистрация психолога - имя
    if action == 'reg_psy_name':
        db.create_user(user_id, text, 'psychologist')
        user_states[user_id] = {'action': 'reg_psy_phone'}
        await update.message.reply_text("📞 Введите ваш телефон (можно пропустить, отправьте '-'):")
    
    # Регистрация психолога - телефон
    elif action == 'reg_psy_phone':
        if text != '-':
            db.update_user_phone(user_id, text)
        del user_states[user_id]
        await update.message.reply_text(
            f"✅ Регистрация завершена!\n\nТеперь вы можете добавлять клиентов.\nИспользуйте /start.\n\nПробный период: {TRIAL_DAYS} дней бесплатно."
        )
    
    # Регистрация клиента - имя
    elif action == 'reg_client_name':
        psychologist_id = user_states[user_id].get('psychologist_id')
        db.create_user(user_id, text, 'client', psychologist_id)
        del user_states[user_id]
        await update.message.reply_text(
            "✅ Регистрация завершена!\n\nТеперь вы можете записываться на сессии.\nИспользуйте /start."
        )
    
    # Добавление клиента - имя
    elif action == 'add_client_name':
        client_id = db.create_user(None, text, 'client', user_id)
        if client_id:
            user_states[user_id] = {'action': 'add_client_phone', 'client_id': client_id}
            await update.message.reply_text("📞 Введите телефон клиента (можно пропустить, отправьте '-'):")
        else:
            await update.message.reply_text("❌ Ошибка при создании клиента. Попробуйте ещё раз.")
    
    # Добавление клиента - телефон
    elif action == 'add_client_phone':
        client_id = user_states[user_id].get('client_id')
        if text != '-':
            db.update_user_phone(client_id, text)
        del user_states[user_id]
        await update.message.reply_text(
            f"✅ Клиент добавлен!\n\nОтправьте ему ссылку: @{context.bot.username}"
        )
    
    # Отправка задания клиенту
    elif action == 'send_task':
        client_id = user_states[user_id].get('client_id')
        task_id = db.add_task(client_id, text, user_id)
        
        client = db.get_user(client_id)
        if client:
            try:
                await context.bot.send_message(
                    client_id,
                    f"📝 Новое задание от психолога\n\n{text}\n\nВыполните, пожалуйста, к следующей сессии. 🌿"
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление клиенту: {e}")
        
        del user_states[user_id]
        await update.message.reply_text(
            "✅ Задание отправлено!\n\nКлиент получит уведомление."
        )
    
    else:
        print(f"❌ Неизвестное действие: {action}")
        await update.message.reply_text("Извините, я не понимаю. Пожалуйста, используйте кнопки меню.")

# ========== ДЕЙСТВИЯ С КНОПОК ==========

async def add_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"🔍 add_client: user_id={user_id}")
    
    if not has_access(user_id):
        await update.callback_query.message.reply_text(
            f"⏰ Пробный период закончился\n\nОформите подписку: ${SUBSCRIPTION_PRICE}/мес\n\nСсылка: {PAYMENT_LINK}"
        )
        return
    
    user_states[user_id] = {'action': 'add_client_name'}
    await update.callback_query.message.reply_text(
        "👤 Добавление клиента\n\nВведите имя и фамилию клиента:"
    )

async def my_clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"🔍 my_clients: user_id={user_id}")
    
    if not has_access(user_id):
        await update.callback_query.message.reply_text(
            f"⏰ Пробный период закончился\n\nОформите подписку: ${SUBSCRIPTION_PRICE}/мес\n\nСсылка: {PAYMENT_LINK}"
        )
        return
    
    clients = db.get_psychologist_clients(user_id)
    
    if not clients:
        await update.callback_query.message.reply_text("👥 У вас пока нет клиентов.\n\nИспользуйте кнопку «Добавить клиента».")
        return
    
    keyboard = []
    for client in clients:
        keyboard.append([InlineKeyboardButton(f"{client['name']}", callback_data=f'client_{client["user_id"]}')])
    
    await update.callback_query.message.reply_text(
        "👥 Ваши клиенты\n\nНажмите на клиента для управления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def subscription_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in WHITELIST:
        await update.callback_query.message.reply_text(
            "👑 Партнёрский доступ\n\nВы имеете полный бесплатный доступ. Спасибо! 💚"
        )
        return
    
    user = db.get_user(user_id)
    if not user or user.get('role') != 'psychologist':
        await update.callback_query.message.reply_text("Эта функция только для психологов.")
        return
    
    is_active = db.check_subscription(user_id)
    trial_until = user.get('trial_until', '')
    
    if is_active:
        if trial_until:
            try:
                end_date = dt.fromisoformat(trial_until).strftime('%d.%m.%Y')
                await update.callback_query.message.reply_text(
                    f"✅ Пробный период активен\n\nДо {end_date} бесплатно.\n\nПосле — ${SUBSCRIPTION_PRICE}/мес.\nСсылка для оплаты: {PAYMENT_LINK}"
                )
            except:
                await update.callback_query.message.reply_text("✅ Подписка активна\n\nСпасибо! 💚")
        else:
            await update.callback_query.message.reply_text("✅ Подписка активна\n\nСпасибо! 💚")
    else:
        keyboard = [[InlineKeyboardButton("💳 Оплатить $20", url=PAYMENT_LINK)]]
        await update.callback_query.message.reply_text(
            f"⏰ Пробный период закончился\n\nОформите подписку: ${SUBSCRIPTION_PRICE}/мес\n\nПосле оплаты нажмите /confirm_payment",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.activate_payment(user_id)
    await update.message.reply_text(
        "✅ Подписка активирована!\n\nВсе функции снова доступны.\nИспользуйте /start."
    )

# ========== ЗАПУСК ==========

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm_payment", confirm_payment))
    
    app.add_handler(CallbackQueryHandler(register_psychologist, pattern='register_psychologist'))
    app.add_handler(CallbackQueryHandler(register_client, pattern='register_client'))
    app.add_handler(CallbackQueryHandler(select_psychologist, pattern='select_psy_'))
    app.add_handler(CallbackQueryHandler(add_client, pattern='add_client'))
    app.add_handler(CallbackQueryHandler(my_clients, pattern='my_clients'))
    app.add_handler(CallbackQueryHandler(subscription_info, pattern='subscription'))
    app.add_handler(CallbackQueryHandler(client_detail, pattern='client_'))
    app.add_handler(CallbackQueryHandler(send_task_to_client, pattern='task_'))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("🤖 ProPsy Bot запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()