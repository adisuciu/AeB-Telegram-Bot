import datetime
botQueryURL = "https://api.telegram.org/bot122796814:AAFFzsDhSGGCLOd_o2KDmsJOiSA99Zc944o/"
dt = datetime.datetime.now()
updateFrequency = 1  # seconds
quote_file = "bug_mafia.txt"
links_file = "links.txt"
log_file = "log-%d%02d%02d-%02d%02d%02d.txt" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
# vlog_file = "log.txt"
stats_file = "stats.txt"
about_message = "Aici este BAIETII Official bot - v0.1\nSources available at: " \
                "https://github.com/adisuciu/AeB-Telegram-Bot\n"

