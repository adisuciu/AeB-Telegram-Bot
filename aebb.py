import urllib.request
import urllib.parse
import json
import sys
import time
import datetime
import random
import os
import settings

# TODO:
# - on the fly meme gen
# - google image search (to replace imgbot)
# - implement daily stats
# - break code down in modules

start_time = time.time()
with open(settings.log_file, mode='w') as f:  # delete previous file
    pass


def get_uptime():
    sec = datetime.timedelta(seconds=int((time.time() - start_time)))
    d = datetime.datetime(1, 1, 1) + sec
    return d


def log(message):
    d = get_uptime()
    string = ("[%d:%02d:%02d:%02d] - " % (d.day - 1, d.hour, d.minute, d.second)) + str(message)
    print(string)
    with open(settings.log_file, mode='a') as file:
        file.write(string + '\n')


def log_exception(message):
    log("EXCEPTION! - " + str(message))


log("AeB - Bot - v0.1 - https://github.com/adisuciu/AeB-Telegram-Bot")
log("initializing ...")
log("%s log file successfully created" % settings.log_file)

botQueryURL = settings.botQueryURL
updateFrequency = settings.updateFrequency

updateID = 0
getMe = "getMe"
getUpdates = "getUpdates"
sendMessage = "sendMessage"
parameters = ""
urlParserSafeChars = '/:&?=\\'
botprefix = '/'
bot_id = 0
chat_id = 0
bot_username = ""
message_id = 0
no_data_cnt = 0
save_stats_cnt = 0
Chats = {}  # dictionary {chat_id : {user_id : UserStat}}
Links = {}
nsfw_tag = False


class UserStat:
    def __init__(self, user, msgcount=1, timecount=1, timestamp=1):
        self.msgcount = msgcount
        self.timecount = timecount
        self.lasttimestamp = timestamp
        self.user = user

    def new_message(self, timestamp):
        self.msgcount += 1
        if (timestamp - self.lasttimestamp) > 60:
            self.lasttimestamp = timestamp
            self.timecount += 1

    # getters
    def get_msgcount(self):
        return self.msgcount

    def get_timecount(self):
        return self.timecount

    def get_lasttimestamp(self):
        return self.lasttimestamp

    def get_user(self):
        return self.user


class JSONChatStatEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UserStat):
            return [o.msgcount, o.timecount, o.lasttimestamp, o.user]
        # Let the base class default method process other types or raise the TypeError,
        return json.JSONEncoder.default(self, o)


def init_bot(json_data):
    if json_data['ok']:  # if ok field is True
        if json_data['result']:  # if a result is present in the JSON list
            global bot_id
            bot_id = json_data['result']['id']
            global bot_username
            bot_username = json_data['result']['username']
            return True
        else:
            log("Unhandled exception: no result found on getMe method.")
            return False
    else:
        log("Bot not identified, aborting")
        return False


def build_update_url(update_id):
    return urllib.parse.quote_plus(botQueryURL + getUpdates + "?offset=" + update_id, urlParserSafeChars)


def build_sendmessage_url(message):
    return urllib.parse.quote_plus(botQueryURL + sendMessage
                                   + "?chat_id=" + str(chat_id)
                                   + '&text=' + message
                                   + '&disable_web_page_preview=' + str(nsfw_tag)
                                   # uncomment next line to enable reply to message
                                   # + '&reply_to_message_id='+str(message_id)
                                   , urlParserSafeChars)


def build_getme_url():
    return urllib.parse.quote_plus(botQueryURL + getMe, urlParserSafeChars)


def get_update():
    pass


def send_http_query(query):
    result_qry = ""
    # review this part
    # noinspection PyBroadException
    try:
        result_qry = urllib.request.urlopen(query).read()
    except:  # urllib.error.HTTPError:
        if type(query) == str:
            log("request query - " + query)
        else:
            log(query.full_url)
        if result_qry:
            log("response query - " + str(result_qry))
        else:
            log("no response")
        log_exception(str(sys.exc_info()))
    return result_qry


def send_message(message):
    global nsfw_tag
    http_qry = build_sendmessage_url(message)
    nsfw_tag = False
    log(http_qry)
    send_http_query(http_qry)


# noinspection PyUnusedLocal
def build_help(request=0):
    return "/help - this help\n" \
           "/about - about this bot\n" \
           "/bug_quote - requests random BUG MAFIA quote\n" \
           "/list_users - lists active users of this chat\n" \
           "/chat_stats - lists statistics for the active users of this chat\n" \
           "/uptime - shows the uptime of the bot\n"\
           "/remember <name> <phrase> - maps <phrase> to a <name>. if name contains nsfw, no preview will be shown on recall\n"\
           "/forget <name> - forgets <name> and attached <phrase>\n"\
           "/recall <name> [hide/nsfw] - recalls the <phrase> with name <name> - [hide][nsfw] - hides preview\n"\
           "/search [phrase] - search all names that begin with [phrase]. [phrase] can be empty - lists all names \n"\
           "/getpic [subreddit] - gets a random picture from the subreddit. The picture is taken from today's top 60"\
    #       "/memegen <meme> '<top>' '<bottom>' - on the fly meme generator"


