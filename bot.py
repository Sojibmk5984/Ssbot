import os
import time
import pyotp
import requests
import gspread
import pandas as pd
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

# --- CONFIGURATION ---
BOT_TOKEN = '8786077862:AAH2HD71gSBJAjyOnlpRAeX_ejDOZzCHZN0'
ADMIN_ID = 7247510411
SHEET_ID = '1775hRkGSY6S3miNZygFuz0PO-LFilsKPZJb7yCZJJpo'
SUPPORT_WA = "https://wa.me/8801823315984"

# State Constants for Conversation
SET_NAME, WORK_FLOW, GET_UID, GET_2FA = range(4)

# Google Sheets Auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = {
    "type": "service_account",
    "project_id": "fbv1-495318",
    "private_key_id": "2672f42dfff86977ca5bd643371401d3f6e68cba",
    "private_key": os.getenv("PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJgEzu302Khecm\nXoAH8lf+oUixfKnxoYcGoeh4SuZOA9DsjwKW1nW8OcvkV9FMy3kJnbTywCpHP6bH\n4sh6MbLONUv+uoyx7Stwm9szIY2CZgDUPPhAfVMq0IMktOWODRbSNjg8s8+V59Pb\nh2BslTyoVX2I091fP8ZPGILd39U3HgEWfcj34H/5jkR1/3uqY63w6GkAQXJBCwkW\ntkJN4Cw5hlrFyU7F4iJ+Ml4FrrcXC0T8okGmZhpoGczhnUaC+GOPblcJ34EXHTO9\nthHzkIjAIhbjP2TQRYJ0sPQA9h4bZJCERXEG1t7piEgUYHvbGIr3B2adkwuppaGx\nrs3EVgu/AgMBAAECggEAXBZ9kmGNL3R4qilf+8G+g0k0TqD5jctTSS2vb2JTlG3c\nCnBlL4g9cFM9olKb/auz2jgv3Q0DhWJKl2lGU8novKLQ405gRGRuiN1BtUFtSZ3S\nXSysC9T6sENw29KsYloLBvDujJdklE7JnLdm0tj1Sr0fTOv+bKxZtgYusLW93JzS\ni9+eCAmWE4039v1PV0Ij6YTJCldkigQcxdSBw+BdlO+D3uiJNAA3VpsyoDs1aoUp\nh5It8B3BHot+SNE1sbInks8hekk4A2qCmZtFxkp5c62aRgTg2eiBOimG+gpXUYKP\njiWvGLTqCH8jAFVEl3S9wZeltH0qIfn1KfNH8e0hGQKBgQD1bzGDSZXk4gGPeNXv\nyf1DGfuqMQT7V1wun9aZ7bp+ZWQZrMgWbBnkeMkePRmx9JivVDsApmk8a4woDEwS\n4VxzfailyRN5DX/5OMYjrzJo4RlpINGdE6NZhM1Ey3J77X6RhLihwTKVN0kB0D9F\nUWJzzMcQa2Uq8SogHuDP65GHowKBgQDSLPEoqmw621k445PwtnIiXIWGAMxZxYfs\nGRCRnGD8Gik0c94ZLJSdHH4nYskGWcCPpr9l1hVAJB89bOqUGMs8dyd6wrOMpLV6\nJPPD5K/oPn+Hfxm6LJMFgLmy7BlI9sLH2oVn1oBOVX2QGikEcdGaN8UKGSmSvhJU\nm1+wjUKdNQKBgEXetsi6TRrQoEMY0kamSRwuLG/h7poi35JCXJSLkdjjwmBwyLFh\naumY3SBnooX/rOvU3csslK7nqwnHnmyNjYUvU7CGkq2Wg0UOvZFxEbe7xUEhX6sI\n6SrV3J3mERxomuyQTQN3fY/vIjCK+UghiBaRSGZLPIzCBQ0J3VQzqsVjAoGAB5wy\n+zr4gkUQ/PtYjv28MjxRZWHABHwfiM/7hpo39Mjptwl/AEBZ/Tpb4wczqjQzwb/S\n7FgNGu5z5yB7efNP4Jeb6VkFcVFBdPPDk9NC/1DMA1b50oDsreVUVAMygy7ULLJf\n5DujF7MGweIAnDWW1lOwocX5eGPDfCbIFzd2MwUCgYEA5RxxI+Mopo/fnxG8zEmj\CkZm+kR9hjqqjNrAzLrMHbfEAcjlyp4HMPYEjp9eOnNpWeLSDDKQxFgty8/FNpIt\nqWVsXgBGdFnW+6mkZyJBWCjmSRbgHIuU7vWMZwxsBEs4eiWRDoEuAn7uq5EpSJDy\nmI1oLVomIY8E2Lw6axaVEq0=\n-----END PRIVATE KEY-----\n"),
    "client_email": "fbv1-96@fbv1-495318.iam.gserviceaccount.com"
}
client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope))
ss = client.open_by_key(SHEET_ID)
inv_sh = ss.worksheet("Inventory")
rep_sh = ss.worksheet("Worker_Reports")
die_sh = ss.worksheet("DIE MAIL")

