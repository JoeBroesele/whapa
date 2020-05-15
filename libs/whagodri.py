#!/usr/bin/env python3

import json
import os
import re
import sys
import queue as queue
import threading
import time
import argparse
import getpass
import requests
from gpsoauth import google

# Append library folder to Python path.
sys.path.append(os.path.relpath(os.path.join(os.path.dirname(__file__), 'libs')))

import whautils

# Define global variables.
version = whautils.whagodri_version
exitFlag = 0
nextPageToken = ""
backups = []
bearer = ""
queueLock = threading.Lock()
workQueue = queue.Queue(9999999)
settings = whautils.settings


def banner():
    """ Function Banner """
    print("""
     __      __.__             ________      ________        .__
    /  \    /  \  |__ _____   /  _____/  ____\______ \_______|__|
    \   \/\/   /  |  \\\\__  \ /   \  ___ /  _ \|    |  \_  __ \  |
     \        /|   Y  \/ __ \\\\    \_\  (  <_> )    `   \  | \/  |
      \__/\  / |___|  (____  /\______  /\____/_______  /__|  |__|
           \/       \/     \/        \/              \/
    ----------- WhatsApp Google Drive Extractor v""" + version + """ ------------
    """)


def show_help():
    """Function showing help message."""

    print("""\
    ** Author: Ivan Moreno a.k.a B16f00t
    ** Github: https://github.com/B16f00t
    ** Fork from WhatsAppGDExtract by TripCode and forum.xda-developers.com

    Usage: python3 whagodri.py -h (for help)
    """)


def getConfigs():
    try:
        # Create the settings file if it does not exist.
        whautils.create_settings_file()
        # Read the settings from the settings file.
        settings = whautils.read_settings_file()
        if not whautils.check_google_password():
            settings['passw'] = getpass.getpass(prompt="Google password for account '" + settings['gmail'] + "': ", stream=None)
        if not settings['passw']:
            quit('[e] The password must not be empty!')
    except Exception as e:
        print("[e] The settings file `{0:s}' is missing or corrupt! Error: ".format(whautils.settingsFile) + str(e))
        sys.exit(1)


def size(obj):
    if obj > 1048576:
        return "(" + "{0:.2f}".format(obj / float(1048576)) + " MB)"
    else:
        return "(" + "{0:.2f}".format(obj / float(1024)) + " KB)"


def getGoogleAccountTokenFromAuth():
    b64_key_7_3_29 = (b"AAAAgMom/1a/v0lblO2Ubrt60J2gcuXSljGFQXgcyZWveWLEwo6prwgi3"
                      b"iJIZdodyhKZQrNWp5nKJ3srRXcUW+F1BD3baEVGcmEgqaLZUNBjm057pK"
                      b"RI16kB0YppeGx5qIQ5QjKzsR8ETQbKLNWgRY0QRNVz34kMJR3P/LgHax/"
                      b"6rmf5AAAAAwEAAQ==")

    android_key_7_3_29 = google.key_from_b64(b64_key_7_3_29)
    encpass = google.signature(settings['gmail'], settings['passw'], android_key_7_3_29)
    payload = {'Email':settings['gmail'], 'EncryptedPasswd':encpass, 'app':settings['client_pkg'], 'client_sig':settings['client_sig'], 'parentAndroidId':settings['devid']}
    header = {'User-Agent': 'WhatsApp/2.19.244 Android/Device/Whapa'}
    request = requests.post('https://android.clients.google.com/auth', data=payload, headers=header)
    token = re.search('Token=(.*?)\n', request.text)
    if token:
        return token.group(1)
    else:
        quit(request.text)


def getGoogleDriveToken(token):
    payload = {'Token':token, 'app':settings['pkg'], 'client_sig':settings['sig'], 'device':settings['devid'], 'google_play_services_version':settings['client_ver'], 'service':'oauth2:https://www.googleapis.com/auth/drive.appdata https://www.googleapis.com/auth/drive.file', 'has_permission':'1'}
    header = {'User-Agent': 'WhatsApp/2.19.244 Android/9.0 Device/Whapa'}
    request = requests.post('https://android.clients.google.com/auth', data=payload, headers=header)
    try:
        token = request.text.split('Auth=')[1]
    except Exception as e:
        return str(e)

    return token
