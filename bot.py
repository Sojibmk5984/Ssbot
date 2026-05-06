import os
import re
import msal
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- কনফিগারেশন ---
# গিটহাব সিক্রেট বা এনভায়রনমেন্ট ভেরিয়েবল থেকে টোকেন নেবে
BOT_TOKEN = os.getenv('8694471819:AAE8yRgfdOO2PHTpTrGD7vQmBVjU_PPG_B4') 

async def get_otp_logic(email, refresh_token, client_id):
    """OAuth2 Refresh Token ব্যবহার করে OTP সংগ্রহের মূল লজিক"""
    authority = "https://login.microsoftonline.com/common"
    # ওটিপি পড়ার জন্য নির্দিষ্ট স্কোপ
    scopes = ["https://graph.microsoft.com/IMAP.AccessAsUser.All", "offline_access"]

    # মাইক্রোসফট অ্যাপ অবজেক্ট তৈরি
    app = msal.PublicClientApplication(client_id, authority=authority)
    
    # রিফ্রেশ টোকেন দিয়ে নতুন এক্সেস টোকেন নেওয়া
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=scopes)

    if "access_token" in result:
        access_token = result['access_token']
        # Graph API দিয়ে ইনবক্সের লেটেস্ট মেসেজ দেখা
        endpoint = "https://graph.microsoft.com/v1.0/me/messages?$top=1&$select=subject,bodyPreview"
        headers = {'Authorization': 'Bearer ' + access_token}
        
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            messages = response.json().get('value', [])
            if messages:
                body = messages[0].get('bodyPreview', '')
                subject = messages[0].get('subject', '')
                # বডি থেকে ৪-৬ ডিজিটের ওটিপি খুঁজে বের করা (Regex)
                otp_match = re.findall(r'\b\d{4,6}\b', body)
                otp = otp_match[0] if otp_match else "ওটিপি পাওয়া যায়নি"
                
                return f"✅ **মেইল পাওয়া গেছে!**\n📌 **বিষয়:** {subject}\n🔑 **ওটিপি:** `{otp}`"
            return "❌ ইনবক্সে কোনো নতুন মেসেজ নেই।"
        return f"❌ মাইক্রোসফট এরর: {response.status_code}"
    
    return f"❌ লগইন বা টোকেন এরর: {result.get('error_description', 'Unknown error')}"

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম! ওটিপি পেতে আপনার ডাটা নিচের ফরম্যাটে দিন:\n\n"
        "`email|password|refresh_token|client_id`"
    )

# মেসেজ হ্যান্ডলার (যেখানে মেইল ডাটা প্রসেস হবে)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # চেক করা হচ্ছে ইনপুট ফরম্যাট ঠিক আছে কিনা
    if '|' not in text:
        return

    try:
        parts = text.split('|')
        if len(parts) < 4:
            await update.message.reply_text("⚠️ ভুল ফরম্যাট! দয়া করে এভাবে দিন: email|password|refresh_token|client_id")
            return
        
        email = parts[0].strip()
        refresh_token = parts[2].strip()
        client_id = parts[3].strip()

        await update.message.reply_text("🔍 ওটিপি খোঁজা হচ্ছে... একটু অপেক্ষা করুন।")
        
        # ওটিপি ফেচ করার ফাংশন কল
        result = await get_otp_logic(email, refresh_token, client_id)
        await update.message.reply_text(result, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ একটি সমস্যা হয়েছে: {str(e)}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN পাওয়া যায়নি! এনভায়রনমেন্ট চেক করুন।")
    else:
        # বট চালু করা
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("বটটি এখন লাইভ এবং কাজ করছে...")
        app.run_polling()