# noinspection PyUnusedLocal
def build_bug_quote(request=0):
    with open(settings.quote_file) as file:
        content = file.readlines()
    file.close()
    string = content[random.randint(0, len(content) - 1)]  # return random string from file
    decoded_string = bytes(string, "utf-8").decode("unicode_escape")  # parse escape sequences such as \n
    return decoded_string


# noinspection PyUnusedLocal
def build_stats(request=0):
    string = "Chat activity statistics are:\n"
    if not Chats[chat_id]:
        return "No stats for this chat"
    for user in Chats[chat_id]:
        username = Chats[chat_id][user].get_user()[0]
        name = (Chats[chat_id][user].get_user()[1] + " " + (Chats[chat_id][user].get_user()[2]))
        namestring = username if username else name
        number_of_msg = Chats[chat_id][user].get_msgcount()
        number_of_min = Chats[chat_id][user].get_timecount()

        string += (namestring + " - " + str(number_of_msg) + " messages in " + str(number_of_min) + " minutes ") + "\n"
    return string
    pass


# noinspection PyUnusedLocal
def list_users(request=0):
    string = "This channel's active users are:\n"
    for user, attributes in Chats[chat_id].items():
        username = (Chats[chat_id][user].get_user()[0])
        name = (Chats[chat_id][user].get_user()[1] + " " + (Chats[chat_id][user].get_user()[2]))
        namestring = username if username else name

        string += namestring + "\n"
    return string


# noinspection PyUnusedLocal
def build_about(request=0):
    return settings.about_message


# noinspection PyUnusedLocal
def build_uptime(request=0):
    d = get_uptime()
    return "Uptime: %d days, %02d:%02d:%02d " % (d.day - 1, d.hour, d.minute, d.second)


# noinspection PyUnusedLocal
def dummy(request=0):
    return False


def save_links_file():
    output = json.dumps(Links)
    with open(settings.links_file, mode="w") as file:
        file.write(output)


def load_links_file():
    if not os.path.isfile(settings.links_file):
        log("%s does not exist. No links loaded" % settings.links_file)
        return  # file does not exist

    with open(settings.links_file) as file:
        file_content = file.read()

    global Links
    Links = json.loads(file_content)
    log("Links dictionary loaded from %s" % settings.links_file)


def build_remember_link(request):
    if type(request) == list and len(request) == 3:
        if request[1] in Links:
            return "This name already exists in the database"
        else:
            Links[request[1]] = request[2]  # + ("v" if str(request[2].endswith(".gif")) else "") # can be activated
            save_links_file()
            return "'%s' remembered" % request[1]
    else:
        return "Wrong number of parameters. Usage: /remember <name> <link>"


def build_forget_link(request):
    if type(request) == list and len(request) == 2:
        if request[1] in Links:
            del Links[request[1]]
            save_links_file()
            return "'%s' forgotten" % request[1]
        else:
            return "'%s' cannot be found" % request[1]
    else:
        return "Wrong number of parameters. Usage: /forget <name>"


def find_links_startwith(sw=""):
    retval = []
    for link in Links:
        if str(link).startswith(sw):
            retval.append(link)
    return retval


# noinspection PyUnusedLocal
def build_recall_link(request):
    load_links_file()  # reload just in case - it should already be synced
    if type(request) == list and len(request) in {2, 3}:
        global nsfw_tag
        if {'nsfw', 'hide', 'NSFW'}.intersection(request):  # nsfw/hide parameter
            nsfw_tag = True

        if 'nsfw' in request[1]:  # link key contains nsfw
            nsfw_tag = True

        if request[1] in Links:
            return str(Links[request[1]])
        else:
            return "'%s' cannot be found\nDid you mean any of the following: %s" % \
                   (request[1], "'" + "', '".join(find_links_startwith(request[1])) + "'")
    else:
        return "Wrong number of parameters. Usage /recall <name> [nsfw/hide]"


# noinspection PyUnusedLocal
def build_search_link(request):
    if type(request) == list and len(request) in {1, 2}:
        load_links_file()
        string = "Currently remembered links %sare:\n" % \
                 (("that start with '%s' " % request[1]) if len(request) == 2 else "")
        string += "'" + "', '".join(find_links_startwith(request[1] if len(request) == 2 else '')) + "'"
        return string
    else:
        return "Wrong number of parameters. Usage /listlink [phrase]"


