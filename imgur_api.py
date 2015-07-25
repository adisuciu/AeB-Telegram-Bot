__author__ = 'adrian.suciu'

import urllib.request
import sys
import os
import json
import time

client_id = 0
client_secret = 0
current_token = {}


def get_token_from_imgur(param):
    json_data = json.dumps(param).encode('utf8')
    global current_token
    try:
        req = urllib.request.urlopen("https://api.imgur.com/oauth2/token", data=json_data)
        json_data = json.loads(req.read().decode('utf-8'))
        print(str(json_data))
        current_token = {'access_token': json_data['access_token'], 'refresh_token': json_data['refresh_token'],
                         'timestamp': time.time(), "expires_in": json_data['expires_in'],
                         "account_username": json_data['account_username']}
        return True
    except (urllib.request.URLError, urllib.request.HTTPError):
        print("Token cannot be refreshed due to HTTP Exception: " + (str(sys.exc_info())))
        return False


def get_token_from_pin(pin):

    params = {"client_id": client_id,
              "client_secret" : client_secret,
              "grant_type" : "pin",
              "pin": pin}

    retval = get_token_from_imgur(params)
    write_token_to_file()
    return retval


def refresh_token():
    params = {"refresh_token": current_token['refresh_token'],
              "client_id": 'afc6b8634860754',
              "client_secret": '662b35fe7c3b9efd90ba8b391de7c3c9eadadcfb',
              "grant_type": 'refresh_token'
              }
    retval = get_token_from_imgur(params)
    write_token_to_file()
    return retval


def write_token_to_file():
    with open("token", "w") as f:
        output = json.dumps(current_token)
        f.write(output)


def read_token_from_file(filename):
    with open(filename) as file:
        global current_token
        current_token = json.loads(file.read())


def get_token():
    # we consider token expired if 3/4 of it's expiration time was reached
    if not current_token:
        return False
    token_expiration_timestamp = (int(current_token['timestamp'])) + ((int(current_token['expires_in'])) * 3 / 4)

    if time.time() > token_expiration_timestamp:
        refresh_succesful = refresh_token()
        if refresh_succesful:
            write_token_to_file()
        else:
            return False
    return True


def build_header():
    global current_token
    result = get_token()
    if result:
        # logged in
        return {"Authorization": ("Bearer " + current_token['access_token'])}
    else:
        # not logged in
        return {"Authorization": ("Client-ID " + str(client_id))}


def logged_in():
    return get_token()


def logout():
    try:
        os.remove('token')
        global current_token
        current_token = {}
    except OSError:
        pass


def get_bot_username():
    return current_token['account_username'] if current_token else "not logged in"


def get_bot_imgur_profile():
    return current_token['account_username'] + ".imgur.com/all" if current_token else "not logged in"


def init():
    global client_id, client_secret
    with open("imgurtoken", "r") as f:
        content = f.read().splitlines()
        client_id = content[0]
        client_secret = content[1]
    try:
        read_token_from_file("token")
    except FileNotFoundError:
        print("Refresh token not available. Login via bot")
