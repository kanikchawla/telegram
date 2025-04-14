import os
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackContext

# Set your bot token
TELEGRAM_BOT_TOKEN = "8061973116:AAEugstumhfIEo2qkL59Ro2qeQiM0JWk0BA"

# Directories
UPLOAD_FOLDER = "uploads"
PDF_FOLDER = "pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# States for conversation
NAME, AGE, APP_ID, AUDIO = range(4)


# User details storage
user_data_store = {}

def convert_to_wav(input_path):
    """Convert audio file to WAV format using FFmpeg."""
    output_path = os.path.splitext(input_path)[0] + ".wav"
    
    if os.path.exists(output_path):
        os.remove(output_path)

    try:
        subprocess.run(["ffmpeg", "-y", "-i", input_path, output_path], check=True)
        return output_path if os.path.exists(output_path) else None
    except subprocess.CalledProcessError:
        return None


async def start(update: Update, context: CallbackContext):
    """Handles the /start command and initiates the conversation professionally."""
    await update.message.reply_text(
        "Welcome to Resonanze, your personalized voice analysis assistant.\n\n"
        "To get started, may I have your full name?"
    )
    return NAME


async def get_name(update: Update, context: CallbackContext):
    """Stores the user's name and asks for age."""
    user_data_store[update.message.chat_id] = {"name": update.message.text}
    await update.message.reply_text("Thank you. Could you please provide your age?")
    return AGE


async def get_age(update: Update, context: CallbackContext):
    """Stores age and asks for the appointment ID."""
    user_data_store[update.message.chat_id]["age"] = update.message.text
    await update.message.reply_text("Got it. Please enter your Appointment ID.")
    return APP_ID


async def get_app_id(update: Update, context: CallbackContext):
    """Stores appointment ID and requests a voice message."""
    user_data_store[update.message.chat_id]["appointment_id"] = update.message.text
    await update.message.reply_text(
        "Thank you for providing the details.\n\n"
        "Now, please send a voice message so we can proceed with the analysis."
    )
    return AUDIO



async def process_audio(update: Update, context: CallbackContext):
    """Handles incoming audio messages."""
    file = update.message.voice or update.message.audio
    if not file:
        await update.message.reply_text("No valid audio file received.")
        return AUDIO

    user_info = user_data_store.get(update.message.chat_id, {})

    if not user_info:
        await update.message.reply_text("Please start with /start and provide your details first.")
        return AUDIO

    # Download the file
    file_id = file.file_id
    audio_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.ogg")
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(audio_path)

    # Convert to WAV
    wav_path = convert_to_wav(audio_path)
    if not wav_path:
        await update.message.reply_text("Audio conversion failed.")
        return AUDIO

    # Generate PDF report
    pdf_path = os.path.join(PDF_FOLDER, f"{file_id}.pdf")

    script_path = "/Users/kaniklchawla/Desktop/telegrm/report_generation.py"
    if not os.path.exists(script_path):
        await update.message.reply_text("Error: Missing report_generation.py script.")
        return AUDIO

    try:
        subprocess.run([
            "python3", script_path, wav_path, pdf_path, 
            user_info["name"], user_info["age"], user_info["appointment_id"]

        ], check=True)
    except subprocess.CalledProcessError:
        await update.message.reply_text("Failed to generate PDF report.")
        return AUDIO

    # Send the generated PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(pdf_file, caption="Here is your medical report.")
    else:
        await update.message.reply_text("PDF report generation failed.")

    return ConversationHandler.END


def main():
    """Starts the bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
        APP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_app_id)],
        AUDIO: [MessageHandler(filters.VOICE | filters.AUDIO, process_audio)],
    },
    fallbacks=[CommandHandler("start", start)],
)


    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
