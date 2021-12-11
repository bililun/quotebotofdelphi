# DESIGN for Quotebot

## Overarching design ideas

The Discord community has created several different libraries that allow people to more easily interact with the Discord API and make bots. Two of the most common are Discord.py and Discord.js. I chose to use the Python library because I a) I like Python more than JS and b) I wanted to use the CS50 SQL library. In outlining my codebase, I wanted to mimic the model from many of our PSETS where there's a main file and a helpers file that contains methods. 

The version of Quotebot I made several years ago used Discord.js because I didn't know Discord.py existed. Also, that version just kind of sucked, in general. Aside from crashing all the time, I was using .txt files for text storage and did not think about maintanability whatsoever. So doing better than that version wasn't particularly difficult, but the additional features of SQLite3 database storage and oracle language processing was a welcome challenge.

Now, on with the tour of each file:

## bot.py

First is setup: importing, configuring the SQL "db" shortcut, configuring the terminal logger, configuring discord permissions (aka "intents"), and setting a few variables. PREFIX should be self-explanatory. It's the prefix for commands intended for Quotebot. The COMMANDS and ASYNCCOMMANDS dictionaries store the links between the text of a command and the method to run. 

Discord.py calls the on_ready method once as setup. This code makes sure that the two tables, quotes and oracles, both exist and have indices for faster searching. See below for why I organized the SQL database the way I did.

Likewise, Discord.py calls the on_message function every time a message is sent, passing in a [Message object](https://discordpy.readthedocs.io/en/stable/api.html#message). This function checks for a message with content starting with the prefix and with a first word that is a valid command. If a command was sent, then it runs the method linked in the COMMANDS or ASYNCCOMMANDS dictionary and sends a message with the response.

Finally, bot.py runs the bot with the token.

## quotebot.db

Let's look at the SQL database setup. This database has two tables: quotes and oracles. 

Each row in quotes has an id, guild_id, timestamp, submitter, quote, and flavor. guild_id stores the unique Discord server ID, timestamp defaults to the current time, and submitter stores the unique Discord user ID of the person who submitted the quote. "this is the quote" -this is the flavor. Right now, this distinction isn't really used, but I prefer having more information so I've split them. Then, in the future, if I want to run statistical analysis of, say, how many quotes were said by person x, I can check just in flavor. 

Each row in oracles has a quote_id and an oracletype. quote_id is a foreign key that references the id column in the quotes table. oracletype is a catch-all text field that stores oracle-relevant information about that quote. 

For example, let's use the quote "it is, statistically speaking, more probably comfortable than the floor. i’m enjoying the floor right now." -kat. This quote's oracletype rows have "high subjectivity" (based on TextBlob analysis), "speak", "comfortable", "floor", "enjoy", and "kat". Any !o prompt that shares one or more of those oracletype rows could return this quote.

There're also indices on quotes and oracles, for speed of searching.

## helpers.py

Setup for helpers.py is mostly just importing the relevant libraries. nltk is the [Natural Language ToolKit](https://www.nltk.org/), and the three downloaded nltk modules are necessary for the TextBlob library. [Here](https://textblob.readthedocs.io/en/dev/index.html)'s the documentation for TextBlob. We'll look more in depth at how Quotebot uses TextBlob later in this file, but its basic purpose is to run text analysis and condense words to their lemmas.

boringlemmas is a set of, well, boring lemmas. They're hardcoded because it's a personal judgement of which words are not interesting enough to merit being included. Some of them are endings of words, like 's and 've, and therefore aren't actually useful; some of them are just boring like "be" because to-be verbs are everywhere and don't actually mean anything.

Next, we have the methods. We're actually going to skip to the bottom of helpers.py, because it makes more sense to explain it in this order.

### getcleanblob(string)

This method takes a string, cleans it, and returns a TextBlob object made from the string. In this case, cleaning the string means removing any characters that aren't alphabetical, a space, or an apostrophe, and replaces rich-text angled apostrophes with normal apostrophes.

### getuniquecoolwords(blob)

This method takes a TextBlob object and returns a list of cool lemmas with no duplicates. The lemma of a word is the "core" word. For example, "break", "breaks", "broke", "broken", and "breaking" all share the lemma "break". TextBlob takes the string that initialized it, splits it into words, and tags each word with a part of speech (POS). blob.tags is a list of tuples with the word and part of speech. I decided to look at nouns, verbs, and adjectives because they tend to be the interesting parts of speech.

Here's [a full list of POS tags](https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html), if you're interested. Not strictly necessary to understand the code, though. 

### getquoteandflavor(content)

This method takes the string content of a message and returns the cleaned quote and flavor. Angled quotation marks will be the death of me, so clean the content by replacing them with normal quotation marks. Then, use the index of the first and last quotation marks to separate "the quote from" -the flavor, or return none if there weren't quotation marks.

Now, back to the top for the command methods:

### randomquote

Gets a random quote from the server. Pretty simple. If there aren't any quotes available, send back an error message. Note: Discord's client-side UI and API use "server" and "guild," respectively, to refer to the same thing.

### oraclequote

A more complex way to get a quote. Oraclequote creates an array called wherearr (named because it's the WHERE SQL clause) and fills it. First, prompts with "should" get tagged with "high polarity" and "high subjectivity." Next, we add all of the unique cool words. Reformat wherearr into a string so it can go in the SQL query, and pick a quote that matches. If there is one, return that; otherwise, pick a random quote.

### submitquote

The first part of this is pretty simple - get the quote and flavor and put them into quotes. Figuring out the information that goes into the oracles table is the fun part. I'm using TextBlob again here to check the polarity (on a scale from -1.0 very negative to +1.0 very positive) and subjectivity (0.0 very objective 1.0 very subjective). Add the words from getuniquecoolwords, and then put all of that in oracles.

### aboutquote

*omg, it's more interactions with the database couched in if-statements and try-statements to protect against command miscalls!*

Perhaps that was a bit sarcastic, but it is also true. When a user replies to a quotebot message with !a or !about, this method returns information about the quote. Right now, that information is the user who submitted it and date+time that they submitted it. I decided that if the quote was batch-imported, it doesn't make much sense to say that a certain person submitted it or to make claims about when it was said, so that returns the textual equivalent of a shrug.

### unsubmit

Deletes the last quote submitted in this server. There's not that much more to it. The DELETE commands have to go in order: first delete from oracles, then from quotes. That way, the foreign key table onstraint is never violated.

### deletequote

Similarly to aboutquote, deletequote is a command that a user can send in reply to a quotebot message. In this case, instead of responding with information about that quote, it's deleted. It's basically a combination of the logic in aboutquote and unsubmit, but not quite similar enough that I thought a helper function was warranted.

### batchimport

This method takes a plaintext file attached to the commanding message and imports all of those quotes. To do so, Quotebot sends itself !s commands for each line in the attached file. I thought for a while about making the quote submission all internal. I even reworked the submitquote method and wrote a helper method so that submitquote and batchimport would both call the helper method that would do the actual quote submitting. In the end, I decided that I didn't like that method from a design standpoint. Even though this version is... a little notification-intensive, it's idealogically important to me that all of the quotes submitted to Quotebot have their submission messages actually in the Discord server.

This method is an asynchronous method because the Discord.py Attachment object's [read() method](https://discordpy.readthedocs.io/en/stable/api.html#discord.Attachment.read) is asynchronous.

### help

Built-in reminder of what the commands are. It's literally just a long string.