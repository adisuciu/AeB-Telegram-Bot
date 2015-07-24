import time
import settings
import os

try:
    with open("sync") as f:
        t = f.read()
    sync = int(t)
except:
    print ("file sync not found")
    sync = 0

now = time.time()
if (now - sync) >= settings.stats_save_freq*2:
    with open("sync",'w') as f:
        f.write(str(int(time.time())))
    import aebb

else:
    # nothing to do, app is already running
    print("App is already running")

