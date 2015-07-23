import datetime

with open("bottoken", "r") as f:
    botToken = f.read()
botQueryURL = "https://api.telegram.org/bot%s/" % botToken
with open("imgurtoken", "r") as f:
    imgur_api_client_id = f.read()
dt = datetime.datetime.now()
updateFrequency = 1.5  # seconds
quote_file = "bug_mafia.txt"
links_file = "links.txt"
log_file = "log-%d%02d%02d-%02d%02d%02d.txt" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
image_temp_file = "temp.jpg"
# log_file = "log.txt"
stats_file = "stats.txt"
with open("font","r") as f:
    font_location = f.read()
about_message = "Aici este BAIETII Official bot - v0.1\nSources available at: " \
                "https://github.com/adisuciu/AeB-Telegram-Bot\n"

