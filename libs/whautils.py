#!/usr/bin/env python3
#
# File: whautils.py
# Auth: Joe Broesele
# Mod.: Joe Broesele
# Date: 05 May 2020
# Rev.: 22 Dec 2024
#
# Utility library for the WhatsApp Parser Toolset.
#



import os
import sys
from configparser import ConfigParser



# Change to the WhatsApp Parser Toolset base directory as working directory.
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))



# Define global variables.
whacipher_version   = "1.2"
whagodri_version    = "1.3"
whamerge_version    = "1.1"
whapa_version       = "1.8"
whapa_gui_version   = "2024.12.22" # based on Whapa 1.59 from Bigfoot
settings = {
    # Section 'report'.
    "logo":                     "",
    "logo_height":              "",
    "company":                  "",
    "record":                   "",
    "unit":                     "",
    "examiner":                 "",
    "notes":                    "",
    "report_prefix":            "",
    "bg_index":                 "",
    "bg_report":                "",
    "preview_pics_size":        "",
    "preview_pics_max_width":   "",
    "preview_pics_max_height":  "",
    "profile_pics_enable":      "",
    "profile_pics_size_report": "",
    "profile_pics_size_index":  "",
    "profile_pics_dir":         "",
    "profile_pic_user":         "",
    "profile_pic_group":        "",
    "contact_vcard_dir":        "",
    "contact_tooltip_enable":   "",
    "contact_tooltip_pretty":   "",
    "custom_emoji_enable":      "",
    "custom_emoji_size":        "",
    "custom_emoji_dir":         "",
    "html_links_enable":        "",
    "html_img_alt_enable":      "",
    "html_img_noimage_pic":     "",
    "debug_warnings_enable":    "",
    "debug_errors_enable":      "",
    # Section 'auth'.
    "gmail":                    "",
    "gmail_passw":              "",
    "devid":                    "",
    "celnumbr":                 "",
    "oauth":                    "",
    "android_id":               "",
    # Section 'icloud-auth'.
    "icloud":                   "",
    "icloud_passw":             "",
    # Section 'app'.
    "pkg":                      "",
    "sig":                      "",
    # Section 'client'.
    "client_pkg":               "",
    "client_sig":               "",
    "client_ver":               ""
}
prefixError = "ERROR: "
settingsFile = "./cfg/settings.cfg".replace("/", os.path.sep)



