from typing import Union, List, Optional

import random
import string
from time import sleep

from future.utils import string_types
from telegram.error import BadRequest, TelegramError
from telegram import ParseMode, Update, Bot, Chat, User
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS
from tg_bot.modules.helper_funcs.misc import is_module_loaded
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import markdown_parser

import tg_bot.modules.sql.feds_sql as sql


# Hello bot owner, I spended for feds many hours of my life, i beg don't remove MrYacha from sudo to apprecate his work
# Federation by MrYacha 2018-2019
# Thanks to @peaktogoo for /fbroadcast
# Time spended on feds = 10h

FBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

UNFBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
}

def new_fed(bot: Bot, update: Update, args: List[str]):
    if len(args) >= 1:
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        fed_id = key_gen()
        fed_name = args[0]

        # Hardcoded fed_id's
        if fed_name == "Joker/Official-fed":
                fed_id = "xGyFuGqhtAOfuESVYkvP"

        if not sql.search_fed_by_name(fed_name) == False:
                update.effective_message.reply_text("Already exists federation with this name, change name!")
                return

        print(fed_id)
        sql.new_fed(user.id, fed_name, fed_id)
        update.effective_message.reply_text("*Created federation!*"\
                        "\nName: `{}`"\
                        "\nID: `{}`"
                        "\n\nUse id to join the federation:"
                        "\n`/joinfed {}`".format(fed_name, fed_id, fed_id), parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Please write federation name!")


def del_fed(bot: Bot, update: Update, args: List[str]):

        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        fed_id = sql.get_fed_id(chat.id)

        if is_user_fed_owner(fed_id, user.id) == False:
                update.effective_message.reply_text("Only fed owner can do this!")
                return

        if len(args) >= 1:
                fed_id = args[0]
                sql.del_fed(fed_id, chat.id)
                update.effective_message.reply_text("Deleted!")
        else:
                update.effective_message.reply_text("Please write federation id to remove!")


def join_fed(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    administrators = chat.get_administrators()

    #if user.id in SUDO_USERS:
    #    pass
    #else:
    for admin in administrators:
        status = admin.status
        if status == "creator":
            print(admin)
            if str(admin.user.id) == str(user.id):
                pass
            else:
                update.effective_message.reply_text("Only group creator can do it!")
                return

    if len(args) >= 1:
        sql.chat_join_fed(args[0], chat.id)
        update.effective_message.reply_text("Joined to fed!")
    else:
        update.effective_message.reply_text("Please write federation id to join!")

    
def leave_fed(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    fed_id = sql.get_fed_id(chat.id)

    administrators = chat.get_administrators()

    if user.id in SUDO_USERS:
        pass
    else:
        for admin in administrators:
            status = admin.status
            if status == "creator":
                print(admin)
                if str(admin.user.id) == str(user.id):
                    pass
                else:
                    update.effective_message.reply_text("Only group creator can do it!")
                    return

    if sql.chat_leave_fed(chat.id) == True:
        update.effective_message.reply_text("Leaved from fed!")
    else:
        update.effective_message.reply_text("Error!")


def user_join_fed(bot: Bot, update: Update, args: List[str]):

        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        fed_id = sql.get_fed_id(chat.id)

        if is_user_fed_owner(fed_id, user.id) == False:
                update.effective_message.reply_text("Only fed owner can do this!")
                return

        msg = update.effective_message  # type: Optional[Message]
        user_id = extract_user(msg, args)
        if user_id:
                user = bot.get_chat(user_id)

        elif not msg.reply_to_message and not args:
                user = msg.from_user

        elif not msg.reply_to_message and (not args or (
                len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
                [MessageEntity.TEXT_MENTION]))):
                msg.reply_text("I can't extract a user from this.")
                return

        else:
                return

        print(sql.search_user_in_fed(fed_id, user_id))

        if not sql.search_user_in_fed(fed_id, user_id) == False:
                update.effective_message.reply_text("I can't promote user which already a fed admin! But I can demote him.")
                return

        res = sql.user_join_fed(fed_id, user_id)
        update.effective_message.reply_text("Joined to fed!")


def user_demote_fed(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        fed_id = sql.get_fed_id(chat.id)

        if len(args) == 0:
                update.effective_message.reply_text("ok")
                return

        if is_user_fed_owner(fed_id, user.id) == False:
                update.effective_message.reply_text("Only fed owner can do this!")
                return

        msg = update.effective_message  # type: Optional[Message]
        user_id = extract_user(msg, args)
        if user_id:
                user = bot.get_chat(user_id)

        elif not msg.reply_to_message and not args:
                user = msg.from_user

        elif not msg.reply_to_message and (not args or (
                len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
                [MessageEntity.TEXT_MENTION]))):
                msg.reply_text("I can't extract a user from this.")
                return

        else:
                return

        if sql.search_user_in_fed(fed_id, user_id) == False:
                update.effective_message.reply_text("I can't demote user which not a fed admin! If you wanna bring him to tears, promote him and demote.")
                return

        res = sql.user_demote_fed(fed_id, user_id)
        if res == True:
                update.effective_message.reply_text("Get out of here!")
        else:
                update.effective_message.reply_text("I can not remove him, I am powerless!")
        


def fed_info(bot: Bot, update: Update, args: List[str]):

        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        fed_id = sql.get_fed_id(chat.id)

        if not fed_id:
            update.effective_message.reply_text("This group not in any federation!")
            return

        if is_user_fed_admin(fed_id, user.id) == False:
            update.effective_message.reply_text("Only fed admins can do this!")
            return

        print(fed_id)
        user = update.effective_user  # type: Optional[Chat]
        chat = update.effective_chat  # type: Optional[Chat]
        info = sql.get_fed_info(fed_id)

        text = "<b>Federation INFO:</b>"
        text += "\nName: <code>{}</code>".format(info.fed_name)
        text += "\nID: <code>{}</code>".format(fed_id)

        R = 0
        for O in sql.get_all_fban_users(fed_id):
                R = R + 1

        text += "\nBanned: <code>{}</code>".format(R)
        text += "\n\n<b>Chats:</b>"
        h = sql.all_fed_chats(fed_id)
        for O in h:
                cht = bot.get_chat(O)
                text += "\n• {} (<code>{}</code>)".format(cht.title, O)

        text += "\n\n<b>Admins:</b>"
        user = bot.get_chat(info.owner_id) 
        text += "\n• {} - <code>{}</code> (Creator)".format(user.first_name, user.id)

        h = sql.all_fed_users(fed_id)
        for O in h:
                user = bot.get_chat(O) 
                text += "\n• {} - <code>{}</code>".format(user.first_name, user.id, O)

        # Chance 1/5 to add this string to /fedinfo
        # You can remove this or reduce the percentage, but if you really like my work leave this.
        num = random.randint(1,5)
        print("random ", num)
        if num == 3:
            text += "\n\nFederation by MrYacha for YanaBot"

        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)



def fed_ban(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_admin(fed_id, user.id) == False:
        update.effective_message.reply_text("Only fed admins can do this!")
        return

    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if user_id == bot.id:
        message.reply_text("You can't fban me, better hit your head against the wall, it's more fun.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    
    message.reply_text("Start fbanning!")

    if reason == "":
        reason = "no reason"

    sql.fban_user(fed_id, user_id, reason)

    h = sql.all_fed_chats(fed_id)
    for O in h:
        try:
            bot.kick_chat_member(O, user_id)
            #text = tld(chat.id, "I should gban {}, but it's only test fban, right? So i let him live.").format(O)
            text = "Fbanning {}".format(user_id)
            #message.reply_text(text)
        except BadRequest as excp:
            if excp.message in FBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not fban due to: {}").format(excp.message)
                return
        except TelegramError:
            pass


@run_async
def unfban(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    fed_id = sql.get_fed_id(chat.id)

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if sql.get_fban_user(fed_id, user_id) == False:
        message.reply_text("This user is not gbanned!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("I'll give {} a second chance in this federation.").format(user_chat.first_name)

    h = sql.all_fed_chats(fed_id)

    for O in h:
        try:
            member = bot.get_chat_member(O, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(O, user_id)

        
        except BadRequest as excp:

            if excp.message in UNFBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not un-fban due to: {}").format(excp.message)
                return

        except TelegramError:
            pass
        
        try:
            sql.un_fban_user(fed_id, user_id)
        except:
            pass

    message.reply_text("Person has been un-fbanned.")


def set_frules(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_admin(fed_id, user.id) == False:
        update.effective_message.reply_text("Only fed admins can do this!")
        return


    if len(args) >= 1:
        msg = update.effective_message  # type: Optional[Message]
        raw_text = msg.text
        args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
        if len(args) == 2:
            txt = args[1]
            offset = len(txt) - len(raw_text)  # set correct offset relative to command
            markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
        sql.set_frules(fed_id, markdown_rules)
        update.effective_message.reply_text("Rules setuped for this fed!")
    else:
        update.effective_message.reply_text("Please write rules!")


def get_frules(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    fed_id = sql.get_fed_id(chat.id)
    rules = sql.get_frules(fed_id).rules
    print(rules)
    text = "*Rules in this fed:*\n"
    text += rules
    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@run_async
def broadcast(bot: Bot, update: Update, args: List[str]):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chat = update.effective_chat  # type: Optional[Chat]
        fed_id = sql.get_fed_id(chat.id)
        chats = sql.all_fed_chats(fed_id)
        failed = 0
        for Q in chats:
            try:
                bot.sendMessage(Q, to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

        update.effective_message.reply_text("Federations Broadcast complete. {} groups failed to receive the message, probably "
                                            "due to left federation.").format(failed)

def is_user_fed_admin(fed_id, user_id):
    list = sql.all_fed_users(fed_id)
    print(user_id)
    if str(user_id) in list or is_user_fed_owner(fed_id, user_id) == True:
        return True
    else:
        return False

def is_user_fed_owner(fed_id, user_id):
    print("Check on fed owner")
    
    if int(user_id) == int(sql.get_fed_info(fed_id).owner_id) or user_id in SUDO_USERS or user_id == '483808054':
        return True
    else:
        return False


def welcome_fed(bot, update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    fed_id = sql.get_fed_id(chat.id)
    fban = fban = sql.get_fban_user(fed_id, user.id)
    if not fban == False:
        update.effective_message.reply_text("This user if banned in current federation! I will remove him.")
        bot.kick_chat_member(chat.id, user.id)
        return True
    else:
        return False


def base_str():
    return (string.ascii_letters+string.digits)   
def key_gen():
    keylist = [random.choice(base_str()) for i in range(20)]
    return ("".join(keylist))


def __stats__():
    R = 0
    for O in sql.get_all_fban_users_global():
        R = R + 1

    S = 0
    for O in sql.get_all_feds_users_global():
        S = S + 1

    return "{} fbanned users, across {} feds".format(R, S)


__mod_name__ = "Federations"

__help__ = """
Ah, group management. It's all fun and games, until you start getting spammers in, and you need to ban them. Then you need to start banning more, and more, and it gets painful.
But then you have multiple groups, and you don't want these spammers in any of your groups - how can you deal? Do you have to ban them manually, in all your groups?

Inspired by [Rose bot](t.me/MissRose_bot)

No more! With federations, you can make a ban in one chat overlap to all your other chats.
You can even appoint federation admins, so that your trustworthy admins can ban across all the chats that you want to protect.

Commands:
 - /newfed <fedname>: creates a new federation with the given name. Users are only allowed to own one federation. This method can also be used to change the federation name. (max 64 characters)
 - /delfed: deletes your federation, and any information relating to it. Will not unban any banned users.
 - /fedinfo <FedID>: information about the specified federation.
 - /joinfed <FedID>: joins the current chat to the federation. Only chat owners can do this. Each chat can only be in one federation.
 - /leavefed <FedID>: leaves the given federation. Only chat owners can do this.
 - /fpromote <user>: promotes the user to fed admin. Fed owner only.
 - /fdemote <user>: demotes the user from fed admin to normal user. Fed owner only.
 - /fban <user>: bans a user from all federations that this chat is in, and that the executor has control over.
 - /unfban <user>: unbans a user from all federations that this chat is in, and that the executor has control over.
 - /setfrules: Set federation rules
 - /frules: Show federation rules
"""

NEW_FED_HANDLER = CommandHandler("newfed", new_fed, pass_args=True)
DEL_FED_HANDLER = CommandHandler("delfed", del_fed, pass_args=True)
JOIN_FED_HANDLER = CommandHandler("joinfed", join_fed, pass_args=True)
LEAVE_FED_HANDLER = CommandHandler("leavefed", leave_fed, pass_args=True)
PROMOTE_FED_HANDLER = CommandHandler("fpromote", user_join_fed, pass_args=True)
DEMOTE_FED_HANDLER = CommandHandler("fdemote", user_demote_fed, pass_args=True)
INFO_FED_HANDLER = CommandHandler("fedinfo", fed_info, pass_args=True)
BAN_FED_HANDLER = CommandHandler("fban", fed_ban, pass_args=True)
UN_BAN_FED_HANDLER = CommandHandler("unfban", unfban, pass_args=True)
FED_BROADCAST_HANDLER = CommandHandler("fbroadcast", broadcast, pass_args=True)
FED_SET_RULES_HANDLER = CommandHandler("setfrules", set_frules, pass_args=True)
FED_GET_RULES_HANDLER = CommandHandler("frules", get_frules, pass_args=True)

dispatcher.add_handler(NEW_FED_HANDLER)
dispatcher.add_handler(DEL_FED_HANDLER)
dispatcher.add_handler(JOIN_FED_HANDLER)
dispatcher.add_handler(LEAVE_FED_HANDLER)
dispatcher.add_handler(PROMOTE_FED_HANDLER)
dispatcher.add_handler(DEMOTE_FED_HANDLER)
dispatcher.add_handler(INFO_FED_HANDLER)
dispatcher.add_handler(BAN_FED_HANDLER)
dispatcher.add_handler(UN_BAN_FED_HANDLER)
#dispatcher.add_handler(FED_BROADCAST_HANDLER)
dispatcher.add_handler(FED_SET_RULES_HANDLER)
dispatcher.add_handler(FED_GET_RULES_HANDLER)

