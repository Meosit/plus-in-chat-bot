import datetime
import os
import re

import main
import messages
import store

CREATOR_ID = os.getenv("CREATOR_ID")


def trigger_by_prefix(chat, user, payload, reply_to_message):
    if chat["type"] in ("group", "supergroup"):
        group_id = chat["id"]
        if str(user["id"]) == CREATOR_ID or main.telegram_chat_role(chat["id"], user["id"]) == "creator":
            group = store.get_group_or_new(group_id, chat["title"])
            group["trigger_by_prefix"] = not group["trigger_by_prefix"]
            store.set_group(group_id, group)
            main.telegram_send_text(group_id, "Updated")


def help_command(chat, user, payload, reply_to_message):
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


def weight(chat, user, payload, reply_to_message):
    chat_id = str(chat["id"])
    if chat["type"] == "private":
        main.telegram_send_text(chat_id, messages.HELP_USER)
        return

    user_id = str(user["id"])
    payload = payload.strip().replace(" ", "").replace(",", ".")
    if payload == "":
        main.telegram_send_text(chat_id, "Weight is not provided")
    elif re.fullmatch(r"\d+(\.\d+)?", payload):
        weight_payload = round(float(payload), 1)
        group = store.get_group_or_new(chat_id, chat["title"])
        user_name = f"{user['first_name']} {str(user.get('last_name', '') or '')}".strip()
        user_username = user.get('username', None)
        now = datetime.datetime.now()
        now_string = now.strftime("%Y-%m-%d %H:%M:%S")
        rating_changed_timedelta = datetime.timedelta(seconds=group["rating_change_timeout"])
        user = group["users"].get(user_id, {
            "name": user_name.strip(),
            "username": user_username,
            "actions": 0,
            "last_action": (now - rating_changed_timedelta).strftime("%Y-%m-%d %H:%M:%S"),
            "rating": 0,
            "rating_changed": now_string,
            "weights": []
        })
        user["weights"] = [] if "weights" not in user else user["weights"]
        if (now - datetime.datetime.fromisoformat(user["last_action"])) >= rating_changed_timedelta:
            user["name"] = user_name
            user["username"] = user_username
            user["last_action"] = now_string
            user["weights"].insert(0, {"d": now_string, "v": weight_payload})
            if len(user["weights"]) >= 20:
                user["weights"].pop()
            message = user_weight_message(user)
            group["users"][user_id] = user
            store.set_group(chat_id, group)
            main.telegram_send_text(chat_id, f"Saved: {message}")
    else:
        main.telegram_send_text(chat_id, "Weight is not provided")


def user_weight_message(user):
    current_weight_object = user["weights"][0]
    current_datetime = datetime.datetime.strptime(current_weight_object["d"], "%Y-%m-%d %H:%M:%S")
    current_weight = current_weight_object["v"]
    previous_weight_object = user["weights"][1] if len(user["weights"]) >= 2 else None
    if previous_weight_object is not None:
        previous_datetime = datetime.datetime.strptime(previous_weight_object["d"], "%Y-%m-%d %H:%M:%S")
        previous_weight = previous_weight_object["v"]
        after = (current_datetime.date() - previous_datetime.date()).days
        delta = current_weight - previous_weight
        delta_text = '{:+.1f}'.format(delta)
        icon = "🌭" if delta > 0 else "💪"
        delta_label = f"({icon} `{delta_text}` in {after}d)"
    else:
        delta_label = f""
    message = f"*{main.escape_markdown(user['name'])}* ⚖️ `{current_weight}` {delta_label}"
    return message


def weight_rating(chat, user, payload, reply_to_message):
    chat_id = str(chat["id"])
    if chat["type"] in ("group", "supergroup"):
        group = store.get_group_or_new(chat_id, chat["title"])
        weights = list(map(lambda u: user_weight_message(u), filter(lambda u: "weights" in u and len(u["weights"]) > 0, group["users"].values())))
        list_rating = "No one have any weight" if len(weights) == 0 \
            else "\n".join(f"- {it}"
                           for it in weights)
        message = messages.WEIGHT_GROUP\
            .replace("[name]", main.escape_markdown(chat["title"]))\
            .replace("[date]", datetime.datetime.now().strftime("%Y-%m-%d"))\
            .replace("[list]", list_rating)
        if reply_to_message is not None and reply_to_message["from"]["is_bot"] \
                and reply_to_message["text"].startswith(messages.WEIGHT_GROUP_PREFIX) \
                and (str(user["id"]) == CREATOR_ID or main.telegram_chat_role(chat_id, user["id"]) == "creator"):
            main.telegram_update_text(chat_id, reply_to_message["message_id"], message)
        else:
            main.telegram_send_text(chat_id, message)


def rating(chat, user, payload, reply_to_message):
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


def set_decrease_trigger(chat, user, payload, reply_to_message):
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


def set_increase_trigger(chat, user, payload, reply_to_message):
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


def timeout(chat, user, payload, reply_to_message):
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


def empty_handler(chat, user, payload, reply_to_message):
    print("No handler for this command")


HANDLERS = {
    "/trigger_by_prefix": trigger_by_prefix,
    "/start": help_command,
    "/help": help_command,
    "/rating": rating,
    "/timeout": timeout,
    "/weight": weight,
    "/weight_rating": weight_rating,
    "/set_increase_trigger": set_increase_trigger,
    "/set_decrease_trigger": set_decrease_trigger,
}


def from_command(command):
    return HANDLERS.get(command.split("@")[0], empty_handler)
