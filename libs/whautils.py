#!/usr/bin/env python3
#
# File: whautils.py
# Auth: Joe Broesele
# Mod.: Joe Broesele
# Date: 05 May 2020
# Rev.: 06 May 2020
#
# Utility library for the WhatsApp Parser Toolset.
#



import os
import sys
from configparser import ConfigParser

# Define global variables.
settings = {
    # Section 'report'.
    "logo":             "",
    "logo_height":      "",
    "record":           "",
    "unit":             "",
    "examiner":         "",
    "notes":            "",
    "prefix":           "",
    "bg_index":         "",
    "bg_report":        "",
    "preview_pics_size":"",
    # Section 'auth'.
    "gmail":            "",
    "passw":            "",
    "devid":            "",
    "celnumbr":         "",
    # Section 'app'.
    "pkg":              "",
    "sig":              "",
    # Section 'client'.
    "client_pkg":       "",
    "client_sig":       "",
    "client_ver":       ""
}
prefixError = "ERROR: "
settingsFile = os.path.dirname(__file__) + "/../cfg/settings.cfg".replace("/", os.path.sep)



def create_settings_file():
    """Function that creates the settings file."""
    settingsDefault = """\
# WhatsApp Parser Toolset v1.16 settings file.

[report]
logo = ./cfg/logo.png
logo_height = 128
company =
record =
unit =
examiner =
notes =
prefix = report_
bg_index = ./images/background-index.png
bg_report = ./images/background.png
preview_pics_size = 100

[auth]
gmail = alias@gmail.com
passw = yourpassword
devid = 1234567887654321
celnumbr = BackupPhoneNunmber

[app]
pkg = com.whatsapp
sig = 38a0f7d505fe18fec64fbf343ecaaaf310dbd799

[client]
pkg = com.google.android.gms
sig = 38918a453d07199354f8b19af05ec6562ced5788
ver = 9877000
"""
    try:
        if os.path.isfile(settingsFile) is False:
            with open(settingsFile, 'w') as cfg:
                cfg.write(settingsDefault.replace("/", os.path.sep))
    except Exception as e:
        print(prefixError + "Cannot create the settings file `{0:s}': ".format(settingsFile) + str(e))
        sys.exit(1)



def read_settings_file():
    """Function to read the settings file."""
    try:
        config = ConfigParser()
        config.read(settingsFile)
        # Section 'report'.
        settings['logo']                = config.get('report', 'logo')
        settings['logo_height']         = config.get('report', 'logo_height')
        settings['company']             = config.get('report', 'company')
        settings['record']              = config.get('report', 'record')
        settings['unit']                = config.get('report', 'unit')
        settings['examiner']            = config.get('report', 'examiner')
        settings['notes']               = config.get('report', 'notes')
        settings['prefix']              = config.get('report', 'prefix')
        settings['bg_index']            = config.get('report', 'bg_index')
        settings['bg_report']           = config.get('report', 'bg_report')
        settings['preview_pics_size']   = config.get('report', 'preview_pics_size')
        # Section 'auth'.
        settings['gmail']               = config.get('auth', 'gmail')
        settings['passw']               = config.get('auth', 'passw')
        settings['devid']               = config.get('auth', 'devid')
        settings['celnumbr']            = config.get('auth', 'celnumbr').lstrip('+0')
        # Section 'app'.
        settings['pkg']                 = config.get('app', 'pkg')
        settings['sig']                 = config.get('app', 'sig')
        # Section 'client'.
        settings['client_pkg']          = config.get('client', 'pkg')
        settings['client_sig']          = config.get('client', 'sig')
        settings['client_ver']          = config.get('client', 'ver')

        return settings
    except Exception as e:
        print(prefixError + "The settings file `{0:s}' is missing or corrupt! Error: ".format(settingsFile) + str(e))
        sys.exit(1)

