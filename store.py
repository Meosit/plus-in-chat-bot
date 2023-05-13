from google.cloud import firestore

db = firestore.Client()
collection_id = "plusinchatbot-groups"


def delete_group(group_id):
    db.collection(collection_id).document(str(group_id)).delete()


def get_group_or_new(group_id, title):
    snapshot = db.collection(collection_id).document(str(group_id)).get()
    if snapshot.exists:
        return snapshot.to_dict()
    else:
        new = {
            "id": group_id,
            "name": title,
            "rating_change_timeout": 10,
            "trigger_by_prefix": True,
            "increase_triggers": ["+", "plus", "плюс", "thanks", "based", "спасибо", "база", "проорал", "ору"],
            "decrease_triggers": ["-", "minus", "минус", "кринж", "cringe"],
            "users": {}
        }
        db.collection(collection_id).document(group_id).set(new)
        return new


def set_group(group_id, group):
    db.collection(collection_id).document(str(group_id)).set(group)