
TOP_GROUP = """Top for group *[name]*:\n[list]"""
WEIGHT_GROUP = f"""Weight for group *[name]* on [date]:\n\n[list]"""

HELP_GROUP = """This bot allows to count rating of people within a group.

To increase rating, message should [mode]: [increase]
To decrease rating, message should [mode]: [decrease]

Commands for everyone:
/help - show this help
/rating - Show top 10 users with highest rating
/height <value> - Record current height, used for BMI calculation only 
/weight <value> - Record current weight, if this a reply to existing /weight\\_rating message, then it will be updated as well 
/weight\\_init <value> - Record current weight history and set the beginning of the new path  
/weight\\_rating - Show current weights of group users
/weight\\_status - Show current weight status of all users

Commands for group creator:
/trigger\\_by\\_prefix - toggle trigger rating change by start of the message instead of full equality, currently is *[trigger_by_prefix]*
/timeout `<timeout>` - set timeout seconds between user actions (how fast it can change rating for others), currently is *[timeout]* seconds
/set\\_increase\\_trigger `<text>` - add or remove word which will increase user rating
/set\\_decrease\\_trigger `<text>` - add or remove word which will decrease user rating"""

HELP_USER = """This bot allows to count rating of people within a group.
It's not supposed to be used in private chats."""