# In-Memory Tracking
users_db = {} 
active_sessions = {}

# --- LOGIC FUNCTIONS ---

def verify_uid(uid):
    try:
        r = requests.get(f"https://graph.facebook.com/{uid}/picture?type=normal")
        return r.status_code == 200
    except: return False

def handle_die_mail(mail_row, is_fresh=False):
    mail = mail_row['MAIL']
    die_sh.append_row([mail, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    if is_fresh:
        # Green marking logic here if needed
        pass

# --- BOT HANDLERS ---

def start(update: Update, context):
    uid = update.effective_user.id
    if uid not in users_db:
        update.message.reply_text("💎 **WELCOME!**\nকাজ শুরু করতে আপনার আসল নামটি লিখুন:")
        return SET_NAME
    return main_menu(update, context)

def main_menu(update, context):
    uid = update.effective_user.id
    kb = [[InlineKeyboardButton("🚀 Start Work", callback_data='warning_page')]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ Admin Mode", callback_data='admin_panel')])
    kb.append([InlineKeyboardButton("📞 Support", url=SUPPORT_WA)])
    
    msg = "🏠 **Main Menu**\nআপনার পছন্দের অপশনটি বেছে নিন।"
    if update.callback_query:
        update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def warning_page(update, context):
    query = update.callback_query
    uid = update.effective_user.id
    
    if users_db.get(uid, {}).get('frozen_until') and datetime.now() < users_db[uid]['frozen_until']:
        query.answer("🚫 আপনি বর্তমানে ফ্রিজ আছেন!", show_alert=True)
        return

    text = (
        "⚠️ **সতর্কবার্তা ও নিয়মাবলী**\n\n"
        "১. প্রতিটি কাজের জন্য ৩০ মিনিট সময় পাবেন।\n"
        "২. ৩ বার ক্যানসেল করলে ৩০ মিনিট ব্লক।\n"
        "৩. ভুল ডাটা দিলে চিরতরে ব্যান হবেন।"
    )
    kb = [[InlineKeyboardButton("✅ I Agree & Start", callback_data='get_task')]]
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def get_task(update, context):
    query = update.callback_query
    uid = update.effective_user.id
    
    last_done = users_db.get(uid, {}).get('last_done')
    if last_done and datetime.now() < last_done + timedelta(minutes=5):
        query.answer("⏳ ৫ মিনিট অপেক্ষা করুন!", show_alert=True)
        return

    rows = inv_sh.get_all_records()
    for i, r in enumerate(rows):
        if r.get('STATUS') != 'Done':
            active_sessions[uid] = {'row': i+2, 'start': datetime.now(), 'data': r}
            msg = f"📧 Mail: `{r['MAIL']}`\n🔑 Pass: `{r['PASSWORD']}`\n\n⏱ সময় শুরু: ৩০ মিনিট"
            kb = [
                [InlineKeyboardButton("🔄 Refresh OTP", callback_data='refresh_otp')],
                [InlineKeyboardButton("❌ Cancelled Work", callback_data='cancel_task')]
            ]
            query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            return

# --- ADMIN PANEL ---

def admin_panel(update: Update, context):
    kb = [
        [
            InlineKeyboardButton("🚫 BLOCK LIST", callback_data='block_list'), 
            InlineKeyboardButton("❄️ Freeze Workers", callback_data='freeze_list')
        ],
        [InlineKeyboardButton("📋 User Details", callback_data='user_details')],
        [InlineKeyboardButton("🏠 Home", callback_data='go_home')]
    ]
    update.callback_query.edit_message_text("💎 **ADMIN CONTROL PANEL**", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SET_NAME: [MessageHandler(Filters.text & ~Filters.command, lambda u, c: main_menu(u, c))],
            WORK_FLOW: [CallbackQueryHandler(warning_page, pattern='warning_page')],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(get_task, pattern='get_task'))
    dp.add_handler(CallbackQueryHandler(admin_panel, pattern='admin_panel'))
    dp.add_handler(CallbackQueryHandler(main_menu, pattern='go_home'))
    
    print("Elite AI Engine is Live...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
