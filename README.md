# Plus In Chat Bot

This is a simple telegram bot which allows counting user statistics within specific group based on message replies.
As an additional feature, allows to track and share body weight within the group.
Not supposed to run in large groups

## Deployment

This bot is designed for [GCP Cloud Functions](https://cloud.google.com/functions) as execution environment and with
[GCP Firestore](https://cloud.google.com/firestore) as storage for user statistics.

### Cloud function requirements:

* Runtime: `Python 3.10`
* Allow unauthenticated access
* Memory: `128M`

```shell
gcloud functions deploy plusinchatbot-handle --runtime python310 --trigger-http --region europe-central2 --entry-point main --env-vars-file .env.yaml --memory 128Mi --gen2 --allow-unauthenticated
```


### Environment variables required:

* `CREATOR_ID`: id of the person who will have superuser permissions and will receive error notification in case something happened on backend
* `BOT_TOKEN`: Telegram bot token which will be used for sending messages

### Bot Prerequisites:

* Bot should Allow Groups
* [Privacy mode](https://core.telegram.org/bots/features#privacy-mode) must be **disabled**
* Update fields to listen: `["message", "my_chat_member"]`


### Setting Webhook
```shell
curl -X "POST" "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d '{"drop_pending_updates": true, "url": "<Function URL>", "allowed_updates": ["message", "my_chat_member"]}' \
  -H 'Content-Type: application/json; charset=utf-8'
```