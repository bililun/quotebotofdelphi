from cs50 import SQL
db = SQL("sqlite:///quotebot.db")
import nltk # pip install -U nltk
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('wordnet', quiet=True)
from textblob import TextBlob # pip install -U textblob

# lemmas to remove because they're not very interesting
boringlemmas = {"be", "gon", "i", "u", "he", "she", "they", "have", "'s", "'ve", "'m", "'re", "get", "do", "uh"}


def randomquote(m):
    quote = db.execute("SELECT quote, flavor FROM quotes WHERE guild_id = ? ORDER BY random() LIMIT 1", m.guild.id)
    try:
        quote = quote[0]
        return quote["quote"] + quote["flavor"]
    except:
        return "uh oh, no quotes found in this server :( \nsubmit with `!s \"the quote\" -the author` to get started!"


def oraclequote(m):
    # !o [question]
    questionwords = m.content.split()[1:]
    # wherearr represents the array of search terms we're looking for matches with
    wherearr = []

    if "should" in questionwords:
        wherearr.append("high polarity")
        wherearr.append("high subjectivity")

    # make a textblob
    questionblob = getcleanblob(" ".join(questionwords))
    # add unique cool words in the prompt to wherearr
    wherearr.extend(getuniquecoolwords(questionblob))

    # format wherearr into a string for SQL: ("item", "item", "item"). start with open parenthesis
    wherestr = "(\""
    # add each lemma by joining wherearr with ", " between them
    wherestr = wherestr + "\", \"".join(wherearr)
    # close the last " and add close parenthesis
    wherestr = wherestr + "\")"

    try:
        # pick a random quote that matches something in wherestr
        # valid f-string because wherestr is guaranteed to be clean
        quote = db.execute(f"SELECT quote, flavor FROM quotes WHERE guild_id = ? AND id IN (SELECT quote_id FROM oracles WHERE oracletype IN {wherestr}) ORDER BY random() LIMIT 1", m.guild.id)
        quote = quote[0]
        return quote["quote"] + quote["flavor"]
    # on fail (didn't match anything) just give a random quote back
    except:
        return randomquote(m)


def submitquote(m):
    quoteflavor = getquoteandflavor(m.content)
    tags = []
    if quoteflavor is not None:
        submitter = m.author.id
        # check for prefix content
        try:
            submitteridx = quoteflavor["prefix"].index("submitter:")
            # take the prefix string, substring to after the index of "submitter:", then take the second word (the word after "submitter:")
            submitternick = quoteflavor["prefix"][submitteridx:].split()[1]
            submitter = m.guild.get_member_named(submitternick)
            if not submitter:
                return "couldn't find a user in this server with the (case-sensitive) name \"" + submitternick + "\", submission cancelled"
            submitter = submitter.id

        # if all that worked, put it in the quotes table
        insertedid = db.execute("INSERT INTO quotes (guild_id, submitter, quote, flavor) VALUES (?, ?, ?, ?)", m.guild.id, submitter, quoteflavor["quote"], quoteflavor["flavor"])

        # analysis for oracle-ing
        quoteblob = getcleanblob(quoteflavor["quote"] + quoteflavor["flavor"])

        # polarity represents the positive or negative-ness of the text on a scale from -1 to 1
        if abs(quoteblob.sentiment.polarity) > 0.5:
            tags.append("high polarity")
        # 0 is very objective and 1 is very subjective
        if quoteblob.sentiment.subjectivity > 0.5:
            tags.append("high subjectivity")
        
        tags.extend(getuniquecoolwords(quoteblob))

        # now put everything in oracles
        for tag in tags:
            db.execute("INSERT INTO oracles(quote_id, oracletype) VALUES (?, ?)", insertedid, tag)

        return "submitted!"
    else:
        return "couldn't submit. does the quote have quotation marks around it?"


def aboutquote(m):
    # check that the !a command is in reply and in reply to to a message from quotebot
    if m.reference is None or m.reference.resolved.author is not m.guild.me:
        return "reply to a quote that i sent with `!a` and i'll tell you about it"
    else:
        quoteflavor = getquoteandflavor(m.reference.resolved.content)
        if not quoteflavor:
            return "please respond to a message with a quote"
        try:
            quote = db.execute("SELECT timestamp, submitter FROM quotes WHERE quote = ? AND flavor = ?", quoteflavor["quote"], quoteflavor["flavor"])
            quote = quote[0]
            submitter = m.guild.get_member(int(quote['submitter']))
            if submitter is None or submitter is m.guild.me:
                return "this quote is legacy or imported and i dunno who submitted it or when it was said"
            else:
                # if they have a server nickname use that, otherwise their username
                submitter = submitter.nick or submitter.name
            return f"this quote was submitted on {quote['timestamp']} by {submitter}"
        # catches if the submitter part doesn't work
        except:
            return "sorry, something weird happened. did the quote get deleted?"


