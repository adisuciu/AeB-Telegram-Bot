__author__ = 'adrian.suciu'

import urllib.request
import urllib.parse
import json
import sys
import time
import datetime
import random
import os
import settings
import meme
import shlex
import io
import mimetypes
import base64
from base64 import b64encode

import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

import imgur_api

# TODO:
# - google image search (to replace imgbot)

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
botprefix = '/'
bot_id = 0
chat_id = 0
bot_username = ""
message_id = 0
no_data_cnt = 0
save_stats_cnt = 0
Chats = {}  # dictionary {chat_id : {user_id : UserStat}}
SessionChats = {}
Links = {}
nsfw_tag = False
daily_stats_reset = 0
requester = ""


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
    return botQueryURL + getUpdates + "?offset=" + urllib.parse.quote_plus(update_id)


def build_sendmessage_url(message):
    return botQueryURL + sendMessage + "?chat_id=" + str(chat_id) + '&text=' + \
        urllib.parse.quote_plus(message) + '&disable_web_page_preview=' + str(nsfw_tag)
    # uncomment next line to enable reply to message
    # + '&reply_to_message_id='+str(message_id)


def build_getme_url():
    return botQueryURL + getMe


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
           "/quote <bug/ciuraru> - requests random BUG MAFIA/Ciuraru quote\n" \
           "/list_users - lists active users of this chat\n" \
           "/stats_daily - lists statistics for the active users of this chat\n" \
           "/stats_alltime - lists statistics for this chat session\n"\
           "/uptime - shows the uptime of the bot\n"\
           "/remember <name> <phrase> - maps <phrase> to a <name>. if name contains nsfw, no preview will be shown on recall\n"\
           "/forget <name> - forgets <name> and attached <phrase>\n"\
           "/recall <name> [hide/nsfw] - recalls the <phrase> with name <name> - [hide][nsfw] - hides preview\n"\
           "/search [phrase] - search all names that begin with [phrase]. [phrase] can be empty - lists all names \n"\
           "/getpic [subreddit] - gets a random picture from the subreddit. The picture is taken from today's top 60\n"\
           "/memegen <meme> '<top>' '<bottom>' - on the fly meme generator\n"\
           "/search_meme [phrase] - search all the available memes that begin with phrase\n"\
           "/imgur_status - returns the login status of the imgur account\n"


def build_quote(request):
    if len(request) == 2:
        switcher = {"bug": "bug_mafia.txt",
                    "ciuraru": "ciuraru.txt"}
        return build_quote_file(request, switcher[request[1]]) if request[1] in switcher else False


# noinspection PyUnusedLocal
def build_quote_file(request=0, quote_file="bug_mafia.txt"):
    if not quote_file:
        return "No quotes found. Usage quote <bug/ciuraru>"
    with open(quote_file) as file:
        content = file.readlines()
    string = content[random.randint(0, len(content) - 1)]  # return random string from file
    decoded_string = bytes(string, "utf-8").decode("unicode_escape")  # parse escape sequences such as \n
    return decoded_string


# noinspection PyUnusedLocal
def build_alltime_stats(request=0):
    return build_stats(request, Chats)


# noinspection PyUnusedLocal
def build_daily_stats(request=0):
    return build_stats(request, SessionChats)


# noinspection PyUnusedLocal
def build_stats(request=0, chat_var=Chats):
    string = "Chat activity statistics are:\n"
    if not chat_var[chat_id]:
        return "No stats for this chat"
    for user in chat_var[chat_id]:
        username = chat_var[chat_id][user].get_user()[0]
        name = (chat_var[chat_id][user].get_user()[1] + " " + (chat_var[chat_id][user].get_user()[2]))
        namestring = username if username else name
        number_of_msg = chat_var[chat_id][user].get_msgcount()
        number_of_min = chat_var[chat_id][user].get_timecount()

        string += (namestring + " - " + str(number_of_msg) + " messages in " + str(number_of_min) + " minutes ") + "\n"
    return string


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


# noinspection PyUnusedLocal
def reset_daily_stats(request=0):
    global SessionChats
    SessionChats = {}
    return "Daily stats reset"


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


