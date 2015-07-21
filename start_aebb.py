import logging
import socket
import os
import sys


lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
try:
    lock_id = "adisuciu88.aebb"   # this should be unique. using your username as a prefix is a convention
    lock_socket.bind('\0' + lock_id)
    logging.debug("Acquired lock %r" % (lock_id,))
except socket.error:
    # socket already locked, task must already be running
    logging.info("Failed to acquire lock %r" % (lock_id,))
    sys.exit()

os.chdir("AeB-Telegram-Bot")
os.system("python3 aebb.py")