#    token = re.search('Auth=(.*?)\n', request.text)
#    if token:
#        return token.group(1)
#    else:
#        quit(request.text)


def gDriveFileMap(bearer, nextPageToken):
    header = {'Authorization': 'Bearer ' + bearer, 'User-Agent': 'WhatsApp/2.19.244 Android/9.0 Device/Whapa'}
    url_data = "https://backup.googleapis.com/v1/clients/wa/backups/{}".format(settings['celnumbr'])
    url_files = "https://backup.googleapis.com/v1/clients/wa/backups/{}/files?{}pageSize=5000".format(settings['celnumbr'], "pageToken=" + nextPageToken + "&")
    request_data = requests.get(url_data, headers=header)
    request_files = requests.get(url_files, headers=header)
    data_data = json.loads(request_data.text)
    data_files = json.loads(request_files.text)
    try:
        try:
            nextPageToken = data_files['nextPageToken']
        except Exception as e:
            nextPageToken = ""

        for result in data_files['files']:
            backups.append(result['name'])
        if nextPageToken:
            gDriveFileMap(bearer, nextPageToken)

    except Exception as e:
        if data_files:
            print("[e] Error: ", data_files['error']['message'])
        else:
            print("[e] No Google Drive backup: {}".format(e))

    if not backups:
        print("[e] Unable to locate google drive file map for: {} {}".format(settings['pkg'], request_files))

    return data_data, backups