def find_memes_contain(cont=""):
    retval = []
    for key, value in sorted(meme.Dict.items()):
        if cont in key:
            retval.append(key)
    return retval


def find_links_contain(cont=""):
    retval = []
    for link in Links:
        if cont in str(link):
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
                   (request[1], "'" + "', '".join(find_links_contain(request[1])) + "'")
    else:
        return "Wrong number of parameters. Usage /recall <name> [nsfw/hide]"


# noinspection PyUnusedLocal
def build_search_link(request):
    if type(request) == list and len(request) in {1, 2}:
        load_links_file()
        string = "Currently remembered links %sare:\n" % \
                 (("that start with '%s' " % request[1]) if len(request) == 2 else "")
        string += "'" + "', '".join(find_links_contain(request[1] if len(request) == 2 else '')) + "'"
        return string
    else:
        return "Wrong number of parameters. Usage /listlink [phrase]"


def build_imgur_pic(request):
    if type(request) == list and len(request) == 2:

        req = urllib.request.Request("https://api.imgur.com/3/gallery/r/" + request[1] + "/top/week",
                                     headers=imgur_api.build_header())
        log("logged in as %s" % imgur_api.get_bot_username())
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


def draw_outlined_text(image, coords, text, font, outline="black", fill="white"):
    if type(coords) != tuple:
        raise ValueError("coords not tuple")
    x = coords[0]
    y = coords[1]
    image.text((x - 1, y - 1), text, font=font, fill=outline)
    image.text((x + 1, y + 1), text, font=font, fill=outline)
    image.text((x + 1, y - 1), text, font=font, fill=outline)
    image.text((x - 1, y + 1), text, font=font, fill=outline)
    image.text(coords, text, font=font, fill=fill)


def build_meme_from_link(request):

    dt = datetime.datetime.now()
    toptext = request[2] if len(request) == 4 else ""
    bottomtext = request[3] if len(request) == 4 else ""

    if not toptext and not bottomtext:
        return request[1]

    response = send_http_query(request[1])
    if response:
        file = io.BytesIO(response)
    else:
        return "URL not found"

    log("image loaded from %s " % request[1])
    basewidth = 640

    # resize file to base width 500

    img = Image.open(file)
    wpercent = (basewidth / float(img.size[0]))
    if 0.9 <= wpercent <= 1.1:
        hsize = int(float(img.size[1]) * float(wpercent))
        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        log("image resized")

    draw = ImageDraw.Draw(img)
    shadowcolor = "black"
    fillcolor = "white"
    width = img.size[0]
    height = img.size[1]
    textwidth = width - 100

    # search appropriate font size
    font = ImageFont.truetype(settings.font_location, 10)
    toptextsize = 0

    for i in range(100):
        font = ImageFont.truetype(settings.font_location, i)
        toptextsize = font.getsize(toptext)[0]
        if textwidth < toptextsize:
            break

    # draw top text
    draw_outlined_text(draw, ((width - toptextsize) / 2, 5), toptext, font=font, outline=shadowcolor, fill=fillcolor)

    # search appropriate font size
    bottextsize = 0
    bottextheight = 0
    for i in range(100):
        font = ImageFont.truetype(settings.font_location, i)
        bottextsize = font.getsize(bottomtext)[0]
        # workaround for older PIL version that is used by pythonanywhere
        bottextheight = i  # font.getsize(bottomtext)[1]
        if textwidth < bottextsize:
            break

    # draw bottom text
    draw_outlined_text(draw, ((width - bottextsize) / 2, height - bottextheight - 10), bottomtext,
                       font=font, outline=shadowcolor, fill=fillcolor)

    img.save(settings.image_temp_file, quality=50)
    log("Text added to the image")
    with open(settings.image_temp_file, "rb") as file:
        params = {'image': b64encode(file.read())}
        if album_id:
            params['album_id'] = album_id
        params['description'] = "[%02d:%02d:%02d] <%s>" % (dt.hour, dt.minute, dt.second, requester)
        data = urllib.parse.urlencode(params)
    binary_data = data.encode('ASCII')
    log("Upload start")
    req = urllib.request.Request("https://api.imgur.com/3/upload", data=binary_data,
                                 headers=imgur_api.build_header())
    log("logged in as %s" % imgur_api.get_bot_username())
    response = send_http_query(req)
    if response:
        log("Upload finish")
        json_data = json.loads(response.decode('utf-8'))
        return json_data['data']['link']
    else:
        log("Upload failed")
        return "Upload to imgur failed"


