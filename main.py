from telegram.error import BadRequest, RetryAfter, TimedOut, NetworkError
from ctransformers import AutoModelForCausalLM
from langchain.llms import CTransformers
from telegram.ext import *
import multiprocessing
import configparser
import threading
import telegram
import sqlite3
import time
import os

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

llm = AutoModelForCausalLM.from_pretrained(path, model_type=model_type, lib=config.get("Ai", "instruction_set"), last_n_tokens=256)

if config.get("Chat", "summary") == "yes":
    llm_lang = CTransformers(model=path, model_type=model_type, lib=config.get("Ai", "instruction_set"))

# Limit the number of parallel processes
if config.get("Chat", "history") == "yes":
    max_parallel_processes = 1
else: max_parallel_processes = int(config.get("Chat", "max_parallel_chats"))
process_semaphore = multiprocessing.Semaphore(max_parallel_processes)

# Define process manager
manager = multiprocessing.Manager()
active_processes_count = manager.Value('i', 0)
active_processes_lock = manager.Lock()

# Database initialization
history_db = sqlite3.connect("history.db")
history = history_db.cursor()
history.execute("CREATE TABLE IF NOT EXISTS History (user_id INT, user_history TEXT, history_size INT)")
history_db.close()

def ai(update, context):
    # Increase the value of the processes count
    with active_processes_lock:
        active_processes_count.value += 1
    
    # Get message from user
    mex = update.message.text
    mex = mex.replace("/ai ", "")

    # Define the tokens
    tokens = llm.tokenize(str(config.get("Ai", "prompt") + '\n\n### Instruction:\n\n' + mex + '\n\n### Response:\n\n'))

    # Is this using langchain
    langchain = False

    # Start a new chat
    process = multiprocessing.Process(target=inference, args=(update, context, active_processes_count, active_processes_lock, mex, tokens, langchain))
    process.start()

def summarize(update, context):
    if config.get("Chat", "summary") == "yes":
        # Increase the value of the processes count
        with active_processes_lock:
            active_processes_count.value += 1
        with process_semaphore:
            # Get new delay in seconds
            with active_processes_lock:
                num_active_processes = active_processes_count.value
        
        # Check if directory exists
        if not os.path.exists('media/summarize/'):
                os.makedirs('media/summarize/')
        
        # Valid file extensions
        extensions = [".txt"]

        prompt_is_done = False
        def is_thinking():
            suspance = 1
            # Set bot as typing
            while not prompt_is_done:
                while True:
                    try:
                        context.bot.sendChatAction(chat_id=update.message.chat_id, action = telegram.ChatAction.TYPING)
                        context.bot.editMessageText(chat_id=update.message.chat_id,
                                                message_id=context.user_data['bot_last_message_id'],
                                                text="Summarizing" + "." * suspance)
                        if suspance >= 3:
                            suspance = 1
                        else: 
                            suspance += 1
                        time.sleep(4)
                        break
                    except NetworkError:
                        time.sleep(1)

        # Get file from user
        try:
            file = update.message.reply_to_message.document.get_file()
            file_path = file['file_path']
            file_extension = os.path.splitext(file_path)[1]
            if file_extension in extensions:
                file.download("media/summarize/document.txt")
                f = open("media/summarize/document.txt", "r")
                mex = f.read()

                msg = context.bot.send_message(chat_id=update.effective_chat.id, text="Summarizing",
                                                    reply_to_message_id=update.message.message_id)
                context.user_data['bot_last_message_id'] = msg.message_id

                # Start the typing state
                is_thinking_thread = threading.Thread(target=is_thinking)
                is_thinking_thread.start()

                response = llm_lang(mex)
                prompt_is_done = True

                while True:
                    try:
                        context.bot.editMessageText(chat_id=update.message.chat_id,
                                                    message_id=context.user_data['bot_last_message_id'],
                                                    text=response)
                        break
                    #except BadRequest:
                    #    time.sleep(1)
                    #    pass
                    except RetryAfter:
                                print("Flood control triggered. Retrying in 10 seconds...")
                                time.sleep(10)
                    except TimedOut:
                        pass
                    except NetworkError:
                        pass
            else:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                            text="Invalid text file")
                return None

        except AttributeError:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                            text="No file selected")
        # Decrease the process count
        with active_processes_lock:
            active_processes_count.value -= 1
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                            text="Summary feature is not enabled.")

