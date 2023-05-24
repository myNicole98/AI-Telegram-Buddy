<h3 align="center">
<img src="assets/buddy.png" height="100" width="100"/></br>
<b>AI Telegram Buddy</b></a>
</h3>

## About
AI Telegram Buddy is an AI-powered Python Telegram bot designed to assist and entertain users on the Telegram platform.

## Todo

* [x] Core functionality
* [ ] Chat history per user
* [ ] Docker support
* [ ] Support for all major ggml models 

## Requirements

- <a href=https://www.python.org/>Python</a> 3.11
- A <a href=https://core.telegram.org/bots/tutorial#obtain-your-bot-token>telegram bot token</a>

## Install


### Open a terminal and follow these steps

1. <b>Clone this repository</b>:

```git clone https://gitea.nikko.cf/nikko/AI-Telegram-Buddy```
<br>```cd AI-Telegram-Buddy```

2. <b>Install the requirements:</b>

```pip install -r requirements.txt```

## Getting Started

1. <b>Download model</b>: Execute the model downloader program and follow its instructions

```python model-downloader.py```

2. <b>Configuration</b>: populate your `config.ini` with the required <b>bot token</b> and make sure to define the <b>model</b> and <b>model_type</b> of your previously downloaded model.

3. <b>Run the bot</b>:

```python main.py```

4. <b>Interact with your bot</b>: Open the Telegram app, search for your bot's username, and start interacting with it by sendind the `/ai` command followed by a message (e.g. `/ai hello there, nice to meet you`)

## Contributing

Contributions to AI Telegram Buddy are welcome! If you find any issues, have suggestions for improvements, or want to add new features, please feel free to open an issue or submit a pull request. Make sure to follow the existing coding style and include relevant tests.

## Disclaimer

AI Telegram Buddy is an open-source project developed by an independent contributor. While I strive to provide accurate and helpful informations, depending on the model in use the bot's responses might not always be perfect or up-to-date, and can be prone to negative social biases. Please refer to the documentation of any model before downloading it.

## ❤️ Gratitude
Thanks to the following tools developing this project is possible:

- <a href=https://github.com/marella/ctransformers>ctransformers</a>: Python bindings for the Transformer models implemented in C/C++ using GGML library.

- <a href=https://python-telegram-bot.org/>python-telegram-bot</a>: A telegram API wrapper