def build_imgur_pic(request):
    if type(request) == list and len(request) == 2:

        req = urllib.request.Request("https://api.imgur.com/3/gallery/r/" + request[1] + "/top/week",
                                     headers={"Authorization": ("Client-ID " + settings.imgur_api_client_id)})
        response = send_http_query(req)  # urllib.request.urlopen(req).read()
        if response_query:
            json_data = json.loads(response.decode('utf-8'))
            if json_data['data']:  # data is available
                link_id = random.randint(0, len(json_data['data']) - 1)
                retval = (str(json_data['data'][link_id]['title']) + " - "
                          + str(json_data['data'][link_id]['link'] +
                                ("v" if(str(json_data['data'][link_id]['link']).endswith(".gif")) else "")))
                return retval
            else:
                return "images in subreddit '%s' not found in the past day" % request[1]
        else:
            return "internal error. please try again."
    else:
        return "Wrong number of parameters. Usage /getpic [subreddit]"


def process(update):
    request = str(update['message']['text']) if 'text' in update['message'] else "$$"
    global chat_id
    chat_id = update['message']['chat']['id']
    global message_id
    message_id = update['message']['message_id']
    user_id = update['message']['from']['id']
    username = update['message']['from']['username'] if 'username' in update['message']['from'] else 0
    first_name = update['message']['from']['first_name'] if 'first_name' in update['message']['from'] else 0
    last_name = update['message']['from']['last_name'] if 'last_name' in update['message']['from'] else 0
    message_timestamp = update['message']['date']

    # update stats
    if chat_id in Chats:
        if user_id in Chats[chat_id]:
            Chats[chat_id][user_id].new_message(message_timestamp)
        else:
            Chats[chat_id][user_id] = UserStat([username, first_name, last_name], timestamp=message_timestamp)
    else:
        Chats[chat_id] = {user_id: UserStat([username, first_name, last_name], timestamp=message_timestamp)}

    # process received commands
    if request.startswith(botprefix):
        request = request.split(botprefix, 1)[1]

        if request:
            if "@" in request:
                target = request.split("@",1)[1].split(" ")
                if target[0] != bot_username:
                    return
                else:
                    request = request.replace("@"+bot_username, "")

            request = request.split()
        else:
            return

        switcher = {
            "": dummy,
            "help": build_help,
            "bug_quote": build_bug_quote,
            "chat_stats": build_stats,
            "about": build_about,
            "uptime": build_uptime,
            "list_users": list_users,
            "save_stats": save_stats,
            "remember": build_remember_link,
            "forget": build_forget_link,
            "recall": build_recall_link,
            "search": build_search_link,
            "getpic": build_imgur_pic
        }
        response = switcher[request[0]](request) if request[0] in switcher else False
        log("Request - " + str(request))
        log("Response - " + str(response))
        if response:
            send_message(response)


def init_stats():
    if not os.path.isfile(settings.stats_file):
        log("%s does not exist. No stats loaded" % settings.stats_file)
        return  # file does not exist

    with open(settings.stats_file) as file:
        file_content = file.read()

    if not input:
        return  # file is empty

    json_data = json.loads(file_content)
    for chat, chatusers in json_data.items():
        for user_id, userattributes in chatusers.items():
            msgcount = userattributes[0]
            timecount = userattributes[1]
            timestamp = userattributes[2]
            username = userattributes[3][0]
            first_name = userattributes[3][1]
            last_name = userattributes[3][2]
            user = [username, first_name, last_name]
            # JSON does not allow integer keys for dictionaries - therefore a conversion must be done before
            # building the dictionary => int(chat), int(user_id)
            if int(chat) in Chats:
                Chats[int(chat)][int(user_id)] = UserStat(user, msgcount, timecount, timestamp)
            else:
                Chats[int(chat)] = {int(user_id): UserStat(user, msgcount, timecount, timestamp)}
    log("Chat statistics loaded from %s" % settings.stats_file)


# noinspection PyUnusedLocal
def save_stats(request=0):
    output = json.dumps(Chats, cls=JSONChatStatEncoder)
    with open(settings.stats_file, mode='w') as file:
        file.write(output)
    log("Stats saved")
    pass


log("getMe() - verifies HTTPS connectivity to Telegram API")
response_query = send_http_query(build_getme_url())
log("parsing received JSON")
jsonData = json.loads(response_query.decode('utf-8'))

if not init_bot(jsonData):  # init unsuccessful
    sys.exit(0)  # bot program will now quit

shutdown = False
random.seed()  # init random number generator
init_stats()
load_links_file()
log("bot initialization successful")
log("bot is now listening")

while not shutdown:
    # getUpdates from server
    response_query = send_http_query(build_update_url(str(updateID)))
    if response_query:
        jsonData = json.loads(response_query.decode('utf-8'))
    else:
        time.sleep(updateFrequency)
        continue  # request new http query

    if jsonData['ok']:
        if jsonData['result']:
            for http_update in jsonData['result']:
                # process updates
                process(http_update)
                updateID = http_update['update_id'] + 1
        else:
            if no_data_cnt < 30:  # every 30 seconds
                no_data_cnt += 1
            else:
                no_data_cnt = 0
                log("No data to parse")
    else:
        log("JSON 'ok' field false ")

    if save_stats_cnt < 300:  # every 5 minutes
        save_stats_cnt += 1
    else:
        save_stats_cnt = 0
        save_stats()

    time.sleep(updateFrequency)
