# Hi! Welcome to Quotebot's README.

To run Quotebot, you'll need a few things. 

## Discord account

It's a Discord bot, so you'll need a Discord account and a server that you have Manage Server privileges on. See [discord.com](https://discord.com/) to create an [account](https://support.discord.com/hc/en-us/articles/360033931551) and a [server](https://support.discord.com/hc/en-us/articles/204849977), if you don't already have one. 

## Bot setup

Once you have a Discord account setup, head over to the [Discord developer portal](https://discord.com/developers/applications/). Click *New Application* in the top right corner, and name it Quotebot. On the sidebar, navigate to Bot and click Add Bot. Scroll down and toggle *Server Member Intent* to on and *Message Content Intent* to on.

On the sidebar, navigate to OAuth2 -> URL Generator. Check *Bot*, then in the next menu, check *Read Messages/View Channels*, *Send Messages*, *Embed Links*, and *Attach Files*. Copy the link at the bottom of the page and open it. Make sure you're signed in and select the server you want to add Quotebot to. Verify you're a human, and bam! bot added!

Go back to the developer portal and navigate to Bot on the sidebar. Copy the bot's unique token with the blue *Copy* button. You'll need that in the code environment!

[Here's a nice article](https://discordpy.readthedocs.io/en/stable/discord.html) that explains adding a bot alongside helpful pictures.

## Running the code

Navigate back to the CS50IDE. Run $export TOKEN=value where value is the bot's token you copied earlier. Next, there's some packages to install. Navigate to the quotebot directory and run:

> $ pip install -U discord.py
> $ pip install -U nltk
> $ pip install -U textblob

In the quotebot directory, run $ python3 bot.py to start the bot.

It may take a few seconds, but there we go! If everything went as expected, quotebot is now in your server. :) To quote every pset, "If you run into any trouble, follow these same steps again and see if you can determine where you went wrong!" or yknow, email me.

## Using Quotebot

Get an overview of the options by sending !help in your discord server. You'll probably want to start by submitting some quotes - if you have quotes in mind, you can use those, or you can download the samplequotes.txt file included in the repository. (fun fact: these sample quotes come from my friends' quote collections, with names changed). You can batch import these quotes by sending !bi and attaching samplequotes.txt.

Now that you've got some quotes in there, query for random quotes with !q. You can also use !o followed by a question/prompt and you'll get a related quote if there is one. For example, *!o is it nap time yet?* or *!o sandwich or soup* or *!o how is my math test going to go* are all the types of things you could prompt Quotebot with. See the other available commands with !help, or they're listed right below.

## Commands
| Command | Result |
| --- | --- |
| !q | gives a random quote |
| !o \[question\] | gives an oracle'd quote. i'll try to give you something relevant! |
| !submit "quote" -author | submits a quote. (!s also works) |
| !unsubmit | removes the last-submitted quote |
| !delete | when in reply to a quote, deletes that quote (!del also works) |
| !about | when in reply to a quote, tells you who submitted the quote and when in UTC time (!a also works) |
| !bi | batch imports an attached plaintext file of quotes. warning: this sends a lot of messages. |
| !help | gives you this menu! |
