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
# - save stats only if new messages detected (in case privacy is set off) - is it worth it ?
# - get gentlemanboners
# - remember/forget/getlink

start_time = time.time()
with open("log.txt", mode='w') as f:  # delete previous log file - TODO: rename log file ?
    pass


def get_uptime():
    sec = datetime.timedelta(seconds=int((time.time() - start_time)))
    d = datetime.datetime(1, 1, 1) + sec
    return d


def log(message):
    d = get_uptime()
    string = ("[%d:%02d:%02d:%02d] - " % (d.day-1, d.hour, d.minute, d.second))+str(message)
    print(string)
    with open("log.txt", mode='a') as file:
        file.write(string+'\n')


def log_exception(message):
    log("EXCEPTION! - "+str(message))

log("AeB - Bot - v0.1 - https://github.com/adisuciu/AeB-Telegram-Bot")
log("initializing ...")

botQueryURL = settings.botQueryURL
updateFrequency = settings.updateFrequency

updateID = 0
getMe = "getMe"
getUpdates = "getUpdates"
sendMessage = "sendMessage"
urlParserSafeChars = '/:&?=\\'
botprefix = '/'
bot_id = 0
chat_id = 0
no_data_cnt = 0
save_stats_cnt = 0
Chats = {}  # dictionary {chat_id : {user_id : UserStat}}


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
            return True
        else:
            log("Unhandled exception: no result found on getMe method.")
            return False
    else:
        log("Bot not identified, aborting")
        return False


def build_update_url(update_id):
    return urllib.parse.quote_plus(botQueryURL+getUpdates+"?offset="+update_id, urlParserSafeChars)


def build_sendmessage_url(message):
    return urllib.parse.quote_plus(botQueryURL+sendMessage+"?chat_id="+str(chat_id)+'&text='+message,
                                   urlParserSafeChars)


def build_getme_url():
    return urllib.parse.quote_plus(botQueryURL+getMe, urlParserSafeChars)


def get_update():
    pass


def send_http_query(query):
    result_qry = ""
    try:
        result_qry = urllib.request.urlopen(query).read()
    except:  # urllib.error.HTTPError:
        log_exception("request query - " + query)
        if result_qry:
            log_exception("response query - " + str(result_qry))
        else:
            log_exception("no response query")
        log_exception(str(sys.exc_info()))
    return result_qry


def send_message(message):
    http_qry = build_sendmessage_url(message)
    send_http_query(http_qry)


def build_help():
    return "/help - this help\n" \
           "/about - about this bot\n"\
           "/bug_quote - requests random BUG MAFIA quote\n" \
           "/list_users - lists active users of this chat\n" \
           "/chat_stats - lists statistics for the active users of this chat\n"\
           "/uptime - shows the uptime of the bot"


def build_bug_quote():
    with open(settings.quote_src) as file:
        content = file.readlines()
    file.close()
    string = content[random.randint(0, len(content)-1)]  # return random string from file
    decoded_string = bytes(string, "utf-8").decode("unicode_escape")  # parse escape sequences such as \n
    return decoded_string


def build_stats():
    string = "Chat activity statistics are:\n"
    if not Chats[chat_id]:
        return "No stats for this chat"
    for user in Chats[chat_id]:
        username = Chats[chat_id][user].get_user()[0]
        name = (Chats[chat_id][user].get_user()[1] + " " + (Chats[chat_id][user].get_user()[2]))
        namestring = username if username else name
        number_of_msg = Chats[chat_id][user].get_msgcount()
        number_of_min = Chats[chat_id][user].get_timecount()

        string += (namestring + " - " + str(number_of_msg) + " messages in " + str(number_of_min) + " minutes ")+"\n"
    return string
    pass


def list_users():
    string = "This channel's active users are:\n"
    for user, attributes in Chats[chat_id].items():
        username = (Chats[chat_id][user].get_user()[0])
        name = (Chats[chat_id][user].get_user()[1] + " " + (Chats[chat_id][user].get_user()[2]))
        namestring = username if username else name

        string += namestring + "\n"
    return string


def build_about():
    return settings.about_message


def build_uptime():
    d = get_uptime()
    return "Uptime: %d days, %02d:%02d:%02d " % (d.day-1, d.hour, d.minute, d.second)


def dummy():
    return False


def process(update):
    request = str(update['message']['text']) if 'text' in update['message'] else "$$"
    global chat_id
    chat_id = update['message']['chat']['id']
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
        switcher = {
            "": dummy,
            "help": build_help,
            "bug_quote": build_bug_quote,
            "chat_stats": build_stats,
            "about": build_about,
            "uptime": build_uptime,
            "list_users": list_users,
            "save_stats": save_stats
        }
        response = switcher[request]() if request in switcher else False
        log("Request - " + str(request))
        log("Response - " + str(response))
        if response:
            send_message(response)


def init_stats():
    if not os.path.isfile("stats.txt"):
        return  # file does not exist

    with open("stats.txt") as file:
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


def save_stats():
    output = json.dumps(Chats, cls=JSONChatStatEncoder)
    with open("stats.txt", mode='w') as file:
        file.write(output)
    file.close()
    log("Stats saved")
    pass


log("getMe() - verifies HTTPS connectivity to Telegram API")
response_query = send_http_query(build_getme_url())
log("parsing received JSON")
jsonData = json.loads(response_query.decode('utf-8'))

if not init_bot(jsonData):  # init unsuccessful
    sys.exit(0)  # bot program will now quit

log("bot initialization successful")
shutdown = False
random.seed()  # init random number generator
init_stats()

while not shutdown:
    # getUpdates from server
    response_query = send_http_query(build_update_url(str(updateID)))
    jsonData = json.loads(response_query.decode('utf-8'))
    if jsonData['ok']:
        if jsonData['result']:
            for http_update in jsonData['result']:
                # process updates
                process(http_update)
                updateID = http_update['update_id']+1
        else:
            if no_data_cnt < 30:  # every 30 seconds
                no_data_cnt += 1
            else:
                no_data_cnt = 0
                log("No data to parse")
    else:
        log("Unhandled exception. JSON 'ok' field false. Exiting ")
        shutdown = True

    if save_stats_cnt < 300:  # every 5 minutes
        save_stats_cnt += 1
    else:
        save_stats_cnt = 0
        save_stats()

    time.sleep(updateFrequency)