def downloadFileGoogleDrive(bearer, url, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    header = {'Authorization': 'Bearer ' + bearer, 'User-Agent': 'WhatsApp/2.19.244 Android/Device/Whapa'}
    request = requests.get(url, headers=header, stream=True)
    request.raw.decode_content = True
    if request.status_code == 200:
        with open(local, 'wb') as asset:
            for chunk in request.iter_content(1024):
                asset.write(chunk)
        print("    [-] Downloaded     : {}".format(local))
    else:
        print("    [-] Not downloaded : {}".format(local))


def getMultipleFiles(drives, bearer, files):
    threadList = ["Thread-01", "Thread-02", "Thread-03", "Thread-04", "Thread-05", "Thread-06", "Thread-07", "Thread-08", "Thread-09", "Thread-10",
                  "Thread-11", "Thread-12", "Thread-13", "Thread-14", "Thread-15", "Thread-16", "Thread-17", "Thread-18", "Thread-19", "Thread-20",
                  "Thread-21", "Thread-22", "Thread-23", "Thread-24", "Thread-25", "Thread-26", "Thread-27", "Thread-28", "Thread-29", "Thread-30",
                  "Thread-31", "Thread-32", "Thread-33", "Thread-34", "Thread-35", "Thread-36", "Thread-37", "Thread-38", "Thread-39", "Thread-40"]
    threads = []
    threadID = 1
    print("[i] Generating threads...")
    print("[+] Backup name : {}".format(drives["name"]))
    for tName in threadList:
        thread = MyThread(threadID, tName, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    n = 1
    lenfiles = len(files)
    queueLock.acquire()
    if args.output:
        output = args.output
    else:
        output = ""

    for entries in files:
        file = entries.split('files/')[1]
        local_store = (output + file).replace("/", os.path.sep)
        if os.path.isfile(local_store):
            print("    [-] Number: {}/{}  => {} Skipped".format(n, lenfiles, local_store))
        else:
            url = "https://backup.googleapis.com/v1/clients/wa/backups/{}/files/{}?alt=media".format(settings['celnumbr'], file)
            workQueue.put({'bearer': bearer, 'url': url, 'local': local_store, 'now': n, 'lenfiles': lenfiles})
        n += 1

    queueLock.release()
    while not workQueue.empty():
        pass

    global exitFlag
    exitFlag = 1
    for t in threads:
        t.join()
    print("[i] Downloads finished")


class MyThread(threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q

    def run(self):
        process_data(self.name, self.q)


def process_data(threadName, q):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            data = q.get()
            queueLock.release()
            getMultipleFilesThread(data['bearer'], data['url'], data['local'], data['now'], data['lenfiles'], threadName)
            time.sleep(1)

        else:
            queueLock.release()
            time.sleep(1)


def getMultipleFilesThread(bearer, url, local, now, lenfiles, threadName):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    header = {'Authorization': 'Bearer ' + bearer, 'User-Agent': 'WhatsApp/2.19.244'}
    request = requests.get(url, headers=header, stream=True)
    request.raw.decode_content = True
    if request.status_code == 200:
        with open(local, 'wb') as asset:
            for chunk in request.iter_content(1024):
                asset.write(chunk)
        print("    [-] Number: {}/{} - {} => Downloaded: {}".format(now, lenfiles,  threadName, local))

    else:
        print("    [-] Number: {}/{} - {} => Not downloaded: {}".format(now, lenfiles,  threadName, local))


# Initializing
if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser(description="Extract your WhatsApp files from Google Drive")
    user_parser = parser.add_mutually_exclusive_group()
    user_parser.add_argument("-i", "--info", help="Show information about WhatsApp backups", action="store_true")
    user_parser.add_argument("-l", "--list", help="List all available files", action="store_true")
    user_parser.add_argument("-lw", "--list_whatsapp", help="List WhatsApp backups", action="store_true")
    user_parser.add_argument("-p", "--pull", help="Pull a file from Google Drive")
    user_parser.add_argument("-s", "--sync", help="Sync all files locally", action="store_true")
    user_parser.add_argument("-si", "--s_images", help="Sync Images files locally", action="store_true")
    user_parser.add_argument("-sv", "--s_videos", help="Sync Videos files locally", action="store_true")
    user_parser.add_argument("-sa", "--s_audios", help="Sync Audios files locally", action="store_true")
    user_parser.add_argument("-sx", "--s_documents", help="Sync Documents files locally", action="store_true")
    user_parser.add_argument("-sd", "--s_databases", help="Sync Databases files locally", action="store_true")
    parser.add_argument("-o", "--output", help="Output path to save files")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        show_help()
    else:
        print("[i] Searching...\n")
        getConfigs()
        bearer = getGoogleDriveToken(getGoogleAccountTokenFromAuth())
        print("Your Google Access Token: {}\n".format(bearer))
        drives, files = gDriveFileMap(bearer, nextPageToken)

        if args.info:
            try:
                print("[-] Backup name   : {}".format(drives["name"]))
                print("[-] Backup upload : {}".format(drives["updateTime"]))
                print("[-] Backup size   : {} Bytes {}".format(drives["sizeBytes"], size(int(drives["sizeBytes"]))))
                print("[+] Backup metadata")
                print("    [-] Backup Frequency         : {} ".format(json.loads(drives["metadata"])["backupFrequency"]))
                print("    [-] Backup Network Settings  : {} ".format(json.loads(drives["metadata"])["backupNetworkSettings"]))
                print("    [-] Backup Version           : {} ".format(json.loads(drives["metadata"])["backupVersion"]))
                print("    [-] Include Videos In Backup : {} ".format(json.loads(drives["metadata"])["includeVideosInBackup"]))
                print("    [-] Num Of Photos            : {}".format(json.loads(drives["metadata"])["numOfPhotos"]))
                print("    [-] Num Of Media Files       : {}".format(json.loads(drives["metadata"])["numOfMediaFiles"]))
                print("    [-] Num Of Messages          : {}".format(json.loads(drives["metadata"])["numOfMessages"]))
                print("    [-] Video Size               : {} Bytes {}".format(json.loads(drives["metadata"])["videoSize"], size(int(json.loads(drives["metadata"])["videoSize"]))))
                print("    [-] Backup Size              : {} Bytes {}".format(json.loads(drives["metadata"])["backupSize"], size(int(json.loads(drives["metadata"])["backupSize"]))))
                print("    [-] Media Size               : {} Bytes {}".format(json.loads(drives["metadata"])["mediaSize"], size(int(json.loads(drives["metadata"])["mediaSize"]))))
                print("    [-] Chat DB Size             : {} Bytes {}".format(json.loads(drives["metadata"])["chatdbSize"], size(int(json.loads(drives["metadata"])["chatdbSize"]))))

            except Exception as e:
                print("[i] Error: {}".format(e))

        elif args.list:
            print("[+] Backup name : {}".format(drives["name"]))
            lenfiles = len(files)
            n = 1
            for i in files:
                print("    [-] File {}/{}  : {}".format(n, lenfiles, i.split('files/')[1]))
                n += 1

        if args.list_whatsapp:
            print("[+] Backup name : {}".format(drives["name"]))
            lenfiles = len(files)
            n = 1
            for i in files:
                i = i.split('files/')[1]
                if i == "Databases/msgstore.db.crypt12":
                    print("    [-] File {}/{}   : {}".format(n, lenfiles, i))
                    print("    [-] Chat DB Size : {} Bytes {}".format(json.loads(drives["metadata"])["chatdbSize"], size(int(json.loads(drives["metadata"])["chatdbSize"]))))
                    exit()
                n += 1

        if args.sync:
            getMultipleFiles(drives, bearer, files)

        if args.s_images:
            filter_var = []
            for i in files:
                try:
                    if i.split("/")[6] == ".Statuses" or i.split("/")[6] == "WhatsApp Images" or i.split("/")[6] == "WhatsApp Stickers" or i.split("/")[6] == "WhatsApp Profile Photos" or i.split("/")[6] == "WallPaper":
                        filter_var.append(i)
                except Exception as e:
                    pass
            getMultipleFiles(drives, bearer, filter_var)

        if args.s_videos:
            filter_var = []
            for i in files:
                try:
                    if i.split("/")[6] == ".Statuses" or i.split("/")[6] == "WhatsApp Animated Gifs" or i.split("/")[6] == "WhatsApp Video":
                        filter_var.append(i)
                except Exception as e:
                    pass
            getMultipleFiles(drives, bearer, filter_var)

        if args.s_audios:
            filter_var = []
            for i in files:
                try:
                    if i.split("/")[6] == "WhatsApp Voice Notes" or i.split("/")[6] == "WhatsApp Audio":
                        filter_var.append(i)
                except Exception as e:
                    pass
            getMultipleFiles(drives, bearer, filter_var)

        if args.s_documents:
            filter_var = []
            for i in files:
                try:
                    if i.split("/")[6] == "WhatsApp Documents":
                        filter_var.append(i)
                except Exception as e:
                    pass
            getMultipleFiles(drives, bearer, filter_var)

        if args.s_databases:
            filter_var = []
            for i in files:
                try:
                    if i.split("/")[5] == "Databases" or i.split("/")[5] == "Backups" or i.split("/")[5] == "gdrive_file_map":
                        filter_var.append(i)
                except Exception as e:
                    pass
            getMultipleFiles(drives, bearer, filter_var)

        if args.pull:
            try:
                file = str(args.pull)
                local_store = file.replace("/", os.path.sep)

                if args.output:
                    local_store = args.output + local_store
                if os.path.isfile(local_store):
                    print("[+] Backup name : {}".format(drives["name"]))
                    print("    [-] Skipped : {}".format(local_store))
                else:
                    print("[+] Backup name        : {}".format(drives["name"]))
                    downloadFileGoogleDrive(bearer, "https://backup.googleapis.com/v1/clients/wa/backups/{}/files/{}?alt=media".format(settings['celnumbr'], file), local_store)
            except Exception as e:
                print("[e] Unable to locate: {}".format(file))
