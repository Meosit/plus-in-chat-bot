import datetime
import os
import sys
import traceback
import requests

import handlers
import store

TOKEN = os.getenv("BOT_TOKEN")
CREATOR_ID = os.getenv("CREATOR_ID")
if TOKEN is None or CREATOR_ID is None:
    raise Exception("Expected BOT_TOKEN and CREATOR_ID envs")


def main(request):
    try:
        update = request.get_json(force=True, cache=False)
    except:
        log_error_with_notification("Failed to parse request")
        return "OK", 200
    try:
        if "message" in update and "text" in update["message"] and "from" in update["message"]:
            message = update["message"]
            text = message["text"]
            user = message["from"]
            chat = message["chat"]
            entities = message["entities"] if "entities" in message else None
            command_entity = None if entities is None else first_or_none(entities, lambda item: item["type"] == "bot_command")
            if command_entity is not None:
                command = text[command_entity["offset"]:command_entity["offset"] + command_entity["length"]]
                print(f"Handling '{command}' command for ${chat['id']}")
                handler = handlers.from_command(command)
                handler(chat, user, text.lstrip(command), message.get("reply_to_message", None))
            elif "reply_to_message" in message \
                    and chat["type"] in ("group", "supergroup") \
                    and message["reply_to_message"]["from"]["id"] != user["id"] \
                    and not message["reply_to_message"]["from"]["is_bot"] and not user["is_bot"]:
                group_id = chat["id"]
                group = store.get_group_or_new(group_id, chat["title"])
                group["name"] = chat["title"]
                predicate = (lambda a: text.lower().startswith(a.lower())) \
                    if group["trigger_by_prefix"] else (lambda a: text.lower() == a.lower())
                target_user = message["reply_to_message"]["from"]
                action_user = user
                rating_delta = 0
                if first_or_none(group["increase_triggers"], predicate) is not None:
                    rating_delta = 1
                elif first_or_none(group["decrease_triggers"], predicate) is not None:
                    rating_delta = -1
                if rating_delta != 0:
                    now = datetime.datetime.now()
                    rating_changed_timedelta = datetime.timedelta(seconds=group["rating_change_timeout"])
                    action_id = str(action_user["id"])
                    action_name = f"{action_user['first_name']} {str(action_user.get('last_name', '') or '')}".strip()
                    action_username = action_user.get('username', None)
                    now_string = now.strftime("%Y-%m-%d %H:%M:%S")
                    action_person = group["users"].get(action_id, {
                        "name": action_name,
                        "username": action_username,
                        "actions": 0,
                        "last_action": (now - rating_changed_timedelta).strftime("%Y-%m-%d %H:%M:%S"),
                        "rating": 0,
                        "rating_changed": now_string,
                        "weights": [],
                    })
                    target_id = str(target_user["id"])
                    target_name = f"{target_user['first_name']} {str(target_user.get('last_name', '') or '')}".strip()
                    target_username = target_user.get('username', None)
                    target_person = group["users"].get(target_id, {
                        "name": target_name,
                        "username": target_username,
                        "actions": 0,
                        "last_action": now_string,
                        "rating": 0,
                        "rating_changed": now_string,
                        "weights": [],
                    })
                    if (now - datetime.datetime.fromisoformat(action_person["last_action"])) >= rating_changed_timedelta:
                        action_person["actions"] = action_person["actions"] + 1
                        action_person["last_action"] = now_string
                        action_person["name"] = action_name
                        action_person["username"] = action_username
                        target_person["rating"] = target_person["rating"] + rating_delta
                        target_person["rating_changed"] = now_string
                        target_person["name"] = target_name
                        target_person["username"] = target_username
                        group["users"][action_id] = action_person
                        group["users"][target_id] = target_person
                        store.set_group(group_id, group)
                        label = "\uD83D\uDFE2⤴️" if rating_delta > 0 else "\uD83D\uDD34⤵️"
                        telegram_send_text(chat["id"], f"{escape_markdown(action_name)} ({action_person['rating']}) {label} {escape_markdown(target_name)} ({target_person['rating']})")
        elif "my_chat_member" in update \
                and update["my_chat_member"]["chat"]["type"] in ("group", "supergroup") \
                and update["my_chat_member"]["new_chat_member"]["status"] in ("left", "kicked"):
            store.delete_group(update["my_chat_member"]["chat"]["id"])
    except:
        log_error_with_notification("Failed to handle request")
    return "OK", 200


def first_or_none(items, condition):
    for item in items:
        if condition(item):
            return item
    return None


def log_error_with_notification(message):
    exc = traceback.format_exc()
    print(exc.replace("\n", " "), file=sys.stderr)
    try:
        telegram_send_text(int(CREATOR_ID), f"{message}\n```{trim_to_max_length(escape_markdown(exc))}```")
    except:
        exc = traceback.format_exc().replace("\n", " ")
        print(f"Failed to notify creator: {exc}", file=sys.stderr)


def trim_to_max_length(string):
    return (string[:4070] + "... (Too long message)") if len(string) > 4096 else string


def escape_markdown(string):
    return string.replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")


def telegram_send_text(user_id, markdown):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": int(user_id), "parse_mode": "Markdown", "text": trim_to_max_length(markdown)}
    requests.post(url, json=data)


def telegram_update_text(user_id, message_id, markdown):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {"chat_id": int(user_id), "message_id": int(message_id), "parse_mode": "Markdown", "text": trim_to_max_length(markdown)}
    requests.post(url, json=data)


def telegram_chat_role(chat_id, user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
    data = {'chat_id': int(chat_id), 'user_id': int(user_id)}
    return requests.post(url, json=data).json()["result"]["status"]