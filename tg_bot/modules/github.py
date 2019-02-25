from telegram import ParseMode, Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

from requests import get


@run_async
def github(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/git '):]
    usr = get(f'https://api.github.com/users/{text}').json()
    if usr.get('login'):
        reply_text = f"""*Name:* `{usr['name']}`
*Login:* `{usr['login']}`
*Location:* `{usr['location']}`
*Type:* `{usr['type']}`
*Bio:* `{usr['bio']}`"""
    else:
        reply_text = "User not found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

__help__ = """
 - /git:{GitHub username} Returns info about a GitHub user or organization.
"""

__mod_name__ = "GitHub username info"

github_handle = DisableAbleCommandHandler("git", github)

dispatcher.add_handler(github_handle)
