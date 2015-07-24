
import time
import settings
import os

with open("sync") as f:
    t = f.read()
sync = int(t)
now = time.time()
if (now - sync) >= settings.stats_save_freq*2:
    os.chdir("AeB-Telegram-Bot")
    os.system("python3 aebb.py")
    with open("sync",'w') as f:
        f.write(int(time.time()))
else:
    # nothing to do, app is already running
    print("App is already running")

