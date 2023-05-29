from ctransformers import AutoModelForCausalLM
from telegram.error import BadRequest, RetryAfter
from telegram.ext import *
import multiprocessing
import configparser
import threading
import telegram
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
else:
    censor = ""

model = config.get("Ai", "model")
model_type = config.get("Ai", "model_type")
model_size = config.get("Ai", "model_size")
path = "models/" + model + "-" + model_size + censor + ".bin"

llm = AutoModelForCausalLM.from_pretrained(path, model_type=model_type, lib=config.get("Ai", "instruction_set"))

# Limit the number of parallel processes
max_parallel_processes = int(config.get("Chat", "max_parallel_chats"))
process_semaphore = multiprocessing.Semaphore(max_parallel_processes)

# Define process manager
manager = multiprocessing.Manager()
active_processes_count = manager.Value('i', 0)
active_processes_lock = manager.Lock()

def ai(update, context):
    # Increase the value of the processes count
    with active_processes_lock:
        active_processes_count.value += 1

    # Start a new chat
    process = multiprocessing.Process(target=inference, args=(update, context, active_processes_count, active_processes_lock))
    process.start()
    
# AI command
def inference(update, context, active_processes_count, active_processes_lock):
    # Execute with the limit imposed by max_parallel_processes
    with process_semaphore:
        # Get new delay in seconds
        with active_processes_lock:
            num_active_processes = active_processes_count.value
        # Get message from user
        mex = update.message.text
        mex = mex.replace("/ai", "")
        response = ""
        # Define the tokens
        tokens = llm.tokenize(str(config.get("Ai", "prompt") + '\n\n### Instruction:\n\n' + mex + '\n\n ###Response:\n\n'))

        # Initialize variables
        sent_message = False
        prompt_is_done = False

        # Define a fragmenter for sending edited messages every n seconds
        def fragmenter():
            while not prompt_is_done:
                try:
                    context.bot.editMessageText(chat_id=update.message.chat_id,
                                                message_id=context.user_data['bot_last_message_id'],
                                                text=response)
                except BadRequest:
                    pass
                except KeyError:
                    pass
                except RetryAfter:
                    print("Flood control triggered. Retrying in 10 seconds...")
                    time.sleep(10)
                # Get new delay in seconds
                with active_processes_lock:
                    num_active_processes = active_processes_count.value
                    print(num_active_processes)

                time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)
                print(int(config.get("Chat", "edit_delay")) * num_active_processes)

        def is_typing():
            # Set bot as typing
            while not prompt_is_done:
                context.bot.sendChatAction(chat_id=update.message.chat_id, action = telegram.ChatAction.TYPING)
                time.sleep(4)

        # Start the defragmenter and ignore the initial KeyError exception
        defragmenter_thread = threading.Thread(target=fragmenter)
        defragmenter_thread.start()

        # Start the typing state
        is_typing_thread = threading.Thread(target=is_typing)
        is_typing_thread.start()

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
                context.bot.sendChatAction(chat_id=update.message.chat_id, action = telegram.ChatAction.TYPING)
                time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)
        prompt_is_done = True

        # Edit the message one last time with the final response
        while True:
            try:
                context.bot.editMessageText(chat_id=update.message.chat_id,
                                            message_id=context.user_data['bot_last_message_id'],
                                            text=response)
                break
            except BadRequest:
                pass
            except RetryAfter:
                        print("Flood control triggered. Retrying in 10 seconds...")
                        time.sleep(10)

# Bot handlers
ai_handler = CommandHandler('ai', ai)

# Bot dispatchers
dispatcher.add_handler(ai_handler)

# Bot polling
updater.start_polling()