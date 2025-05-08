from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
)
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Responses for commands
RESPONSES = {
    "ok": "AGR APNE PAYMENT KAR DI HAI, YA APKI PAYMENT PAHLE SE JAMA HAI TO APKI GAME OK HAI❤\n\n"
          "🆗 अपनी गेम का टोटल चेक📝 करके गेम पोस्ट करे टोटल गलत पर आपको सिर्फ ℝ𝔼𝔽𝕌ℕ𝔻 किया जाएगा 👍",
    "payment": "सभी भुगतान संख्या पर\n\n"
               "पेटीएम : 🔜 8126881875\n"
               "फ़ोन पे : 🔜 8126881875\n"
               "गूगल पे : 🔜 8126881875\n\n"
               "भाव 10 का 950\n\n"
               "A.V.A.U online game club\n\n"
               "इसके आलावा आप अगर किसी और नंबर पर पेमेंट करते हैं तो उसकी जिम्मेदारी आपकी होगी\n\n"
               "(ADMIN)\n\n"
               "https://t.me/AVAU_ONLINE_GAME_CLUB\n"
               "https://t.me/Payment_admin_AVAU",
    "rules": "RATE : 10 ke 950 ❤‍🔥\n\n"
             "👉🏻(TIME TABLE)\n"
             "DB : 03:00 LAST\n"
             "SG : 04:30 LAST\n"
             "FD : 05:50 LAST\n"
             "GB : 08:50 LAST\n"
             "GL : 11:25 LAST\n"
             "DS : 04:00 LAST\n\n"
             "PAYMENT NO. 💰\n"
             "*paytm\n"
             "*8126881875\n"
             "*PhonePe\n"
             "*8126881875\n"
             "*Google Pay\n"
             "*8126881875\n\n"
             "❤‍🔥RULES❤‍🔥\n"
             "01. टोटल ग़लत होने पर हाफ ( आदि ) पासिंग दी जाएगी ... (TRUNCATED FOR BREVITY)",
    'lock' : "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "‼‼‼‼‼‼‼‼‼‼‼‼‼कृपया ध्यान दें ... (LOCK MESSAGE CONTENT)",
    "unlock": "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
              "‼‼‼‼‼‼‼‼‼‼‼‼‼कृपया ध्यान दें ... (UNLOCK MESSAGE CONTENT)",
}

# Command handlers
async def command_handler(update: Update, context: CallbackContext):
    command = update.message.text.lower()
    if command in RESPONSES:
        await update.message.reply_text(RESPONSES[command])

# Timer-based response
message_count = {}

async def set_timer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message_count[chat_id] = 0
    await update.message.reply_text("Timer set! Responding after 10 messages.")

async def count_messages(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id in message_count:
        message_count[chat_id] += 1
        if message_count[chat_id] == 10:
            message_count.pop(chat_id)  # Reset the count
            await update.message.reply_text(
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                "‼‼‼‼‼‼‼‼‼‼‼‼‼कृपया ध्यान दें हम किसी से किसी के ... (TIMER RESPONSE)"
            )

# Main function to set up the bot
def main():
    app = ApplicationBuilder().token("7722538157:AAE4z-CEsS8nsuhwiU7zviphIRLb5QQ5KH4").build()

    # Register commands
    app.add_handler(CommandHandler("ok", command_handler))
    app.add_handler(CommandHandler("payment", command_handler))
    app.add_handler(CommandHandler("rules", command_handler))
    app.add_handler(CommandHandler("lock", command_handler))
    app.add_handler(CommandHandler("unlock", command_handler))

    # Register set timer command and message counting
    app.add_handler(CommandHandler("set_timer", set_timer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
