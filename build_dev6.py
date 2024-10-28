import os
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
scheduler = AsyncIOScheduler()

TOKEN = os.getenv('TELEGRAM_TOKEN')
FILE_PATH = 'build_dev6_list.txt'
TIMEZONE = 'Africa/Johannesburg'
CHAT_ID = os.getenv('DEV6_CHAT_ID')

last_pinned_message_id = None

def read_build_masters_from_file():
    try:
        with open(FILE_PATH, 'r') as file:
            lines = file.read().splitlines()
            build_masters = lines[:-2]
            current_build_master_index = int(lines[-2])
            last_pinned_message_id = lines[-1] if lines[-1] != 'None' else None
        return build_masters, current_build_master_index, last_pinned_message_id
    except FileNotFoundError:
        return ["Josh", "Brent", "Justin"], 0, None

def write_build_masters_to_file(build_masters, current_build_master_index, last_pinned_message_id):
    with open(FILE_PATH, 'w') as file:
        for build_master in build_masters:
            file.write(f"{build_master}\n")
        file.write(f"{current_build_master_index}\n")
        file.write(str(last_pinned_message_id) + '\n')

def get_next_build_master(build_masters, current_build_master_index):
    current_build_master_index = (current_build_master_index + 1) % len(build_masters)
    return build_masters[current_build_master_index], current_build_master_index

async def send_weekly_message(context: ContextTypes.DEFAULT_TYPE):
    build_masters, current_build_master_index, last_pinned_message_id = read_build_masters_from_file()
    next_build_master, updated_index = get_next_build_master(build_masters, current_build_master_index)

    write_build_masters_to_file(build_masters, updated_index, last_pinned_message_id)

    keyboard = [
        [InlineKeyboardButton("Yes, I'm ready", callback_data='ready')],
        [InlineKeyboardButton("No, I'm not ready", callback_data='not_ready')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"{next_build_master}, you're next in the build master rotation. Are you ready to master builds?",
        reply_markup=reply_markup
    )

def schedule_weekly_message(application):
    scheduler.add_job(send_weekly_message, 'cron', day_of_week='mon', hour=8, minute=0, args=[application])
    scheduler.start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! Bot is active.")

async def coolest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    build_masters, current_build_master_index, pin= read_build_masters_from_file()
    current_build_master = build_masters[current_build_master_index]
    await update.message.reply_text(f'The current master builder is: {current_build_master}')

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"The chat ID is: {chat_id}")

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_weekly_message(context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/next - Get the next build master in the rotation\n"
        "/who_is_the_coolest - Find out who the build master is this week (beta)\n"
        "/help - Show this help message\n"
        "/stop - Stop the bot"
    )
    await update.message.reply_text(help_text)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.application.stop()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.first_name
    build_masters, current_build_master_index, last_pinned_message_id = read_build_masters_from_file()
    next_build_master = build_masters[current_build_master_index]

    if user == next_build_master:
        if query.data == 'ready':
            await query.edit_message_text(text=f"{user} has confirmed and is now the master of builds!")

            if last_pinned_message_id is not None:
                await context.bot.unpin_chat_message(chat_id=query.message.chat.id, message_id=last_pinned_message_id)

            last_pinned_message_id = query.message.message_id
            await context.bot.pin_chat_message(chat_id=query.message.chat.id, message_id=last_pinned_message_id)

            write_build_masters_to_file(build_masters, current_build_master_index, last_pinned_message_id)

        elif query.data == 'not_ready':
            await query.edit_message_text(text=f"{user} is not ready to master the build. Next person will be notified.")
            await next_command(update, context)
        else:
            await query.answer("Unknown action!", show_alert=True)
    else:
        await query.answer("You're not the next build master!", show_alert=True)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update: {update} \nError: {context.error}")

if __name__ == '__main__':

    app = ApplicationBuilder().token(TOKEN).build()
    
    schedule_weekly_message(app)
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('next', next_command))
    app.add_handler(CommandHandler('get_chat_id', get_chat_id))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('stop', stop_command))
    app.add_handler(CommandHandler('who_is_the_coolest', coolest_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(error)

    app.run_polling(poll_interval=3)
