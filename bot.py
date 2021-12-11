import discord # pip install -U discord.py
import os # for token secrecy

from helpers import help, randomquote, oraclequote, submitquote, aboutquote, unsubmit, deletequote, batchimport
from cs50 import SQL 
db = SQL("sqlite:///quotebot.db")

# cs50 must be using the logging python module 
# because including the `from cs50 import SQL` statement
# makes discord debug info clog the terminal :(
import logging
logger = logging.getLogger('discord')
# please shut up
logger.setLevel(logging.WARNING)

# give me rights to look at the guild member lists
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

PREFIX = "!"

COMMANDS = {
    'help'      : help,
    'q'         : randomquote,
    'o'         : oraclequote,
    's'         : submitquote,
    'submit'    : submitquote,
    'a'         : aboutquote,
    'about'     : aboutquote,
    'unsubmit'  : unsubmit,
    'del'       : deletequote,
    'delete'    : deletequote
}

ASYNCCOMMANDS = {
    'bi' : batchimport
}

# make sure bot token is set
if not os.environ.get("TOKEN"):
    raise RuntimeError("TOKEN not set. Run $ export TOKEN=value")


@client.event
async def on_ready():
    # create the quotes table. contains primary key id, guild-id to store which server it came from, time, who submitted it, the quote, and the flavor text ("this is the quote" -this is the flavor)
    db.execute("CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, submitter TEXT, quote TEXT NOT NULL, flavor TEXT NOT NULL)")
    # create the oracles table. contains references to quotes and their oracle type - aka what sort of question they would be relevant to answer, nouns, or verbs
    db.execute("CREATE TABLE IF NOT EXISTS oracles (quote_id INTEGER, oracletype TEXT NOT NULL, FOREIGN KEY(quote_id) REFERENCES quotes(id))")
    # make indexes for faster searching
    db.execute("CREATE INDEX IF NOT EXISTS idx_quotes ON quotes(quote, flavor)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_oracles ON oracles(oracletype)")
    # :)
    print("Databases exist. Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    # command handling
    if message.content.startswith(PREFIX):
        # get the first word after the prefix
        command = message.content[len(PREFIX):].lower().split()[0]
        # if that first word is a valid command,
        if command in COMMANDS:
            # run the command and send the response
            handler = COMMANDS[command]
            response = handler(message)
            await message.channel.send(response)
        elif command in ASYNCCOMMANDS:
            handler = ASYNCCOMMANDS[command]
            response = await handler(message)
            await message.channel.send(response)

# go quotebot go!
client.run(os.environ.get("TOKEN"))