def build_meme_gen(request):
    if len(request) == 2:
        toptext = ""
        bottomtext = ""
    elif len(request) < 4:
        return "Wrong number of parameters. Usage /memegen <meme> '<text1>' '<text2>'"
    else:
        toptext = urllib.parse.quote_plus(request[2])
        bottomtext = urllib.parse.quote_plus(request[3])
    dt = datetime.datetime.now()
    if request[1] not in meme.Dict:
        if(request[1]) not in Links:
            pass

        else:  # request is in links dictionary
            request[1] = Links[request[1]]  # change request to link

        url = request[1]
        parsed_url = urllib.parse.urlparse(url)
        if not bool(parsed_url.scheme):
            return "Meme %s not found. Did you mean: %s" % (request[1], "'" +
                                                            "', '".join(find_memes_contain(request[1])) + "'" +
                                                            "', '".join(find_links_contain(request[1])) + "'")
        maintype = mimetypes.guess_type(parsed_url.path)[0]

        if maintype not in ('image/png', 'image/jpeg'):
            return "URL is not a png or jpeg"

        retval = build_meme_from_link(request)
    else:  # request in meme dictionary
        retval = "http://apimeme.com/meme?meme=%s&top=%s&bottom=%s" % (meme.Dict[request[1]], toptext, bottomtext)

        if imgur_api.logged_in():
            params = {'image': retval}
            if album_id:
                params['album_id'] = album_id
            params['description'] = "[%02d:%02d:%02d] <%s>" % (dt.hour, dt.minute, dt.second, requester)
            data = urllib.parse.urlencode(params)
            binary_data = data.encode('ASCII')
            req = urllib.request.Request("https://api.imgur.com/3/upload", data=binary_data,
                                         headers=imgur_api.build_header())
            send_http_query(req)

    with open("meme_history", "a") as file:

        file.write("[%d-%02d-%02d-%02d:%02d:%02d] <%s> %s\n" % (dt.year, dt.month, dt.day, dt.hour, dt.minute,
                                                                dt.second, requester, retval))
    return retval


def build_search_memes(request):
    if type(request) == list and len(request) in {1, 2}:
        string = "Currently implemented memes %sare:\n" % \
                 (("that contain with '%s' " % request[1]) if len(request) == 2 else "")
        string += "'" + "', '".join(find_memes_contain(request[1] if len(request) == 2 else '')) + "'"
        return string
    else:
        return "Wrong number of parameters. Usage /search_meme [phrase]"


def login_imgur(request):
    if len(request) == 1:
        return "Go to the following website: \n"\
               "https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=pin\n"\
               "use command /login_imgur <pin>" % imgur_api.client_id
    elif len(request) == 2:
        result = imgur_api.get_token_from_pin(request[1])
        if result:
            album_init()
            return "Logged in as: " + imgur_api.get_bot_username()
        else:
            return "Login failed. Imgur API might be down, or wrong pin code provided. Please try again"

    else:
        return "Wrong number of parameters. Usage /login_imgur"


# noinspection PyUnusedLocal
def login_status_imgur(request):
    if imgur_api.get_token():
        global nsfw_tag
        nsfw_tag = True
        return "Logged in as: " + imgur_api.get_bot_username() + "\n" + \
               "Full gallery can be viewed at: " + imgur_api.get_bot_imgur_profile()
    else:
        return "Not logged in"


# noinspection PyUnusedLocal
def logout_imgur(request):
    imgur_api.logout()
    global album_id
    album_id = 0
    return "The bot has successfully logged out of Imgur"


