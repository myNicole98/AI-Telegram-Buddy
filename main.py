from ctransformers import AutoModelForCausalLM
from telegram.error import BadRequest
from telegram.ext import *
import configparser

# Config initialization
config = configparser.ConfigParser()
config.read('config.ini')

# Bot initialization
updater = Updater(token=config.get("Bot", "token"), use_context=True)
dispatcher = updater.dispatcher

# AI model loading
llm = AutoModelForCausalLM.from_pretrained("models/" + config.get("Ai", "model") + "-" + config.get("Ai", "model_size") + ".bin", model_type=config.get("Ai", "model_type"))

def ai(update, context):
    # Get message from user
    mex = update.message.text
    mex = mex.replace("/ai", "")

    # Reply to message
    response = llm(config.get("Ai", "prompt") + '\n\n### Instruction:\n\n' + mex + '\n\n ###Response:\n\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=response,
            reply_to_message_id=update.message.message_id)


# Bot handlers
ai_handler = CommandHandler('ai', ai)

#Bot dispatchers
dispatcher.add_handler(ai_handler)

# Bot polling
updater.start_polling()