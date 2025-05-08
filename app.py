from typing import Final
from telegram import Update, ChatPermissions, InputFile
from telegram.ext import Application, CommandHandler, ChatMemberHandler, MessageHandler, filters, ContextTypes, CallbackContext
from dotenv import load_dotenv
import os
import re
import logging


# Configure logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load environment variables from .env file
load_dotenv()


TOKEN: Final = os.getenv("BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

# A dictionary to store message counts for each chat
message_counter = {}

# Function to lock the chat for users
async def lock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restrict the group so that only admins can send messages."""
    user_id = update.effective_user.id
    admin_ids = await get_admin_ids(update, context)

    if user_id in admin_ids:
        try:
            await context.bot.set_chat_permissions(
                chat_id=update.effective_chat.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            await update.message.reply_text("🔒 Chat is now locked. Only admins can send messages.")
            await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
                                           "https://t.me/+6L4mwcO6UctmOGU1"
                                           "https://wa.me/+917055739671/?text=Bhai_Game_khelna_tha_aapke_pass")
        except Exception as e:
            logging.error(f"Error locking chat: {e}")
    else:
        await update.message.reply_text("❌ Only admins can lock the chat.")


# Function to unlock the chat for all users
async def unlock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow everyone in the group to send messages."""
    user_id = update.effective_user.id
    admin_ids = await get_admin_ids(update, context)

    if user_id in admin_ids:
        try:
            await context.bot.set_chat_permissions(
                chat_id=update.effective_chat.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await update.message.reply_text("🔓 Chat is now unlocked. Everyone can send messages.")
            await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
                                            "https://t.me/+6L4mwcO6UctmOGU1"
                                            "https://wa.me/+917055739671/?text=Bhai_Game_khelna_tha_aapke_pass")
            await update.message.reply_text("🎉 Group is now open! Start playing the game",
                disable_web_page_preview=True,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error unlocking chat: {e}")
    else:
        await update.message.reply_text("❌ Only admins can unlock the chat.")


# Function to get admin IDs for the group
async def get_admin_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return [admin.user.id for admin in chat_admins]  # Always return a list
    except Exception as e:
        print(f"Error fetching admin IDs: {e}")
        return []  # Return an empty list instead of False
    

# Dictionary to store user-provided number lists
allowed_numbers = {} 

# Dictionary to store claimed numbers per chat
game_data = {}

# Dictionary to track users who have already claimed a number
user_claims = {}

async def set_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Users provide a list of numbers, which will be the only numbers allowed for claiming."""
    chat_id = update.message.chat_id
    message = update.message.text

    # Normalize delimiters and extract numbers
    numbers = re.split(r"[ ,=\-\/]+", message)
    valid_numbers = [int(num) for num in numbers if num.isdigit() and 0 <= int(num) <= 99]

    if not valid_numbers:
        await update.message.reply_text("❌ Please provide valid numbers between 00 and 99.")
        return

    allowed_numbers[chat_id] = set(valid_numbers)
    game_data[chat_id] = {"numbers": {}}
    user_claims[chat_id] = {}
    
    await update.message.reply_text(f"✅ Numbers set for this game: {', '.join(map(str, sorted(valid_numbers)))}\n\nUsers, please claim your numbers using /claim <number>!")

async def claim_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to claim only one number from the provided list using /claim <number>."""
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user_name = update.message.from_user.first_name
    message = update.message.text

    if user_id in user_claims[chat_id]:
        await update.message.reply_text("❌ You have already claimed a number. You cannot claim more than one.")
        return

    parts = message.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ Usage: /claim <number>")
        return

    try:
        number = int(parts[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please enter a single number from the set list.")
        return

    if chat_id not in allowed_numbers:
        await update.message.reply_text("❌ No numbers have been set for this game. Please provide a number list first.")
        return

    if number not in allowed_numbers[chat_id]:
        await update.message.reply_text("❌ Invalid number. You can only claim from the set list.")
        return

    if number in game_data[chat_id]["numbers"] and user_id in [entry["id"] for entry in game_data[chat_id]["numbers"][number]]:
        await update.message.reply_text(f"⚠️ You have already claimed number {number}.")
        return

    if number not in game_data[chat_id]["numbers"]:
        game_data[chat_id]["numbers"][number] = []
    
    game_data[chat_id]["numbers"][number].append({"id": user_id, "name": user_name})
    user_claims[chat_id][user_id] = number
    await update.message.reply_text(f"✅ {user_name} successfully claimed number {number}.")

async def open_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin opens a number to check if any user has won. After opening, game resets."""
    chat_id = update.message.chat_id
    message = update.message.text

    if not game_data[chat_id]["numbers"]:
        await update.message.reply_text("⚠️ No numbers have been claimed yet. Use /claim <number> to participate.")
        return

    parts = message.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ Usage: /open <number>")
        return

    try:
        number_to_open = int(parts[1])
    except ValueError:
        await update.message.reply_text("❌ Please specify a valid number.")
        return

    if chat_id not in allowed_numbers:
        await update.message.reply_text("⚠️ No numbers have been set for this game. Use /setnumbers first.")
        return

    if number_to_open not in allowed_numbers[chat_id]:
        await update.message.reply_text(f"⚠️ Number {number_to_open} was never in the game.")
        return

    if number_to_open not in game_data[chat_id]["numbers"]:
        await update.message.reply_text(f"⚠️ No one has claimed number {number_to_open}. Better luck next time!")
        return

    claimed_users = game_data[chat_id]["numbers"][number_to_open]
    mentions = [f"[{entry['name']}](tg://user?id={entry['id']})" for entry in claimed_users]
    mention_text = ", ".join(mentions)

    await update.message.reply_text(
        f"🎉 **Number {number_to_open} is now open!**\n👤 Users who claimed it: {mention_text}\n\n🏆 **Winner: {mention_text}!** 🎉" if claimed_users else "⚠️ No one wins this time. Better luck next time! Please set numbrers again to play the game.",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

    # Reset the game
    allowed_numbers.pop(chat_id, None)
    game_data[chat_id] = {"numbers": {}}
    user_claims[chat_id] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Thanks for chatting with me. I respond to commands only.')

async def ok_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('AGR APNE PAYMENT KAR DI HAI, YA APKI PAYMENT PAHLE SE JAMA HAI TO APKI GAME OK HAI❤ \n \n 🆗 अपनी गेम का टोटल चेक📝 करके गेम पोस्ट करे टोटल गलत पर आपको सिर्फ ℝ𝔼𝔽𝕌ℕ𝔻 किया जाएगा 👍')

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('A.V.A.U online Khaiwal : \n \n RATE : 10 ke 950 ❤‍🔥 \n\n 👉🏻(TIME TABLE) \n\n DB : 03:00 LAST \n SG : 04:30 LAST \n FD : 05:50 LAST \n GB : 08:50 LAST \n  GL : 11:25 LAST \n DS : 04:00 LAST \n\n ❤‍🔥RULES❤‍🔥\n\n 01. टोटल ग़लत होने पर हाफ ( आदि ) पासिंग दी जाएगी आदि पासिंग तब मिलेगी जब आप बैलेंस ++ या आपकी पेमेंट पूरी होगी | अगर बैलेंस ++ नहीं हो तो सिर्फ़ रिफ़ंड होगा । \n\n 02. ⁠क्रासिंग में विद् जोड़ा विदाउट जोड़ा क्लियर लिखा होगा चाइए । नहीं तो सिर्फ़ रिफ़ंड होगा । \n\n 03. ⁠हरफ़ में अंदर बाहर (🆎) क्लियर लिखे । 🆎 ना लिखने पर हर्फ़ बाहर का माना जाएगा । \n\n 04. ⁠मैसेज डिलीट करने से पहले एडमिन को बता दे । और रिजल्ट के बाद मेसेज डिलीट करने पर बैलेंस 00 हो जाएगा । \n\n 05. ⁠एडिट मैसेज पर कोई पासिंग रिफ़ंड नहीं होगा |  \n\n 06. ⁠अगर ++ से गेम खेलते है तो अपना हिसाब बना कर डाले हिसाब ना बनाने कोई गेम वैलिड नहीं होगा । \n\n 07. ⁠फेल गेम का कोई रिफ़ंड नहीं होगा । \n\n 08. 5 ईंटों जोड़ी और 50 ईंटों हर्फ़ वैलिड होगा । इससे कम खेलने पर आदी पासिंग दी जाएगी । \n\n 09. एक मेसेज मे डबल जोड़ी 50 ईंटों से ज़्यादा होगी तो एक बार ही जोड़ी जायेगी । 1 फोल्डर के डबल जोड़ी की 50 इंटू तक ही पासिंग दी जाएगी । \n\n LIVE IN YOUR WORLD PLAY IN OURS \n           ( AVAU )     \n\n किसी भी समस्या के लिए कांटैक्ट करे । \n\n Telegram:- https://t.me/+6L4mwcO6UctmOGU1 \n\n Whatsapp:- https://wa.me/+917055739671/?text=Bhai_Game_khelna_tha_aapke_pass \n ') 


#  Commands

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send payment details along with QR code image."""
    qr_image_path = "QR.jpg"  # Ensure this file exists

    try:
        with open(qr_image_path, 'rb') as qr:
            await update.message.reply_photo(
                photo=InputFile(qr),
                caption=(
                    "सभी भुगतान संख्या पर \n\n"
                    "💰 *भाव 10 का 950*\n\n"
                    "*A\\.V\\.A\\.U online Khaiwal*\n\n"
                    "⚠️ *इसके आलावा आप अगर किसी और नंबर पर पेमेंट करते हैं तो उसकी जिम्मेदारी आपकी होगी\\.*\n\n"
                    "*🛡️ \\(ADMIN\\)*\n\n"
                    "🔹 [Telegram Group](https://t\\.me/+6L4mwcO6UctmOGU1)\n"
                    "🔹 [WhatsApp Contact](https://wa\\.me/+917055739671/?text=Bhai\\_Game\\_khelna\\_tha\\_aapke\\_pass)\n\n"
                    "**LIVE IN YOUR WORLD, PLAY IN OURS**\n\n"
                    "*\\(AVAU\\)*"
                ),
                parse_mode="MarkdownV2"
            )
    except Exception as e:
        logging.error(f"❌ Error sending payment QR: {e}")
        await update.message.reply_text("❌ Error sending payment QR. Please try again later.")


# Mapping abbreviations to full names
PREFIX_MAPPING = {
    "DS": "DESAWAR", 
    "DB": "DELHI BAZAR",
    "SG": "SHREE GANESH",
    "FD": "FARIDABAD",
    "GB": "GHAZIABAD",
    "GL": "GALI"
}

# Mapping numbers to emoji format
number_emojis = {
    "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
    "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"
}

async def convert_to_emoji(number_str):
    """Convert a string number to emoji format while preserving leading zeros."""
    return ''.join(number_emojis[digit] for digit in number_str)

async def live_command(update: Update, context: CallbackContext):
    """Handle the /live command and send formatted response."""

# ✅ Check if the user is an admin
    if not await get_admin_ids(update, context):
        await update.message.reply_text("❌ You are *not authorized* to use this command!", parse_mode="MarkdownV2")
        return

    message_text = update.message.text.strip()

    if message_text.startswith("/live "):
        message_text = message_text[6:]  
    elif message_text.startswith("live "):
        message_text = message_text[5:]
    else:
        return  # Ignore other messages

    args = message_text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Invalid format. Use: `live <prefix> <number>`", parse_mode="MarkdownV2")
        return

    prefix = args[0].upper()
    number_str = args[1]  # Keep as string to preserve leading zeros

    # Validate input (should only contain digits)
    if not number_str.isdigit():
        await update.message.reply_text("❌ The number must be a valid integer.", parse_mode="MarkdownV2")
        return

    full_name = PREFIX_MAPPING.get(prefix, prefix)
    emoji_number = await convert_to_emoji(number_str)  # Pass the string, not an int

    response_text = (
        "*●*━━━━━*༺⚜️༻*━━━━━*●*\n"
        "              🏆⚜️❂❂⚜️🏆\n"
        f"               *{full_name}*\n"
        "                     *𝗟𝗜𝗩𝗘*\n\n"
        f"                      {emoji_number}\n\n"
        "*●*━━━━━*༺⚜️༻*━━━━━ *●*\n\n"
        "📌 *Telegram link:*\n"
        "[Join Now](https://t\\.me/+6L4mwcO6UctmOGU1)\n\n"
        "📌 *WhatsApp Numbers:*\n"
        "[Click Here](https://wa\\.me/+917055739671/?text=Bhai\\_Game\\_khelna\\_tha\\_aapke\\_pass)"
    )

    await update.message.reply_text(response_text, parse_mode="MarkdownV2")


# Responses

def handle_response(text: str)-> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey i am here to help you!'
    
    if 'i need information of payment' in processed:
        return 'Sure What type of payment do you consider QR / UPI / Mob. no. !'
    
    if 'i want to do upi payment' in processed:
        return 'UPI:../.../.. and Mob: ..... !'
    
    return 'I do not understand what you wrote....'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text.lower().strip()

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Ensure the message has text
    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Invalid input. Please send a valid text message.")
        return

    message = update.message.text.strip()  # Safely access and strip the text
    message_type = update.message.chat.type

    # Initialize the counter for the chat if it doesn't exist
    if chat_id not in message_counter:
        message_counter[chat_id] = 0

    # Increment the message counter for the chat
    message_counter[chat_id] += 1

    if message_counter[chat_id] == 15:
        await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
                                        "https://t.me/+6L4mwcO6UctmOGU1 \n"
                                        "https://t.me/Payment_admin_AVAU")
        # message_counter[chat_id] += 1  # Increment to avoid repeated triggers

    # Check if 10 messages have been reached
    if message_counter[chat_id] >= 30:
        await update.message.reply_text(
            "➖➖➖➖➖➖➖➖➖➖➖➖➖ \n\n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n"
            "कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई "
            "किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल "
            "कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि "
            "वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U online Khaiwal \n ➖➖➖➖➖➖➖➖➖➖➖➖➖"
        )
        # Reset the counter to start counting again
        message_counter[chat_id] = 0
        return  # Exit after responding to avoid processing further logic
    
    """Handle messages where users type numbers directly."""
    # # Parse number lists
    delimiters = [",", "=", "-", "/", " "]
    for delimiter in delimiters:
        if delimiter in message:
            message = message.replace(delimiter, ",")

    # Handle number claiming
    if message.replace(",", " ").isdigit():
        # Extract numbers and validate
        numbers = [int(num.strip()) for num in message.split(",") if num.strip().isdigit()]

        valid_numbers = [num for num in numbers if 0 <= num <= 99]

        # Initialize game data for the chat if not present
        if chat_id not in game_data:
            game_data[chat_id] = {"numbers": {}, "opened": []}

        claimed = []
        already_claimed = []
        
        for number in valid_numbers:
            if number not in game_data[chat_id]["numbers"]:
                game_data[chat_id]["numbers"][number] = []

            if user_id not in [user["id"] for user in game_data[chat_id]["numbers"][number]]:
                game_data[chat_id]["numbers"][number].append({"id": user_id, "name": user_name})
                claimed.append(number)
            else:
                already_claimed.append(number)

        # Send response
        response_parts = []
        if claimed:
            response_parts.append(f"✅ {user_name} successfully claimed: {', '.join(map(str, claimed))}.")
        if already_claimed:
            response_parts.append(f"⚠️ You already claimed: {', '.join(map(str, already_claimed))}.")

        if response_parts:
            await update.message.reply_text("\n".join(response_parts))

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if update.message.chat.type in ['group', 'supergroup']:
        # Admin command detection
        if text in ["lock", "lock chat"]:
            if update.effective_user.id in await get_admin_ids(update, context):
                await lock_chat(update, context)
            else:
                await update.message.reply_text("❌ *Only admins can lock the chat.*", parse_mode="Markdown")
            return

        if text in ["unlock", "unlock chat"]:
            if update.effective_user.id in await get_admin_ids(update, context):
                await unlock_chat(update, context)
            else:
                await update.message.reply_text("❌ *Only admins can unlock the chat.*", parse_mode="Markdown")
            return
        
        if "live" in text:
            if update.effective_user.id in await get_admin_ids(update, context):
                await live_command(update, context)   # Call the live function
            else:
                await update.message.reply_text("❌ Only admins can live the number.")
            return    
        
        
        if re.search(r"\bok\b", text, re.IGNORECASE):  
            await ok_command(update, context)
            return

        if text == "rules":
            await rules_command(update, context)  # Respond to "rules"
            return
        
        if text == "rule":
            await rules_command(update, context)  # Respond to "rules"
            return

        if text == "pay":
            await payment_command(update, context)  # Respond to "pay"
            return

        if text == "payment":
            await payment_command(update, context)  # Respond to "pay"
            return

        if text == "upi":
            await payment_command(update, context)  # Respond to "pay"
            return

        if text == "qr":
            await payment_command(update, context)  # Respond to "pay"
            return

        if text == "lock":
            await lock_chat(update, context)
            return
        
        if text == "unlock":
            await unlock_chat(update, context)
            return
        
        if text == "open":
            await open_number(update, context)
            return

        if text == "live":
            await live_command(update, context)
            return    

        if BOT_USERNAME in text:
          new_text: str = text.replace(BOT_USERNAME, '').strip()
          response: str = handle_response(new_text)
        else:
          return  
    else:
        response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

# Keywords to detect in payment screenshots
PAYMENT_KEYWORDS = ["payment", "paid", "transaction", "receipt", "invoice", "amount", "successful"]    


async def send_photo(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    await context._user_id.send_photo(chat_id=chat_id, photo=open("image.jpg", "rb"))  


async def send_audio(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    await context._user_id.send_audio(chat_id=chat_id, audio=open("audio.mp3", "rb"))

async def receive_photo(update: Update, context: CallbackContext) -> None:
    photo = update.message.photo[-1]  # Get the highest resolution photo
    file = await context.bot.get_file(photo.file_id)  # Get file info
    file_path = "received_photo.jpg"
    
    # Download the photo
    await file.download_to_drive(file_path)


if __name__ == '__main__':
    print('starting bot...')
    app = Application.builder().token(TOKEN).read_timeout(30).write_timeout(30).build()


    # Commands
    app.add_handler(CommandHandler('start', start_command))            
    app.add_handler(CommandHandler('ok', ok_command))            
    app.add_handler(CommandHandler('rules', rules_command)) 
    app.add_handler(CommandHandler('rule', rules_command))            
    app.add_handler(CommandHandler('payment', payment_command))            
    app.add_handler(CommandHandler('pay', payment_command))            
    app.add_handler(CommandHandler('qr', payment_command))            
    app.add_handler(CommandHandler('upi', payment_command))
    app.add_handler(CommandHandler('lock', lock_chat))
    app.add_handler(CommandHandler('unlock', unlock_chat))
    app.add_handler(CommandHandler("live", live_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message, live_command))


    # Add handlers for getting and opening numbers
    app.add_handler(CommandHandler('get', handle_message))
    app.add_handler(CommandHandler('claim', claim_number))
    app.add_handler(CommandHandler('open', open_number))

    #updater check media files
    app.add_handler(CommandHandler("photo", send_photo))
    app.add_handler(CommandHandler("audio", send_audio))
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))


    #Errors  
    app.add_error_handler(error)

    # Enable logging to see errors in the console

    print(game_data)

    #Poll the bot
    print('Polling...')
    logging.info("Bot is running...")
    app.run_polling(poll_interval=3)
    # asyncio.run(app())
           

















# async def get_admin_ids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool: 
#     chat = update.effective_chat
#     user_id = update.message.from_user.id

#     try:
#         # Get list of admins in the group
#         chat_admins = await context.bot.get_chat_administrators(chat.id)
#         admin_ids = [admin.user.id for admin in chat_admins]
#         return user_id in admin_ids  # Check if the user is an admin
#     except Exception as e:
#         print(f"Error checking admin status: {e}")
#         return False


# async def lock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Restrict the group so that only admins can send messages."""
#     # Check if the user issuing the command is an admin
#     if update.effective_user.id in await get_admin_ids(update, context):
#         # Update chat permissions to restrict messages from non-admin users
#         await context.bot.set_chat_permissions(
#             chat_id=update.effective_chat.id,
#             permissions=ChatPermissions(
#                 can_send_messages=False,
#                 can_send_media_messages=False,
#                 can_send_other_messages=False,
#                 can_add_web_page_previews=False
#             )
#         )
#         await update.message.reply_text("🔒 Chat is now locked. Only admins can send messages.")
#         await update.message.reply_text("➖➖➖➖➖➖➖➖➖➖➖➖➖ \n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n\n कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n ➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U ONLINE GAME CLUB \n ➖➖➖➖➖➖➖➖➖➖➖➖➖")
#         await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
#                                            "https://t.me/+6L4mwcO6UctmOGU1"
#                                            "https://wa.me/+917055739671/?text=Bhai_Game_khelna_tha_aapke_pass")
#     else:
#         await update.message.reply_text("❌ Only admins can lock the chat.")


# async def unlock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Allow everyone in the group to send messages."""
#     # Check if the user issuing the command is an admin
#     if update.effective_user.id in await get_admin_ids(update, context):
#         # Update chat permissions to allow messages from all users
#         await context.bot.set_chat_permissions(
#             chat_id=update.effective_chat.id,
#             permissions=ChatPermissions(
#                 can_send_messages=True,
#                 can_send_media_messages=True,
#                 can_send_other_messages=True,
#                 can_add_web_page_previews=True
#             )
#         )
#         await update.message.reply_text("🔓 Chat is now unlocked. Everyone can send messages.")
#         await update.message.reply_text("➖➖➖➖➖➖➖➖➖➖➖➖➖ \n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n\n कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n ➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U ONLINE GAME CLUB \n ➖➖➖➖➖➖➖➖➖➖➖➖➖")
#         await update.message.reply_text(
#             "🎉 Group is now open! Register and start playing the game using this link: [Register to Play](https://example.com/register)",
#             disable_web_page_preview=True,
#             parse_mode="Markdown"
#         )
#         await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
#                                            "https://t.me/+6L4mwcO6UctmOGU1"
#                                            "https://wa.me/+917055739671/?text=Bhai_Game_khelna_tha_aapke_pass")
#     else:
#         await update.message.reply_text("❌ Only admins can unlock the chat.")


# if message.lower().startswith("open"):
        #     if user_id in await get_admin_ids(update, context):  # Ensure only admins can open numbers
        #         parts = message.split()
        #         if len(parts) < 2:
        #             await update.message.reply_text("❌ Please specify a valid number. Example: open 33")
        #             return

        #         try:
        #             number_to_open = int(parts[1])  # Extract number correctly
        #         except ValueError:
        #             await update.message.reply_text("❌ Please specify a valid number. Example: open 33")
        #             return
                

        #         if message.isdigit():  # User sends just a number
        #             number_claimed = int(message)

        #             # Ensure chat_id exists in game_data
        #             if chat_id not in game_data:
        #                 game_data[chat_id] = {"numbers": {}, "opened": []}

        #             # Ensure the number is not already claimed
        #             if number_claimed not in game_data[chat_id]["numbers"]:
        #                 game_data[chat_id]["numbers"][number_claimed] = [user_name]  # Store user who claimed it
        #                 await update.message.reply_text(f"✅ {user_name} successfully claimed: {number_claimed}")
        #             else:
        #                 await update.message.reply_text(f"⚠️ Number {number_claimed} is already claimed.")