def album_init():
    if imgur_api.logged_in():
        try:
            with open("album") as file:
                global album_id
                content = file.read().splitlines()
                if content[0] == str(datetime.date.today()):
                    album_id = content[1]
                else:
                    create_today_album()
        except FileNotFoundError:
            create_today_album()


def create_today_album():
    if imgur_api.logged_in():
        global album_id
        album_id = create_album(str(datetime.date.today()))
        with open("album", 'w') as file:
            file.write(str(datetime.date.today()) + "\n" + album_id)


def create_album(albumname):
    data = urllib.parse.urlencode({'title': albumname, "layout": "grid"})
    binary_data = data.encode('ASCII')
    req = urllib.request.Request("https://api.imgur.com/3/album", data=binary_data,
                                 headers=imgur_api.build_header())
    log("logged in as %s" % imgur_api.get_bot_username())
    response = send_http_query(req)
    json_data = json.loads(response.decode('utf-8'))
    return json_data['data']['id']


def process(update):
    request = str(update['message']['text']) if 'text' in update['message'] else "$$"
    global chat_id
    chat_id = update['message']['chat']['id']
    global message_id
    message_id = update['message']['message_id']
    user_id = update['message']['from']['id']
    username = update['message']['from']['username'] if 'username' in update['message']['from'] else False
    first_name = update['message']['from']['first_name'] if 'first_name' in update['message']['from'] else False
    last_name = update['message']['from']['last_name'] if 'last_name' in update['message']['from'] else False
    name = (first_name + " ") if first_name else ""
    name += last_name if last_name else ""
    global requester
    requester = username if username else name

    message_timestamp = update['message']['date']

    # update stats
    for chat_var in [Chats, SessionChats]:
        if chat_id in chat_var:
            if user_id in chat_var[chat_id]:
                chat_var[chat_id][user_id].new_message(message_timestamp)
            else:
                chat_var[chat_id][user_id] = UserStat([username, first_name, last_name], timestamp=message_timestamp)
        else:
            chat_var[chat_id] = {user_id: UserStat([username, first_name, last_name], timestamp=message_timestamp)}

    # process received commands
    if request.startswith(botprefix):

        request = request.split(botprefix, 1)[1]
        if request:
            if "@" in request:
                target = request.split("@", 1)[1].split(" ")
                if target[0] != bot_username:
                    return
                else:
                    request = request.replace("@" + bot_username, "")
        else:
            return

        try:
            request = shlex.split(request)
        except ValueError:
            return

        switcher = {
            "": dummy,
            "help": build_help,
            "quote": build_quote,
            "stats_alltime": build_alltime_stats,
            "stats_daily": build_daily_stats,
            "about": build_about,
            "uptime": build_uptime,
            "list_users": list_users,
            "save_stats": save_stats,
            "reset_daily": reset_daily_stats,
            "remember": build_remember_link,
            "forget": build_forget_link,
            "recall": build_recall_link,
            "search": build_search_link,
            "getpic": build_imgur_pic,
            "memegen": build_meme_gen,
            "search_meme": build_search_memes,
            "login_imgur": login_imgur,
            "logout_imgur": logout_imgur,
            "imgur_status": login_status_imgur
        }
        log("Request - " + str(request))
        response = switcher[request[0]](request) if request[0] in switcher else False
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
imgur_api.init()
album_init()
log("bot initialization successful")
log("bot is now listening")
try:
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

        if save_stats_cnt < settings.stats_save_freq:  # every 5 minutes
            save_stats_cnt += 1
        else:
            save_stats_cnt = 0
            save_stats()

            with open('sync','w') as f: # for sync with other process
                f.write(str(int(time.time())))

        # reset daily stats @03:00 am
        if datetime.datetime.now().hour == 3 and datetime.datetime.now().minute == 0:
            if daily_stats_reset == 0:
                log(reset_daily_stats())
                daily_stats_reset = 1
                album_init() # create new album for today

            else:
                daily_stats_reset = 0

        time.sleep(updateFrequency)

finally:
    with open("sync","w") as f:
        pass  # delete sync if exception occurred
