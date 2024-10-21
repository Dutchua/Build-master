import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging

load_dotenv()

TOKEN = os.getenv('TELEGRAMTOKEN')
FILE_PATH = 'build_masters.txt'

last_pinned_message_id = None  # Initialized globally

def read_build_masters_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.read().splitlines()
            build_masters = lines[:-2]
            current_build_master_index = int(lines[-2])
            last_pinned_message_id = lines[-1] if lines[-1] != 'None' else None
        return build_masters, current_build_master_index, last_pinned_message_id
    except FileNotFoundError:
        return ["Josh", "Brent", "Justin"], 0, None

def write_build_masters_to_file(file_path, build_masters, current_build_master_index, last_pinned_message_id):
    with open(file_path, 'w') as file:
        for build_master in build_masters:
            file.write(f"{build_master}\n")
        file.write(f"{current_build_master_index}\n")
        file.write(str(last_pinned_message_id) + '\n')

def get_next_build_master(build_masters, current_build_master_index):
    current_build_master_index = (current_build_master_index + 1) % len(build_masters)
    return build_masters[current_build_master_index], current_build_master_index

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! Bot is active.")

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    build_masters, current_build_master_index, _ = read_build_masters_from_file(FILE_PATH)
    next_build_master, updated_index = get_next_build_master(build_masters, current_build_master_index)
    write_build_masters_to_file(FILE_PATH, build_masters, updated_index, None)

    keyboard = [
        [InlineKeyboardButton("Yes, I'm ready", callback_data='ready')],
        [InlineKeyboardButton("No, I'm not ready", callback_data='not_ready')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(f"{next_build_master}, you're next in the build master rotation. Are you ready to build master?", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/next - Get the next build master in the rotation\n"
        "/stop - Stop the bot"
    )
    await update.message.reply_text(help_text)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.application.stop()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.first_name
    build_masters, current_build_master_index, last_pinned_message_id = read_build_masters_from_file(FILE_PATH)
    next_build_master = build_masters[current_build_master_index]

    if query.data == 'ready':
        if user == next_build_master:
            await query.edit_message_text(text=f"{user} has confirmed and is now the master of builds!")

            if last_pinned_message_id is not None:
                await context.bot.unpin_chat_message(chat_id=query.message.chat.id, message_id=last_pinned_message_id)

            last_pinned_message_id = query.message.message_id
            await context.bot.pin_chat_message(chat_id=query.message.chat.id, message_id=last_pinned_message_id)

            write_build_masters_to_file(FILE_PATH, build_masters, current_build_master_index, last_pinned_message_id)
        else:
            await query.answer("You're not the next build master!", show_alert=True)
    elif query.data == 'not_ready':
        await query.edit_message_text(text=f"{user} is not ready to master the build. Next person will be notified.")
    else:
        await query.answer("Unknown action!", show_alert=True)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update: {update} \nError: {context.error}")

if __name__ == '__main__':
    print("Bot has started")

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('next', next_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('stop', stop_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(error)

    print("Polling...")  
    app.run_polling(poll_interval=3)
