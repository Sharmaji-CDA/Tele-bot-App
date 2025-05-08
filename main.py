from typing import Final
from PIL import Image
from telegram import Update, ChatPermissions
from telegram.ext import Updater, Application, CommandHandler, ChatMemberHandler, MessageHandler, filters, ContextTypes, CallbackContext
from dotenv import load_dotenv
import os
import re
import pytesseract

# Load environment variables from .env file
load_dotenv()

# Set Tesseract OCR path (update this according to your system)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Users\asus\AppData\Roaming\Python\Python313\Scripts\pytesseract.exe"


TOKEN: Final = os.getenv("BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

# A dictionary to store message counts for each chat
message_counter = {}

# Function to lock the chat for users
async def lock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restrict the group so that only admins can send messages."""
    # Check if the user issuing the command is an admin
    if update.effective_user.id in await get_admin_ids(update, context):
        # Update chat permissions to restrict messages from non-admin users
        await context.bot.set_chat_permissions(
            chat_id=update.effective_chat.id,
            permissions=ChatPermissions(
                can_send_messages=False,  # Non-admins cannot send messages
            )
        )
        await update.message.reply_text("🔒 Chat is now locked. Only admins can send messages.")
        await update.message.reply_text("➖➖➖➖➖➖➖➖➖➖➖➖➖ \n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n\n कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n ➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U ONLINE GAME CLUB \n ➖➖➖➖➖➖➖➖➖➖➖➖➖")
        await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
                                           "https://t.me/AVAU_ONLINE_GAME_CLUB"
                                           "https://t.me/Payment_admin_AVAU")
    else:
        await update.message.reply_text("❌ Only admins can lock the chat.")

# Function to unlock the chat for all users
async def unlock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow everyone in the group to send messages."""
    # Check if the user issuing the command is an admin
    if update.effective_user.id in await get_admin_ids(update, context):
        # Update chat permissions to allow messages from all users
        await context.bot.set_chat_permissions(
            chat_id=update.effective_chat.id,
            permissions=ChatPermissions(
                can_send_messages=True,  # Everyone can send messages
            )
        )
        await update.message.reply_text("🔓 Chat is now unlocked. Everyone can send messages.")
        await update.message.reply_text("➖➖➖➖➖➖➖➖➖➖➖➖➖ \n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n\n कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n ➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U ONLINE GAME CLUB \n ➖➖➖➖➖➖➖➖➖➖➖➖➖")
        await update.message.reply_text(
            "🎉 Group is now open! Register and start playing the game using this link: [Register to Play](https://example.com/register)",
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
        await update.message.reply_text("Note kare: ग्रुप बंद होने के बाद किसी का पेमेंट के स्क्रीन शॉट रह जाता है तो एडमिन के पास भेजना 👇"
                                           "https://t.me/AVAU_ONLINE_GAME_CLUB"
                                           "https://t.me/Payment_admin_AVAU")
    else:
        await update.message.reply_text("❌ Only admins can unlock the chat.")

# Function to get admin IDs for the group
async def get_admin_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch the list of admin user IDs for the group."""
    chat = update.effective_chat
    admins = await context.bot.get_chat_administrators(chat.id)
    return [admin.user.id for admin in admins]

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
    await update.message.reply_text('AVAU Online Game Club : \n \n RATE : 10 ke 950 ❤‍🔥 \n\n 👉🏻(TIME TABLE) \n\n DB : 03:00 LAST \n SG : 04:30 LAST \n FD : 05:50 LAST \n GB : 08:50 LAST \n  GL : 11:25 LAST \n DS : 04:00 LAST \n\n PAYMENT NO. 💰 \n\n *paytm *  8126881875 \n\n *PhonePe *  8126881875 \n\n *Google Pay *  8126881875 \n\n ❤‍🔥RULES❤‍🔥\n\n 01. टोटल ग़लत होने पर हाफ ( आदि ) पासिंग दी जाएगी आदि पासिंग तब मिलेगी जब आप बैलेंस ++ या आपकी पेमेंट पूरी होगी | अगर बैलेंस ++ नहीं हो तो सिर्फ़ रिफ़ंड होगा । \n\n 02. ⁠क्रासिंग में विद् जोड़ा विदाउट जोड़ा क्लियर लिखा होगा चाइए । नहीं तो सिर्फ़ रिफ़ंड होगा । \n\n 03. ⁠हरफ़ में अंदर बाहर (🆎) क्लियर लिखे । 🆎 ना लिखने पर हर्फ़ बाहर का माना जाएगा । \n\n 04. ⁠मैसेज डिलीट करने से पहले एडमिन को बता दे । और रिजल्ट के बाद मेसेज डिलीट करने पर बैलेंस 00 हो जाएगा । \n\n 05. ⁠एडिट मैसेज पर कोई पासिंग रिफ़ंड नहीं होगा |  \n\n 06. ⁠अगर ++ से गेम खेलते है तो अपना हिसाब बना कर डाले हिसाब ना बनाने कोई गेम वैलिड नहीं होगा । \n\n 07. ⁠फेल गेम का कोई रिफ़ंड नहीं होगा । \n\n 08. 5 ईंटों जोड़ी और 50 ईंटों हर्फ़ वैलिड होगा । इससे कम खेलने पर आदी पासिंग दी जाएगी । \n\n 09. एक मेसेज मे डबल जोड़ी 50 ईंटों से ज़्यादा होगी तो एक बार ही जोड़ी जायेगी । 1 फोल्डर के डबल जोड़ी की 50 इंटू तक ही पासिंग दी जाएगी । \n\n LIVE IN YOUR WORLD PLAY IN OURS \n           ( AVAU )     \n\n किसी भी समस्या के लिए कांटैक्ट करे । \n\n Telegram https://t.me/AVAU_ONLINE_GAME_CLUB \n\n https://t.me/Payment_admin_AVAU \n ') 


#  Commands
async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('सभी भुगतान संख्या पर \n\n पेटीएम : 🔜 8126881875   \n\n फ़ोन पे : 🔜 8126881875   \n\n गूगल पे :🔜 8126881875   \n\n भाव 10 का 950  \n\n A.V.A.U online game club   \n\n इसके आलावा आप अगर किसी और नंबर पर पेमेंट करते हैं तो उसकी जिम्मेदारी आपकी होगी  \n\n (ADMIN)   \n\n https://t.me/AVAU_ONLINE_GAME_CLUB   \n * \n https://t.me/Payment_admin_AVAU   \n\n\n LIVE IN YOUR WORLD PLAY IN OURS \n         ( AVAU )')

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

    # Check if 10 messages have been reached
    if message_counter[chat_id] == 30:
        await update.message.reply_text(
            "➖➖➖➖➖➖➖➖➖➖➖➖➖ \n\n ‼‼‼‼‼‼‼‼‼‼‼‼‼ \n"
            "कृपया ध्यान दें हम किसी से किसी के पर्सनल में जाकर पेमेंट नहीं मांगते और ना कोई "
            "किसी प्रकार का ओटीपी , नाही किसी प्रकार का टेलीग्राम का एसएस और ना ही किसी को पर्सनल "
            "कॉल करते है अगर हमारे नाम से आपके पास कोई पेमेंट मांगता है तो सीधा ब्लॉक कर देना क्योंकि "
            "वह चोर है अगर आप फिर भी पेमेंट करते हो तो उसके जिम्मेदार आप खुद होंगे हम नहीं होंगे \n\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖ \n A.V.A.U ONLINE GAME CLUB \n ➖➖➖➖➖➖➖➖➖➖➖➖➖"
        )
        # Reset the counter to start counting again
        message_counter[chat_id] = 0
        return  # Exit after responding to avoid processing further logic
    
    """Handle messages where users type numbers directly."""
    # # Parse number lists
    delimiters = [",", "=", "-", "/", " "]
    for delimiter in delimiters:
        if delimiter in message:
            message = message.replace(delimiter, ",","")

    # Handle number claiming
    if message.replace(",", "").isdigit():
        # Extract numbers and validate
        numbers = [int(num.strip()) for num in message.split(",") if num.strip().isdigit()]

        #numbers = list(set(int(num.strip()) for num in message.split(",") if num.strip().isdigit()))
        valid_numbers = [num for num in numbers if 0 <= num <= 99]

        # Initialize game data for the chat if not present
        if chat_id not in game_data:
            game_data[chat_id] = {"numbers": {}, "opened": []}

        claimed = []
        already_claimed = []
        
        for number in valid_numbers:
            if number not in game_data[chat_id]["numbers"]:
                game_data[chat_id]["numbers"][number] = []

            # Check if the number is globally claimed (Optional: Uncomment to enforce this rule)
            # if game_data[chat_id]["numbers"][number]:
            #     already_claimed.append(number)
            #     continue

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

    if message_type in ['group', 'supergroup']:
        # Admin command detection
        if "lock chat" in text:
            if update.effective_user.id in await get_admin_ids(update, context):
                await lock_chat(update, context)  # Call the lock function
            else:
                await update.message.reply_text("❌ Only admins can lock the chat.")
            return

        if "unlock chat" in text:
            if update.effective_user.id in await get_admin_ids(update, context):
                await unlock_chat(update, context)  # Call the unlock function
            else:
                await update.message.reply_text("❌ Only admins can unlock the chat.")
            return
        
        if "live" in text:
            if update.effective_user.id in await get_admin_ids(update, context):
                await live_command(update, context)   # Call the live function
            else:
                await update.message.reply_text("❌ Only admins can live the number.")
            return    
        
        # Map specific words to corresponding commands
        if text == "ok":
            await ok_command(update, context)  # Respond to "ok"
            return

        if text == "rules":
            await rules_command(update, context)  # Respond to "rules"
            return

        if text == "pay":
            await payment_command(update, context)  # Respond to "pay"
            return

        if text == "payment":
            await payment_command(update, context)  # Respond to "payment"
            return
        
        if text == "upi":
            await payment_command(update, context)  # Respond to "payment"
            return
        
        if text == "qr":
            await payment_command(update, context)  # Respond to "payment"
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
        
        if message.lower().startswith("open"):
            if user_id in await get_admin_ids(update, context):  # Ensure only admins can open numbers
                parts = message.split()
                if len(parts) < 2:
                    await update.message.reply_text("❌ Please specify a valid number. Example: open 33")
                    return

                try:
                    number_to_open = int(parts[1])  # Extract number correctly
                except ValueError:
                    await update.message.reply_text("❌ Please specify a valid number. Example: open 33")
                    return
                

                if message.isdigit():  # User sends just a number
                    number_claimed = int(message)

                    # Ensure chat_id exists in game_data
                    if chat_id not in game_data:
                        game_data[chat_id] = {"numbers": {}, "opened": []}

                    # Ensure the number is not already claimed
                    if number_claimed not in game_data[chat_id]["numbers"]:
                        game_data[chat_id]["numbers"][number_claimed] = [user_name]  # Store user who claimed it
                        await update.message.reply_text(f"✅ {user_name} successfully claimed: {number_claimed}")
                    else:
                        await update.message.reply_text(f"⚠️ Number {number_claimed} is already claimed.")




        if BOT_USERNAME in text:
          new_text: str = text.replace(BOT_USERNAME, '').strip()
          response: str = handle_response(new_text)
        else:
          return  
    else:
        response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)


async def live_command(update: Update, context: CallbackContext) -> None :

    #check if the user is admin
    if update.effective_user.id != get_admin_ids:
        update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    text = update.message.text.strip()
    parts = text.split()

    #Validate command format
    if len(parts) != 3 or parts[0].lower() != "FD" or parts[1].lower() != "live": 
        return  # Ignore invalid message
    
    try:
        live_number = int(parts[2])   # take the admin's provided number
        # update.message.reply_text()
    except ValueError:
        update.message.reply_text("⚠️ Invalid number! Please provide a valid number. Example: `FD live 3`", parse_mode="Markdown")
        return

    #create the response message
    message = ('╔═════════════════════════╗ \n \n 🏆⚜️❂❂⚜️🏆 \n \n ＦＡＲＩＤＡＢＡＤ \n \n 𝗟𝗜𝗩𝗘 \n\n  \n\n ╚═════════════════════════╝ \n\n 📌 *Telegram link:*\n  \n📌 *WhatsApp Numbers:*\n')    

    # Send the message
    update.message.reply_text(message, parse_mode="Markdown")

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

     # Perform OCR to extract text from the image
    try:

        # Check if extracted text contains payment-related keywords
        if any(keyword for keyword in PAYMENT_KEYWORDS):
            await update.message.reply_text("✅ We have received your photo! Our team will verify it soon.")
        else:
            await update.message.reply_text("✅ Payment was received! Our team will verify it soon.")
    
    except Exception as e:
        await update.message.reply_text("❌ Failed to process the image. Please try again.")
        print(f"Error processing image: {e}")

    # Clean up (delete the saved image to free space)


if __name__ == '__main__':
    print('starting bot...')
    app = Application.builder().token(TOKEN).read_timeout(30).write_timeout(30).build()


    # Commands
    app.add_handler(CommandHandler('start', start_command))            
    app.add_handler(CommandHandler('ok', ok_command))            
    app.add_handler(CommandHandler('rules', rules_command))            
    app.add_handler(CommandHandler('payment', payment_command))            
    app.add_handler(CommandHandler('pay', payment_command))            
    app.add_handler(CommandHandler('qr', payment_command))            
    app.add_handler(CommandHandler('upi', payment_command))
    app.add_handler(CommandHandler('lock', lock_chat))
    app.add_handler(CommandHandler('unlock', unlock_chat))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message,))


    # Add handlers for getting and opening numbers
    app.add_handler(CommandHandler('get', handle_message))
    app.add_handler(CommandHandler('claim', claim_number))
    app.add_handler(CommandHandler('open', open_number))

    #updater check media files
    app.add_handler(CommandHandler("photo", send_photo))
    app.add_handler(CommandHandler("audio", send_audio))
    app.add_handler(CommandHandler("live", live_command))
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))


    #Errors  
    app.add_error_handler(error)

    print(game_data)

    #Poll the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
    # app.idle()
           