def create_settings_file():
    """Function that creates the settings file."""
    settingsDefault = """\
# WhatsApp Parser Toolset v""" + whapa_gui_version + """ settings file.

[report]
logo = ./cfg/logo.png
logo_height = 128
company =
record =
unit =
examiner =
notes =
report_prefix = report_
bg_index = ./images/background-index.png
bg_report = ./images/background.png
preview_pics_size = 100
preview_pics_max_width = 500
preview_pics_max_height = 500
profile_pics_enable = no
profile_pics_size_report = 128
profile_pics_size_index = 48
profile_pics_dir = ./Media/Profile Pictures/
profile_pic_user = ./images/profile-pic-user.jpg
profile_pic_group = ./images/profile-pic-group.jpg
contact_vcard_dir = ./Media/Contact vCards/
contact_tooltip_enable = yes
contact_tooltip_pretty = yes
custom_emoji_enable = yes
custom_emoji_size = 20
custom_emoji_dir = ./images/emoji
html_links_enable = yes
html_img_alt_enable = no
html_img_noimage_pic = ./images/noimage.png
debug_warnings_enable = no
debug_errors_enable = no

[auth]
gmail = alias@gmail.com
passw = yourpassword
devid = 1234567887654321
celnumbr = BackupPhoneNunmber
oauth = OAuthToken
android_id = AndroidId

[icloud-auth] 
icloud  = alias@icloud.com
passw = yourpassword

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
        settings['logo']                    = config.get('report', 'logo')
        settings['logo_height']             = config.get('report', 'logo_height')
        settings['company']                 = config.get('report', 'company')
        settings['record']                  = config.get('report', 'record')
        settings['unit']                    = config.get('report', 'unit')
        settings['examiner']                = config.get('report', 'examiner')
        settings['notes']                   = config.get('report', 'notes')
        settings['report_prefix']           = config.get('report', 'report_prefix')
        settings['bg_index']                = config.get('report', 'bg_index')
        settings['bg_report']               = config.get('report', 'bg_report')
        settings['preview_pics_size']       = config.get('report', 'preview_pics_size')
        settings['preview_pics_max_width']  = config.get('report', 'preview_pics_max_width')
        settings['preview_pics_max_height'] = config.get('report', 'preview_pics_max_height')
        settings['profile_pics_enable']     = config.get('report', 'profile_pics_enable')
        settings['profile_pics_size_report']= config.get('report', 'profile_pics_size_report')
        settings['profile_pics_size_index'] = config.get('report', 'profile_pics_size_index')
        settings['profile_pics_dir']        = config.get('report', 'profile_pics_dir')
        settings['profile_pic_user']        = config.get('report', 'profile_pic_user')
        settings['profile_pic_group']       = config.get('report', 'profile_pic_group')
        settings['contact_vcard_dir']       = config.get('report', 'contact_vcard_dir')
        settings['contact_tooltip_enable']  = config.get('report', 'contact_tooltip_enable')
        settings['contact_tooltip_pretty']  = config.get('report', 'contact_tooltip_pretty')
        settings['custom_emoji_enable']     = config.get('report', 'custom_emoji_enable')
        settings['custom_emoji_size']       = config.get('report', 'custom_emoji_size')
        settings['custom_emoji_dir']        = config.get('report', 'custom_emoji_dir')
        settings['html_links_enable']       = config.get('report', 'html_links_enable')
        settings['html_img_alt_enable']     = config.get('report', 'html_img_alt_enable')
        settings['html_img_noimage_pic']    = config.get('report', 'html_img_noimage_pic')
        settings['debug_warnings_enable']   = config.get('report', 'debug_warnings_enable')
        settings['debug_errors_enable']     = config.get('report', 'debug_errors_enable')
        # Section 'auth'.
        settings['gmail']                   = config.get('auth', 'gmail')
        settings['gmail_passw']             = config.get('auth', 'passw')
        settings['devid']                   = config.get('auth', 'devid')
        settings['celnumbr']                = config.get('auth', 'celnumbr').lstrip('+0')
        settings['oauth']                   = config.get('auth', 'oauth')
        settings['android_id']              = config.get('auth', 'android_id')
        # Section 'icloud-auth'.
        settings['icloud']                  = config.get('icloud-auth', 'icloud')
        settings['icloud_passw']            = config.get('icloud-auth', 'passw')
        # Section 'app'.
        settings['pkg']                     = config.get('app', 'pkg')
        settings['sig']                     = config.get('app', 'sig')
        # Section 'client'.
        settings['client_pkg']              = config.get('client', 'pkg')
        settings['client_sig']              = config.get('client', 'sig')
        settings['client_ver']              = config.get('client', 'ver')

        # Evaluate boolean settings.
        bool_true_list = ['1', 'on', 'true', 't', 'yes', 'y']
        settings['profile_pics_enable']     = bool(settings['profile_pics_enable'].lower() in bool_true_list)
        settings['contact_tooltip_enable']  = bool(settings['contact_tooltip_enable'].lower() in bool_true_list)
        settings['contact_tooltip_pretty']  = bool(settings['contact_tooltip_pretty'].lower() in bool_true_list)
        settings['custom_emoji_enable']     = bool(settings['custom_emoji_enable'].lower() in bool_true_list)
        settings['html_links_enable']       = bool(settings['html_links_enable'].lower() in bool_true_list)
        settings['html_img_alt_enable']     = bool(settings['html_img_alt_enable'].lower() in bool_true_list)
        settings['debug_warnings_enable']   = bool(settings['debug_warnings_enable'].lower() in bool_true_list)
        settings['debug_errors_enable']     = bool(settings['debug_errors_enable'].lower() in bool_true_list)

        # Set the correct path format for all files and directories: Relative
        # to the WhatsApp Parser Toolset base directory, beginning with "./".
        settings['bg_index']                = os.path.join(".", os.path.relpath(settings['bg_index']))
        settings['bg_report']               = os.path.join(".", os.path.relpath(settings['bg_report']))
        settings['profile_pics_dir']        = os.path.join(".", os.path.relpath(settings['profile_pics_dir']))
        settings['profile_pic_user']        = os.path.join(".", os.path.relpath(settings['profile_pic_user']))
        settings['profile_pic_group']       = os.path.join(".", os.path.relpath(settings['profile_pic_group']))
        settings['contact_vcard_dir']       = os.path.join(".", os.path.relpath(settings['contact_vcard_dir']))
        settings['custom_emoji_dir']        = os.path.join(".", os.path.relpath(settings['custom_emoji_dir']))
        settings['html_img_noimage_pic']    = os.path.join(".", os.path.relpath(settings['html_img_noimage_pic']))

        return settings
    except Exception as e:
        print(prefixError + "The settings file `{0:s}' is missing or corrupt! Error: ".format(settingsFile) + str(e))
        sys.exit(1)



def check_google_password():
    """Function to check if the Google password is valid."""
    read_settings_file()
    password = settings['passw']
    if not password or password == 'yourpassword':
        return False
    return True

