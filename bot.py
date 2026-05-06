import os
import time
import pyotp
import requests
import gspread
import pandas as pd
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryContext, CallbackQueryHandler
from msal import ConfidentialClientApplication

# --- কনফিগারেশন ---
BOT_TOKEN = '8786077862:AAH2HD71gSBJAjyOnlpRAeX_ejDOZzCHZN0'
ADMIN_ID = 7247510411
SHEET_ID = '1775hRkGSY6S3miNZygFuz0PO-LFilsKPZJb7yCZJJpo'
SUPPORT_WA = "https://wa.me/8801823315984"

# গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = {
    "type": "service_account",
    "project_id": "fbv1-495318",
    "private_key_id": "2672f42dfff86977ca5bd643371401d3f6e68cba",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJgEzu302Khecm\nXoAH8lf+oUixfKnxoYcGoeh4SuZOA9DsjwKW1nW8OcvkV9FMy3kJnbTywCpHP6bH\n4sh6MbLONUv+uoyx7Stwm9szIY2CZgDUPPhAfVMq0IMktOWODRbSNjg8s8+V59Pb\nh2BslTyoVX2I091fP8ZPGILd39U3HgEWfcj34H/5jkR1/3uqY63w6GkAQXJBCwkW\ntkJN4Cw5hlrFyU7F4iJ+Ml4FrrcXC0T8okGmZhpoGczhnUaC+GOPblcJ34EXHTO9\nthHzkIjAIhbjP2TQRYJ0sPQA9h4bZJCERXEG1t7piEgUYHvbGIr3B2adkwuppaGx\nrs3EVgu/AgMBAAECggEAXBZ9kmGNL3R4qilf+8G+g0k0TqD5jctTSS2vb2JTlG3c\nCnBlL4g9cFM9olKb/auz2jgv3Q0DhWJKl2lGU8novKLQ405gRGRuiN1BtUFtSZ3S\nXSysC9T6sENw29KsYloLBvDujJdklE7JnLdm0tj1Sr0fTOv+bKxZtgYusLW93JzS\ni9+eCAmWE4039v1PV0Ij6YTJCldkigQcxdSBw+BdlO+D3uiJNAA3VpsyoDs1aoUp\nh5It8B3BHot+SNE1sbInks8hekk4A2qCmZtFxkp5c62aRgTg2eiBOimG+gpXUYKP\njiWvGLTqCH8jAFVEl3S9wZeltH0qIfn1KfNH8e0hGQKBgQD1bzGDSZXk4gGPeNXv\nyf1DGfuqMQT7V1wun9aZ7bp+ZWQZrMgWbBnkeMkePRmx9JivVDsApmk8a4woDEwS\n4VxzfailyRN5DX/5OMYjrzJo4RlpINGdE6NZhM1Ey3J77X6RhLihwTKVN0kB0D9F\nUWJzzMcQa2Uq8SogHuDP65GHowKBgQDSLPEoqmw621k445PwtnIiXIWGAMxZxYfs\nGRCRnGD8Gik0c94ZLJSdHH4nYskGWcCPpr9l1hVAJB89bOqUGMs8dyd6wrOMpLV6\nJPPD5K/oPn+Hfxm6LJMFgLmy7BlI9sLH2oVn1oBOVX2QGikEcdGaN8UKGSmSvhJU\nm1+wjUKdNQKBgEXetsi6TRrQoEMY0kamSRwuLG/h7poi35JCXJSLkdjjwmBwyLFh\naumY3SBnooX/rOvU3csslK7nqwnHnmyNjYUvU7CGkq2Wg0UOvZFxEbe7xUEhX6sI\n6SrV3J3mERxomuyQTQN3fY/vIjCK+UghiBaRSGZLPIzCBQ0J3VQzqsVjAoGAB5wy\n+zr4gkUQ/PtYjv28MjxRZWHABHwfiM/7hpo39Mjptwl/AEBZ/Tpb4wczqjQzwb/S\n7FgNGu5z5yB7efNP4Jeb6VkFcVFBdPPDk9NC/1DMA1b50oDsreVUVAMygy7ULLJf\n5DujF7MGweIAnDWW1lOwocX5eGPDfCbIFzd2MwUCgYEA5RxxI+Mopo/fnxG8zEmj\nCkZm+kR9hjqqjNrAzLrMHbfEAcjlyp4HMPYEjp9eOnNpWeLSDDKQxFgty8/FNpIt\nqWVsXgBGdFnW+6mkZyJBWCjmSRbgHIuU7vWMZwxsBEs4eiWRDoEuAn7uq5EpSJDy\nmI1oLVomIY8E2Lw6axaVEq0=\n-----END PRIVATE KEY-----\n",
    "client_email": "fbv1-96@fbv1-495318.iam.gserviceaccount.com"
}
client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope))
ss = client.open_by_key(SHEET_ID)
inv_sh = ss.worksheet("Inventory")
rep_sh = ss.worksheet("Worker_Reports")
die_sh = ss.worksheet("DIE MAIL")

# ইন-মেমোরি ডাটাবেজ
users = {} # {id: {name, status, penalty_count, last_work_time, banned}}
active_jobs = {} # {id: {row_index, start_time, mail_data}}