def unsubmit(m):
    # get the last quote that was submitted to this guild/server
    quote = db.execute("SELECT id, quote, flavor FROM quotes WHERE guild_id = ? ORDER BY id DESC LIMIT 1", m.guild.id)
    try:
        quote = quote[0]
        id = quote["id"]
        # delete all oracles rows that reference that quote
        # have to delete from oracles first because oracles(quote_id) references quotes(id)
        db.execute("DELETE FROM oracles WHERE quote_id = ?", id)
        # delete the quote
        db.execute("DELETE FROM quotes WHERE id = ?", id)
        return "unsubmitted " + quote["quote"] + quote["flavor"]
    except:
        return "yikes, couldn't unsubmit, sorry"


def deletequote(m):
    # check that the !e command is in reply and in reply to to a message from quotebot
    if m.reference is None or m.reference.resolved.author is not m.guild.me:
        return "reply to a quote that i sent with `!delete` and i'll delete it"
    else:
        quoteflavor = getquoteandflavor(m.reference.resolved.content)
        if not quoteflavor:
            return "please respond to a message with a quote"
        try:
            quote = db.execute("SELECT id FROM quotes WHERE quote = ? AND flavor = ?", quoteflavor["quote"], quoteflavor["flavor"])
            quote = quote[0]
            db.execute("DELETE FROM oracles WHERE quote_id = ?", quote["id"])
            db.execute("DELETE FROM quotes WHERE id = ?", quote["id"])
            return "successfully deleted `" + quoteflavor["quote"] + quoteflavor["flavor"] + "`"
        # catches if the SQL doesn't run aka the quote doesn't exist in the database
        # which only happens if the quote has already been deleted
        except:
            return "that quote is already deleted"


async def batchimport(m):
    # check that there is one plaintext utf-8 encoded attachment
    if len(m.attachments) == 1:
        if m.attachments[0].content_type == 'text/plain; charset=utf-8':
            await m.channel.send("BEGINNING BATCH IMPORT\n(pro tip: turn off your notifications!)")
            # read it
            content = await m.attachments[0].read()
            content = content.decode('utf-8')
            # for each line, send a submit command in the channel
            for line in content.split("\n"):
                await m.channel.send("!s " + line)
            return "FINISHED BATCH IMPORT"
        else:
            # if there is one attachment but it's not readable
            return "content_type is `" + m.attachments[0].content_type + "` but should be `text/plain; charset=utf-8`. make sure it's a normal .txt file"
    else:
        return "couldn't batch import. make sure you attach exactly one .txt file!" 


def getquoteandflavor(content):
    # bad angled quotation marks get sent to bad angled quotation mark jail
    # and by that i mean replace them with normal vertical ones
    content = content.replace('“', '"').replace('”', '"')

    # find the first and last index of quotation marks in the string
    try:
        firstquote = content.index('"')
        lastquote = content.rindex('"')
        # split the content into the quote, which is between the first and last quotation marks, and the flavor, which is after the last quotation mark
        quoteflavor = {
            'prefix' : content[:firstquote],
            'quote'  : content[firstquote:lastquote+1],
            'flavor' : content[lastquote+1:]
        }
        return quoteflavor
    # if there weren't quotation marks
    except:
        return None


def getuniquecoolwords(blob):
    arr = []
    for word, pos in blob.tags:
        # from the TextBlob library, nouns have a tag starting with NN and verbs with VB and adjectives with JJ
        # the lemma of a word is the "core" word. for example, "break", "breaks", "broke", "broken", and "breaking" would all .lemma to "break"
        # boringlemmas is defined way up top and is a hardcoded list of, well, boring lemmas that don't oracle very well
        if (pos.startswith("NN") or pos.startswith("VB") or pos.startswith("JJ")) and word.lemma not in arr and word.lemma not in boringlemmas:
            arr.append((word.lemma))
    return arr


def getcleanblob(string):
    # remove all non-alpha, non-space, and non-apostrophe characters (and fix bad angled apostrophes)
    # turn it into a TextBlob and return
    return TextBlob(''.join(filter(lambda c: c.isalpha() or c.isspace() or c in "\'", string.lower().replace("’", "\'"))))


def help(m):
    return """
> `!q`
gives a random quote
> `!o [question]`
gives an oracle'd quote. i'll try to give you something relevant!
> `!submit "quote" -author`
submits a quote. (`!s` also works)
> `!unsubmit`
removes the last-submitted quote
> `!delete`
when in reply to a quote, deletes that quote (`!del` also works)
> `!about`
when in reply to a quote, tells you who submitted the quote and when in UTC time (`!a` also works)
> `!bi`
batch imports an attached plaintext file of quotes. warning: this sends a lot of messages and your notifcations may go absolutely bonkers. i'd encourage doing this in a new, muted channel.
> `!help`
gives you this menu!
    """