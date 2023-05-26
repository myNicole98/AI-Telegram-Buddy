from ctransformers import AutoModelForCausalLM
from telegram.error import BadRequest
from telegram.ext import *
import configparser
import threading
import time

# Config initialization
config = configparser.ConfigParser()
config.read('config.ini')

# Bot initialization
updater = Updater(token=config.get("Bot", "token"), use_context=True)
dispatcher = updater.dispatcher


# AI model loading
if config.get("Ai", "uncensored") == "yes":
    censor = "-UNCENSORED"
else: censor = ""
llm = AutoModelForCausalLM.from_pretrained("models/" + config.get("Ai", "model") + "-" + config.get("Ai", "model_size") + censor + ".bin", model_type=config.get("Ai", "model_type"))


# AI command
def ai(update, context):
    # Get message from user
    mex = update.message.text
    mex = mex.replace("/ai", "")
    response = ""

    # Define the tokens
    tokens = llm.tokenize(str(config.get("Ai", "prompt") + '\n\n### Instruction:\n\n' + mex + '\n\n ###Response:\n\n'))
    
    # Initialize variables
    sent_message = False
    prompt_is_done = False

    # Define a fragmenter for sending edited messages every second
    def fragmenter():
        while not prompt_is_done:
            try:
                context.bot.editMessageText(chat_id=update.message.chat_id,
                                            message_id=context.user_data['bot_last_message_id'],
                                            text=response)
            except BadRequest: pass
            except KeyError: pass
            time.sleep(int(config.get("Chat", "edit_delay")))

    # Start the defragmenter and ignore the initial KeyError exception
    thread = threading.Thread(target=fragmenter)
    thread.start()

    # Tokenize the response into fragmented responses
    for token in llm.generate(tokens):
        fragresp = llm.detokenize(token)
        response = response + fragresp

        # Send initial message
        if not sent_message:
            msg = context.bot.send_message(chat_id=update.effective_chat.id, text=response,
                  reply_to_message_id=update.message.message_id)
            context.user_data['bot_last_message_id'] = msg.message_id
            sent_message = True
            time.sleep(int(config.get("Chat", "edit_delay")))
    prompt_is_done = True

    # Edit the message one last time with the final response
    try:
        context.bot.editMessageText(chat_id=update.message.chat_id,
                                                message_id=context.user_data['bot_last_message_id'],
                                                text=response)
    except BadRequest: pass
    # End the threading
    thread.join()

# Bot handlers
ai_handler = CommandHandler('ai', ai)

#Bot dispatchers
dispatcher.add_handler(ai_handler)

# Bot polling
updater.start_polling()