# AI command
def inference(update, context, active_processes_count, active_processes_lock, mex, tokens, langchain):
    # Execute with the limit imposed by max_parallel_processes
    with process_semaphore:
        # Get new delay in seconds
        with active_processes_lock:
            num_active_processes = active_processes_count.value
        
        # Initialize response
        response = ""
        if config.get("Chat", "history") == "yes":
            # Initialize database
            history_db = sqlite3.connect("history.db")
            history = history_db.cursor()

            # Get user ID
            user_id = update.message.from_user.id
            history.execute("INSERT OR IGNORE INTO History (user_id) VALUES (?)", (user_id,))

            # Get user history
            history.execute("SELECT user_history FROM History WHERE user_id = ?", (user_id,))
            fetch = history.fetchone()[0]
            try:
                mex = fetch + "USER: " + mex + "\n" + "ASSISTANT: "
            except TypeError:
                mex = config.get("Ai", "prompt") + "\nUSER: " + mex + "\n" + "ASSISTANT: "
            while True:
                try:
                    history_db.commit()
                    history_db.close()
                    break
                except sqlite3.OperationalError:
                    pass        

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
                except TimedOut:
                    time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)
                    pass
                except NetworkError:
                    time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)
                    pass
                # Get new delay in seconds
                with active_processes_lock:
                    num_active_processes = active_processes_count.value

                time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)

        def is_typing():
            # Set bot as typing
            while not prompt_is_done:
                while True:
                    try:
                        context.bot.sendChatAction(chat_id=update.message.chat_id, action = telegram.ChatAction.TYPING)
                        time.sleep(4)
                        break
                    except NetworkError:
                        time.sleep(1)

        # Start the defragmenter and ignore the initial KeyError exception
        fragmenter_thread = threading.Thread(target=fragmenter)
        fragmenter_thread.start()

        # Start the typing state
        is_typing_thread = threading.Thread(target=is_typing)
        is_typing_thread.start()

        # Tokenize the response into fragmented responses
        for token in llm.generate(tokens):
            fragresp = llm.detokenize(token)
            response = response + fragresp

            # Send initial message
            if not sent_message:
                try:
                    msg = context.bot.send_message(chat_id=update.effective_chat.id, text=response,
                                                reply_to_message_id=update.message.message_id)
                    context.user_data['bot_last_message_id'] = msg.message_id
                    sent_message = True
                    while True:
                        try:
                            context.bot.sendChatAction(chat_id=update.message.chat_id, action = telegram.ChatAction.TYPING)
                            break
                        except NetworkError:
                            time.sleep(1)
                    time.sleep(int(config.get("Chat", "edit_delay")) * num_active_processes)
                except BadRequest: pass

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
            except TimedOut:
                pass
            except NetworkError:
                pass
            finally:
                prompt_is_done = True
                
                # Decrease the process count
                with active_processes_lock:
                    active_processes_count.value -= 1
                
                # Add conversation to history
                if config.get("Chat", "history") == "yes":
                    # Connect to database
                    history_db = sqlite3.connect("history.db")
                    history = history_db.cursor()
                    # Merge conversation
                    merged_mex = mex + response + "\n"
                    history.execute("SELECT user_history FROM History WHERE user_id = ?", (user_id,))
                    current_user_history = history.fetchone()[0]
                    try:
                        current_user_history = current_user_history + "\n\n" + merged_mex
                    except TypeError:
                        current_user_history = merged_mex
                    
                    # Append conversation to database
                    history.execute("UPDATE History SET user_history = ? WHERE user_id = ?", (current_user_history, user_id))
                    while True:
                        try:
                            history_db.commit()
                            history_db.close()
                            break
                        except sqlite3.OperationalError: pass

def clear(update, context):
    if config.get("Chat", "history") == "yes":
        # Get user ID
        user_id = update.message.from_user.id

        # Delete history
        history_db = sqlite3.connect("history.db")
        history = history_db.cursor()
        history.execute("UPDATE History SET user_history = NULL, history_size = NULL WHERE user_id = ?", (user_id,))
        history_db.commit()
        msg = context.bot.send_message(chat_id=update.effective_chat.id, text="History cleared",
                                        reply_to_message_id=update.message.message_id)
        history_db.close()
    else:
        msg = context.bot.send_message(chat_id=update.effective_chat.id, text="Chat history is not enabled. Nothing to clear",
                                        reply_to_message_id=update.message.message_id)

# Bot handlers
ai_handler = CommandHandler('ai', ai)
clear_handler = CommandHandler('clear', clear)
summarize_handler = CommandHandler('summarize', summarize)

# Bot dispatchers
dispatcher.add_handler(ai_handler)
dispatcher.add_handler(clear_handler)
dispatcher.add_handler(summarize_handler)

# Bot polling
updater.start_polling()