# --- ইউটিলিটি ফাংশনস ---

def get_otp(client_id, client_secret, refresh_token):
    # MSAL ওটিপি রিডার লজিক এখানে বসবে
    return "123456" # ডামি

def save_to_die(mail, date, status="Normal"):
    die_sh.append_row([mail, date])
    if status == "Fresh":
        # এখানে কোডিং এর মাধ্যমে সেল কালার সবুজ করা যাবে
        pass

# --- বটের প্রধান লজিক ---

def start(update: Update, context: CallbackQueryContext):
    uid = update.effective_user.id
    if uid not in users:
        update.message.reply_text("💎 **WELCOME**\nআপনার আসল নামটি লিখুন কাজ শুরু করার জন্য:")
        return "WAITING_NAME"
    
    show_main_menu(update)

def show_main_menu(update):
    uid = update.effective_user.id
    is_admin = (uid == ADMIN_ID)
    
    keyboard = [[InlineKeyboardButton("🚀 Start Work", callback_data='work')]]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Mode", callback_data='admin_panel')])
    
    keyboard.append([InlineKeyboardButton("📞 Support", url=SUPPORT_WA)])
    
    update.effective_message.reply_text("🏠 মেইন মেনু:", reply_markup=InlineKeyboardMarkup(keyboard))

def work_logic(update: Update, context: CallbackQueryContext):
    query = update.callback_query
    uid = update.effective_user.id
    
    # পেনাল্টি ও টাইম চেক
    if users[uid].get('banned'):
        query.answer("❌ আপনি ব্যান আছেন!", show_alert=True)
        return

    # ৫ মিনিটের গ্যাপ লজিক
    last_time = users[uid].get('last_work_time')
    if last_time and datetime.now() < last_time + timedelta(minutes=5):
        query.answer("⏳ ৫ মিনিট পর আবার কাজ পাবেন।", show_alert=True)
        return

    # ইনভেন্টরি থেকে ডাটা
    data = inv_sh.get_all_records()
    for i, row in enumerate(data):
        if row['STATUS'] == 'Pending':
            active_jobs[uid] = {'row': i+2, 'start_time': datetime.now(), 'data': row}
            
            msg = f"📧 Mail: `{row['MAIL']}`\n🔑 Pass: `{row['PASSWORD']}`\n\n⏱ সময়: ৩০ মিনিট।"
            kb = [
                [InlineKeyboardButton("✅ DONE Work", callback_data='done_work')],
                [InlineKeyboardButton("❌ Cancelled Work", callback_data='cancel_work')],
                [InlineKeyboardButton("🔄 Refresh OTP", callback_data='refresh_otp')]
            ]
            query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
            return

def done_work(update: Update, context: CallbackQueryContext):
    query = update.callback_query
    uid = update.effective_user.id
    job = active_jobs.get(uid)
    
    if not job: return
    
    # ৩০ মিনিট চেক
    if datetime.now() > job['start_time'] + timedelta(minutes=30):
        query.edit_message_text("⏰ সময় শেষ! নতুন করে শুরু করুন।")
        del active_jobs[uid]
        return

    # এখানে UID ইনপুট ও ২-ফ্যাক্টর প্রসেস শুরু হবে...
    query.message.reply_text("ইউআইডি দিন:")
    # সফল হলে রিপোর্ড শিটে সেভ

def cancel_work(update: Update, context: CallbackQueryContext):
    query = update.callback_query
    uid = update.effective_user.id
    users[uid]['penalty'] = users[uid].get('penalty', 0) + 1
    
    if users[uid]['penalty'] >= 3:
        users[uid]['banned_until'] = datetime.now() + timedelta(minutes=30)
        context.bot.send_message(ADMIN_ID, f"⚠️ নালিশ: ইউজার {uid} বারবার কাজ বাতিল করছে!")
        query.edit_message_text("🚫 আপনি ৩০ মিনিটের জন্য ব্লক।")
    else:
        query.edit_message_text("❌ কাজ বাতিল। নতুন কাজ নিন।")
    
    del active_jobs[uid]

# --- অ্যাডমিন প্যানেল ---

def admin_panel(update: Update, context: CallbackQueryContext):
    kb = [
        [InlineKeyboardButton("📋 User Details", callback_data='user_list')],
        [InlineKeyboardButton("📜 User History (TXT)", callback_data='user_history')],
        [InlineKeyboardButton("🚫 Ban User List", callback_data='ban_list')],
        [InlineKeyboardButton("🏠 Home", callback_data='go_home')]
    ]
    update.callback_query.edit_message_text("⚙️ অ্যাডমিন কন্ট্রোল:", reply_markup=InlineKeyboardMarkup(kb))

# --- মেইন ফাংশন ---

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(work_logic, pattern='work'))
    dp.add_handler(CallbackQueryHandler(done_work, pattern='done_work'))
    dp.add_handler(CallbackQueryHandler(cancel_work, pattern='cancel_work'))
    dp.add_handler(CallbackQueryHandler(admin_panel, pattern='admin_panel'))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
