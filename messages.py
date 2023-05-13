
TOP_GROUP = """Top for group *[name]*:\n[list]"""
WEIGHT_GROUP_PREFIX = """Weight for group"""
WEIGHT_GROUP = f"""{WEIGHT_GROUP_PREFIX} *[name]* on [date]:\n[list]"""

HELP_GROUP = """This bot allows to count rating of people within a group.

To increase rating, message should [mode]: [increase]
To decrease rating, message should [mode]: [decrease]

Commands for everyone:
/rating - Show top 10 users with highest rating
/weight <value> - Record current weight, if this a reply to existing /weight\\_rating message, then it will be updated as well 
/weight\\_rating - Show current weights of group users, if this a reply to existing /weight\\_rating message, then it will be updated instead of new one
/help - show this help

Commands for group creator:
/trigger\\_by\\_prefix - toggle trigger rating change by start of the message instead of full equality, currently is *[trigger_by_prefix]*
/timeout `<timeout>` - set timeout seconds between user actions (how fast it can change rating for others), currently is *[timeout]* seconds
/set\\_increase\\_trigger `<text>` - add or remove word which will increase user rating
/set\\_decrease\\_trigger `<text>` - add or remove word which will decrease user rating"""

HELP_USER = """This bot allows to count rating of people within a group.
It's not supposed to be used in private chats."""
