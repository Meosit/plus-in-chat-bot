import os

import main
import messages
import store

CREATOR_ID = os.getenv("CREATOR_ID")


def trigger_by_prefix(chat, user, payload):
    if chat["type"] in ("group", "supergroup"):
        group_id = chat["id"]
        if str(user["id"]) == CREATOR_ID or main.telegram_chat_role(chat["id"], user["id"]) == "creator":
            group = store.get_group_or_new(group_id, chat["title"])
            group["trigger_by_prefix"] = not group["trigger_by_prefix"]
            store.set_group(group_id, group)
            main.telegram_send_text(group_id, "Updated")


def help_command(chat, user, payload):
    chat_id = str(chat["id"])
    if chat["type"] in ("group", "supergroup"):
        group = store.get_group_or_new(chat_id, chat["title"])
        message = messages.HELP_GROUP\
            .replace("[mode]", "be started with" if group["trigger_by_prefix"] else "be equal to")\
            .replace("[trigger_by_prefix]", "enabled" if group["trigger_by_prefix"] else "disabled")\
            .replace("[increase]", ", ".join(group["increase_triggers"]))\
            .replace("[decrease]", ", ".join(group["decrease_triggers"]))\
            .replace("[timeout]", str(group["rating_change_timeout"]))
        main.telegram_send_text(chat_id, message)
    elif chat["type"] == "private":
        main.telegram_send_text(chat_id, messages.HELP_USER)


def rating(chat, user, payload):
    chat_id = str(chat["id"])
    if chat["type"] in ("group", "supergroup"):
        group = store.get_group_or_new(chat_id, chat["title"])
        top = sorted(group["users"].values(), key=lambda x: x['rating'], reverse=True)[:10]
        list_rating = "No one have any rating" if len(top) == 0 \
            else "\n".join(f"- *{main.escape_markdown(it['name'] + ('' if it.get('username', None) is None else (' (' + it['username'] + ')')))}* (rating: {it['rating']}, actions: {it['actions']})"
                           for it in top)
        message = messages.TOP_GROUP\
            .replace("[name]", main.escape_markdown(chat["title"]))\
            .replace("[list]", list_rating)
        main.telegram_send_text(chat_id, message)


def set_decrease_trigger(chat, user, payload):
    group_id = chat["id"]
    if chat["type"] in ("group", "supergroup") and (str(user["id"]) == CREATOR_ID or main.telegram_chat_role(group_id, user["id"]) == "creator"):
        payload = payload.strip().lower().replace("*", "").replace("\\", "").replace("[", "").replace("`", "")
        if payload == "":
            main.telegram_send_text(group_id, "Trigger text is not provided")
        elif 1 <= len(payload) <= 30:
            group = store.get_group_or_new(group_id, chat["title"])
            group["decrease_triggers"] = [trigger for trigger in group["decrease_triggers"] if trigger != payload] \
                if payload in group["decrease_triggers"] else [payload, *group["decrease_triggers"]]
            if len(group["decrease_triggers"]) <= 30:
                store.set_group(group_id, group)
                main.telegram_send_text(group_id, "Updated")
                print(f"Added {payload} to group {group['name']} ({group_id})")
            else:
                main.telegram_send_text(group_id, "Updated")
        else:
            main.telegram_send_text(group_id, "Trigger text cannot be more than 30 symbols")


def set_increase_trigger(chat, user, payload):
    group_id = chat["id"]
    if chat["type"] in ("group", "supergroup") and (str(user["id"]) == CREATOR_ID or main.telegram_chat_role(group_id, user["id"]) == "creator"):
        payload = payload.strip().lower().replace("*", "").replace("\\", "").replace("[", "").replace("`", "")
        if payload == "":
            main.telegram_send_text(group_id, "Trigger text is not provided")
        elif 1 <= len(payload) <= 30:
            group = store.get_group_or_new(group_id, chat["title"])
            group["increase_triggers"] = [trigger for trigger in group["increase_triggers"] if trigger != payload] \
                if payload in group["increase_triggers"] else [payload, *group["increase_triggers"]]
            if len(group["increase_triggers"]) <= 30:
                store.set_group(group_id, group)
                main.telegram_send_text(group_id, "Updated")
                print(f"Added increase trigger '{payload}' to group {group['name']} ({group_id})")
            else:
                main.telegram_send_text(group_id, "Updated")
        else:
            main.telegram_send_text(group_id, "Trigger text cannot be more than 30 symbols")


def timeout(chat, user, payload):
    group_id = chat["id"]
    if chat["type"] in ("group", "supergroup") and (str(user["id"]) == CREATOR_ID or main.telegram_chat_role(group_id, user["id"]) == "creator"):
        value = int(payload.strip()) if payload.strip().isdigit() else None
        if value is None:
            main.telegram_send_text(group_id, "Integer timeout should be provided")
        elif 3 <= value <= 3600:
            group = store.get_group_or_new(group_id, chat["title"])
            group["rating_change_timeout"] = value
            store.set_group(group_id, group)
            main.telegram_send_text(group_id, "Updated")
        else:
            main.telegram_send_text(group_id, "Timeout must be between 3 and 3600")


def empty_handler(chat, user, payload):
    print("No handler for this command")


HANDLERS = {
    "/trigger_by_prefix": trigger_by_prefix,
    "/start": help_command,
    "/help": help_command,
    "/rating": rating,
    "/timeout": timeout,
    "/set_increase_trigger": set_increase_trigger,
    "/set_decrease_trigger": set_decrease_trigger,
}


def from_command(command):
    return HANDLERS.get(command.split("@")[0], empty_handler)
