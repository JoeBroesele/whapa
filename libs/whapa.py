#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from colorama import init, Fore
from configparser import ConfigParser
import html
import distutils.dir_util
import argparse
import sqlite3
import time
import sys
import os
import shutil
import random
import quopri
import re
from PIL import Image

# Append library folder to Python path.
sys.path.append(os.path.relpath(os.path.join(os.path.dirname(__file__), 'libs')))

import whautils
import whaemoji

# Define global variables.
arg_user = ""
arg_group = ""
cursor = None
message = ""
report_var = "None"
report_html = ""
report_group = ""
version = whautils.whapa_version
names_dict = {}            # names wa.db
color = {}                 # participants color
current_color = "#5586e5"  # default participant color
abs_path_file = os.path.abspath(__file__)    # C:\Users\Desktop\whapa\libs\whapa.py
abs_path = os.path.split(abs_path_file)[0]   # C:\Users\Desktop\whapa\libs\
split_path = abs_path.split(os.sep)[:-1]     # ['C:', 'Users', 'Desktop', 'whapa']
whapa_path = os.path.sep.join(split_path)    # C:\Users\Desktop\whapa
media_rel_path = "../"      # Relative path to "Media" directory.
settings = whautils.settings
# Define variables to suppress pylint errors.
args = ""
local = ""
cursor_rep = []

# Message prefixes.
prefix_info    = "[i] "
prefix_warning = "[w] "
prefix_error   = "[e] "
prefix_fatal   = "[fatal] "

# Counters.
count_messages    = 0
count_group_chats = 0
count_user_chats  = 0
count_warnings    = 0
count_errors      = 0

# Language definitions.
lang_en_me = "Me"
lang_en_sys_msg = "System Message"
lang_es_me = "Yo"
lang_es_sys_msg = "Mensaje de Sistema"
lang_de_me = "Ich"
lang_de_sys_msg = "System-Nachricht"


def banner():
    """Function Banner"""

    print(r"""
     __      __.__          __________
    /  \    /  \  |__ _____ \______   \_____
    \   \/\/   /  |  \\\\__  \ |     ___/\__  \\
     \        /|   Y  \/ __ \|    |     / __ \\_
      \__/\  / |___|  (____  /____|    (____  /
           \/       \/     \/               \/
    ---------- WhatsApp Parser v""" + version + """ -----------
    """)


def show_help():
    """Function showing help message."""

    print("""\
    ** Author: Ivan Moreno a.k.a B16f00t
    ** Github: https://github.com/B16f00t

    Usage: python3 whapa.py -h (for help)
    """)


def db_connect(db):
    """Function connecting to database"""
    global count_errors
    if os.path.exists(db):
        try:
            with sqlite3.connect(db) as conn:
                global cursor
                cursor = conn.cursor()
                cursor_rep = conn.cursor()
            print("msgstore.db connected\n")
            return cursor, cursor_rep
        except Exception as e:
            print(prefix_error + "Error connecting to database:", e)
            count_errors += 1
        return 0, 0
    else:
        print(prefix_fatal + "File 'msgstore.db' doesn't exist!")
        sys.exit(1)
        return 0, 0


def status(st):
    """Function message status"""
    if st == 0 or st == 5:  # 0 for me and 5 for target
        return "Received", "&#10004;&#10004;"
    elif st == 4:
        return Fore.RED + "Waiting in server" + Fore.RESET, "&#10004;"
    elif st == 6:
        return Fore.YELLOW + "System message" + Fore.RESET, "&#128187;"
    elif st == 8 or st == 10:
        return Fore.BLUE + "Audio played" + Fore.RESET, "<font color=\"#0000ff \">&#10004;&#10004;</font>"  # 10 for me and 8 for target
    elif st == 13 or st == 12:
        return Fore.BLUE + "Seen" + Fore.RESET, "<font color=\"#0000ff \">&#10004;&#10004;</font>"
    else:
        return str(st), ""


def size_file(obj):
    """Function objects size"""
    if obj > 1048576:
        obj = "(" + "{0:.2f}".format(obj / float(1048576)) + " MB)"
    else:
        obj = "(" + "{0:.2f}".format(obj / float(1024)) + " KB)"
    return obj


def duration_file(obj):
    """Function duration time"""
    hour = (int(obj / 3600))
    minu = int((obj - (hour * 3600)) / 60)
    seco = obj - ((hour * 3600) + (minu * 60))
    if obj >= 3600:
        obj = (str(hour) + "h " + str(minu) + "m " + str(seco) + "s")
    elif 60 < obj < 3600:
        obj = (str(minu) + "m " + str(seco) + "s")
    else:
        obj = (str(seco) + "s")
    return obj


def html_report_message(text):
    """Format a message for an HMTL report."""
    # Set custom emoji, if enabled.
    if settings['custom_emoji_enable']:
        text = custom_emoji(text)
    return text.replace("  ", "&nbsp;&nbsp;").replace("\r", "").replace("\n", "<br>\n")


def linkify(text):
    """Search for URLs in a text and replace them with links."""
    # Code found here:
    # https://stackoverflow.com/questions/1071191/detect-urls-in-a-string-and-wrap-with-a-href-tag
    # Improved regex pattern found here:
    # https://www.w3resource.com/python-exercises/re/python-re-exercise-42.php
    if settings['html_links_enable']:
        #URL_REGEX = re.compile(r'''((?:mailto:|ftp://|http[s]?://)[^ <>'"{}|\\^`[\]]*)''')
        URL_REGEX = re.compile(r'''((?:mailto:|ftp://|http[s]?://)(?:[a-zA-Z]|[0-9]|[$-_@.&+~#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)''')
        return URL_REGEX.sub(r'<a href="\1" target="_blank">\1</a>', text)
    else:
        return text


def custom_emoji(text):
    """Replace Unicode emoji in a text with custom emoji images."""
    global count_warnings
    emoji = []
    # White list emoji with code < u'\U00002000'.
    emoji_filter_whitelist = [
        u'\U00000023',  # E0.6 keycap: #
        u'\U0000002A',  # E2.0 keycap: *
        u'\U00000030', u'\U00000031', u'\U00000032', u'\U00000033', u'\U00000034',  # E0.6 keycap: 0..4
        u'\U00000035', u'\U00000036', u'\U00000037', u'\U00000038', u'\U00000039',  # E0.6 keycap: 5..9
        u'\U000000A9',  # E0.6 copyright
        u'\U000000AE']  # E0.6 registered
    # Search emoji in text.
    i = 0
    while i < len(text):
        # For faster processing: Skip scanning the whole emoji list, if the
        # current character is not potentially part of an emoji.
        if text[i] < u'\U00002000' and text[i] not in emoji_filter_whitelist:
            i += 1
            continue
        # Is the current sequence an emoji?
        seq_is_emo = False
        # Check for standard (i.e. Unicode) emoji listed in whaemoji.WHA_EMOJI.
        # The maximum emoji sequence length is 7, i.e. check the current
        # character in combination with up to the next 6 ones.
        for j in range(6, -1, -1):
            if i + j < len(text):
                # Improve performance (see above).
                if text[i+j] < u'\U00002000' and text[i+j] not in emoji_filter_whitelist:
                    continue
                seq = text[i:i+j+1]
                if seq in whaemoji.WHA_EMOJI:
                    seq_is_emo = True
                    i += j
                    break
        # In addition to the standard emoji, check for emoji codes used by
        # older WhatsApp versions. Known such codes are E001 ... E537. For
        # safety, the codes E000 ... EFFF are included.
        if text[i] >= u'\U0000E000' and text[i] < u'\U0000F000':
            seq_is_emo = True
        if seq_is_emo:
            emoji.append(seq)
        i += 1
    text_emo = ""
    for emo in emoji:
        # Assemble the complete emoji name.
        emoji_name = ""
        for char in emo:
            emoji_name += "{0:04X}-".format(ord(char))
        emoji_name = emoji_name.rstrip("-")
        # Set the name of the emoji image file.
        emoji_image_file = os.path.join("." + settings['custom_emoji_dir'].rstrip('\\/'), emoji_name + ".png")
        # Check if the emoji image file exists.
        if not os.path.isfile(emoji_image_file[1:]):
            if settings['debug_warnings_enable']:
                print(prefix_warning + "The emoji image file '" + emoji_image_file[1:] + "' does not exist!")
            count_warnings += 1
        # Assemble the HTML emoji image tag.
        emoji_image_tag = "<img src=\"" + emoji_image_file + "\" alt=\"" + emo + "\" height=\"" + settings['custom_emoji_size'] + "\" style=\"vertical-align:middle;\">"
        # Find position of the current emoji.
        emoji_pos = text.find(emo)
        # Add text and emoji to result string.
        text_emo += text[:emoji_pos] + emoji_image_tag
        # Remove processed characters from text.
        text = text[emoji_pos + len(emo):]
    text_emo += text
    return text_emo


def html_preview_file(file_name):
    """Create an HTML image tag for a preview picture with a fixed size from an image file."""
    return html_preview_file_size(file_name, int(settings['preview_pics_size']), int(settings['preview_pics_size']))


def html_preview_file_size(file_name, tag_width, tag_height):
    """Create an HTML image tag for a preview picture with a given size from an image file."""
    global count_errors
    try:
        # If the file does not exist, try adding the local path.
        if not os.path.isfile(file_name):
            file_name = os.path.abspath(os.path.join(local, file_name))
        image = Image.open(file_name)
        img_width, img_height = image.size
        # Only add the relative path for the "Media" direcotry where necessary.
        if os.path.relpath(file_name, local).startswith(media_rel_path):
            html_image_tag = "<img src=\"" + os.path.relpath(file_name, local)
        else:
            html_image_tag = "<img src=\"" + media_rel_path + os.path.relpath(file_name, local)
        if settings['html_img_alt_enable']:
            html_image_tag += "\" alt=\"" + file_name
        html_image_tag += "\" "
        # If the image is in portrait format, set a fixed width.
        if img_width < img_height:
            # Limit the maximum height to a reasonable value.
            tag_height_max = int(settings['preview_pics_max_height'])
            if (img_height / img_width) * tag_width > tag_height_max:
                html_image_tag += "height=\"{0:d}\"".format(tag_height_max)
            else:
                html_image_tag += "width=\"{0:d}\"".format(tag_width)
        # If the image is in landscape format, set a fixed height.
        else:
            # Limit the maximum width to avoid overflowing bubbles.
            tag_width_max = int(settings['preview_pics_max_width'])
            if (img_width / img_height) * tag_height > tag_width_max:
                html_image_tag += "width=\"{0:d}\"".format(tag_width_max)
            else:
                html_image_tag += "height=\"{0:d}\"".format(tag_height)
        html_image_tag += " onError=\"this.onerror=null; this.src='." + settings['html_img_noimage_pic'] + "';\"/>"
        return html_image_tag
    except Exception as e:
        if settings['debug_errors_enable']:
            print(prefix_error + "Cannot create HTML image tag for preview picture '" + file_name + "':", e)
        count_errors += 1
        # In case of an exception, return a default string.
        # Only add the relative path for the "Media" direcotry where necessary.
        if os.path.relpath(file_name, local).startswith(media_rel_path):
            img_src = os.path.relpath(file_name, local)
        else:
            img_src = media_rel_path + os.path.relpath(file_name, local)
        if settings['html_img_alt_enable']:
            return "<img src=\"" + img_src + "\" alt=\"" + file_name + "\" height=\"{0:d}\" onError=\"this.onerror=null; this.src='.".format(tag_height) + settings['html_img_noimage_pic'] + "';\"/>"
        return "<img src=\"" + img_src + "\" height=\"{0:d}\" onError=\"this.onerror=null; this.src='.".format(tag_height) + settings['html_img_noimage_pic'] + "';\"/>"


def profile_picture(group_id, user_id):
    """Check if a profile picture exists. If not, create a default one from a template. Return a profile picture string."""
    global count_warnings
    global count_errors
    # Strip the extension from the user and the group ID.
    group_id = group_id.strip("@g.us")
    user_id = user_id.strip("@s.whatsapp.net")
    # If both group_id and user_id are empty, return an empty string.
    if not group_id + user_id:
        return ""
    profile_picture_src_dir = settings['profile_pics_dir'].rstrip('\\/')
    profile_picture_out_dir = os.path.abspath(os.path.join(local, settings['profile_pics_dir'].rstrip('\\/')))
    profile_picture_src_file = os.path.abspath(os.path.join(profile_picture_src_dir, group_id + user_id + ".jpg"))
    profile_picture_out_file = os.path.abspath(os.path.join(profile_picture_out_dir, group_id + user_id + ".jpg"))
    # Group.
    if group_id:
        profile_picture_template = settings['profile_pic_group']
    else:
        profile_picture_template = settings['profile_pic_user']
    # Check if the profile picture output path exists. If not, create it.
    if not os.path.exists(profile_picture_out_dir):
        try:
            distutils.dir_util.mkpath(profile_picture_out_dir)
        except Exception as e:
            if settings['debug_errors_enable']:
                print(prefix_error + "Error creating the profile picture output directory '{0:s}': ".format(profile_picture_out_dir) + str(e))
            count_errors += 1
    # Check if the profile picture exists. If not, copy the default profile picture template.
    if not os.path.exists(profile_picture_src_file):
        if settings['debug_warnings_enable']:
            print(prefix_warning + "The profile picture file '{0:s}' does not exist.".format(profile_picture_src_file))
        count_warnings += 1
        if (os.path.isfile(profile_picture_template) and
            os.access(profile_picture_template, os.R_OK)):
            try:
                profile_picture_default = Image.open(profile_picture_template)
                profile_picture_default.save(profile_picture_out_file)
            except Exception as e:
                if settings['debug_errors_enable']:
                    print(prefix_error + "Error copying file '{0:s}' to '{1:s}': ".format(profile_picture_template, profile_picture_out_file) + str(e))
                count_errors += 1
        else:
            if settings['debug_warnings_enable']:
                print(prefix_warning + "The profile picture template file '{0:s}' is not readable.".format(profile_picture_template))
            count_warnings += 1
    # If the source profile picture exists, copy it to the output directory.
    else:
        try:
            profile_picture_img = Image.open(profile_picture_src_file)
            profile_picture_img.save(profile_picture_out_file)
        except Exception as e:
            if settings['debug_errors_enable']:
                print(prefix_error + "Error copying file '{0:s}' to '{1:s}': ".format(profile_picture_src_file, profile_picture_out_file) + str(e))
            count_errors += 1
    # Check if the profile picture finally exists.
    if not os.path.exists(profile_picture_out_file):
        if settings['debug_warnings_enable']:
            print(prefix_warning + "The profile picture file '{0:s}' does not exist.".format(profile_picture_out_file))
        count_warnings += 1
    return os.path.relpath(profile_picture_out_file, local)


def vcard_data_extract(vcard_data_bin):
    """Extract vCard data and contact names from binary data."""
    vcard_data = ""
    vcard_names = []
    vcards = str(vcard_data_bin).replace("\r", "").replace("\\n", "\n").split("BEGIN:VCARD")
    for vc in vcards[1:]:
        vcard_data += "BEGIN:VCARD"
        vcard_data += vc.split("END:VCARD")[0] + "END:VCARD\n"
        tmp = vc.split("\nFN:")
        if len(tmp) >= 2:
            tmp = tmp[1].split("\n")
            if tmp:
                vcard_names.append(tmp[0])
            else:
                vcard_names.append("")
        else:
            vcard_names.append("")
    return vcard_data.strip("\n"), vcard_names


def html_vcard_tooltip(vcard_data):
    """Create an HTML tooltip (title) for vCard data."""
    vcard_tooltip = ""
    if settings['contact_tooltip_enable']:
        # Raw vCard data as tooltip.
        if not settings['contact_tooltip_pretty']:
            vcard_tooltip = " title=\"" + html.escape(vcard_data).replace("\n", "&#10;") + "\""
        # Prettily formatted vCard data as tooltip.
        else:
            vcard_tooltip = " title=\"" + html.escape(vcard_format_pretty(vcard_data)).replace("\n", "&#10;") + "\""
    return vcard_tooltip


def vcard_format_pretty(vcard_data):
    """Format vCard data in a pretty way."""
    global count_errors
    vcard_pretty = ""
    try:
        vcards = list(filter(None, vcard_data.replace("END:VCARD", "").replace("=\n=", "=").split("BEGIN:VCARD")))
        for vc in vcards:
            vc_lines = list(filter(None, vc.strip("\n").split("\n")))
            for vc_line in vc_lines:
                vc_line = vc_line.strip(" \n\r")
                # Only split at the first ':'! This is important if the vCard
                # attributes contain another ':', like e.g. in URLs.
                vc_data = list(filter(None, vc_line.split(":", 1)))
                if len(vc_data) < 2:
                    continue
                vc_props = list(filter(None, vc_data[0].split(";")))
                if not vc_props:
                    continue
                # Properties.
                vc_prop = list(filter(None, vc_props[0].split(".")))[-1].upper()
                if vc_prop == "VERSION":
                    continue
                elif vc_prop == "N":
                    vcard_pretty += "Name"
                elif vc_prop == "FN":
                    vcard_pretty += "Full name"
                elif vc_prop == "ADR":
                    vcard_pretty += "Address"
                elif vc_prop == "BDAY":
                    vcard_pretty += "Birthday"
                elif vc_prop == "EMAIL":
                    vcard_pretty += "Email"
                elif vc_prop == "NOTE":
                    vcard_pretty += "Note"
                elif vc_prop == "TEL":
                    vcard_pretty += "Telephone"
                elif vc_prop == "URL":
                    vcard_pretty += "Website"
                else:
                    vcard_pretty += vc_prop
                # Property parameters.
                vc_prop_params = list(filter(None, vc_props[1:]))
                quoted_printable = False
                if vc_prop_params:
                    vcard_pretty += " ("
                    param_cnt = 0
                    for param in vc_prop_params:
                        if param:
                            param_cnt += 1
                            if param.upper().find("ENCODING=") >= 0 and param.upper().find("QUOTED-PRINTABLE") >= 0:
                                quoted_printable = True
                                continue
                            if param_cnt > 1:
                                vcard_pretty += ", "
                            vcard_pretty += param.lower()
                    vcard_pretty += ")"
                vcard_pretty += ": "
                # Attributes.
                vc_attributes = list(filter(None, vc_data[1].split(";")))
                if vc_attributes:
                    attr_cnt = 0
                    for attr in vc_attributes:
                        if attr:
                            attr_cnt += 1
                            if attr_cnt > 1:
                                vcard_pretty += ", "
                            if quoted_printable:
                                vcard_pretty += quopri.decodestring(attr).decode('utf-8')
                            else:
                                vcard_pretty += attr
                # End of line.
                vcard_pretty += "\n"
            # End of current vCard.
            vcard_pretty += "\n"
        # Remove last new line.
        vcard_pretty = vcard_pretty.rstrip("\n")
    except Exception as e:
        print("\n" + prefix_error + "Error in function 'vcard_format_pretty': " + str(e))
        count_errors += 1
    return vcard_pretty


def vcard_file_create(vcard_file_name, vcard_data):
    """Save vCard data to a vCard (*.vcf) file."""
    # Check if the contact vCard path exists. If not, create it.
    if not os.path.exists(os.path.dirname(vcard_file_name)):
        distutils.dir_util.mkpath(os.path.dirname(vcard_file_name))
    # Save vCard data to file.
    overwrite = True
    if not os.path.isfile(vcard_file_name) or overwrite:
        with open(vcard_file_name, 'wt') as vcard_file:
            if vcard_data:  # vCard data exist.
                vcard_file.write(vcard_data)
            else:           # Write an empty file, if no vCard data exist.
                vcard_file.write("")


def names(obj):
    """Function saves a name list if wa.db exists."""
    # global names_dict
    # names_dict = {}  # jid : display_name
    global count_warnings
    global count_errors
    if os.path.exists(obj):
        try:
            with sqlite3.connect(obj) as conn:
                cursor_name = conn.cursor()
                sql_names = "SELECT jid, display_name FROM wa_contacts"
                sql_names = cursor_name.execute(sql_names)
                print("wa.db connected")

                try:
                    for data in sql_names:
                        names_dict.update({data[0]: data[1]})
                except Exception as e:
                    print(prefix_error + "Error adding items in the dictionary:", e)
                    count_errors += 1
        except Exception as e:
            print(prefix_error + "Error connecting to database:", e)
            count_errors += 1
    else:
        print(prefix_warning + "File 'wa.db' database doesn't exist!")
        count_warnings += 1


def gets_name(obj, *args):
    """Function recover a name of the wa.db"""
    if names_dict == {}:  # No exists wa.db
        return " "
    else:  # Exists Wa.db
        #if type(obj) is list:  # It's a list
        if isinstance(obj, list):  # It's a list
            list_broadcast = []
            for i in obj:
                b = i + "@s.whatsapp.net"
                if b in names_dict:
                    if names_dict[b] is not None:
                        list_broadcast.append(names_dict[b])
                    else:
                        list_broadcast.append(i)
                else:
                    list_broadcast.append(i)
            if settings['custom_emoji_enable'] and not args and (report_var == 'EN' or report_var == 'ES' or report_var == 'DE'):
                return custom_emoji(" (" + ", ".join(list_broadcast) + ")")
            return " (" + ", ".join(list_broadcast) + ")"
        else:  # It's a string
            if obj in names_dict:
                if names_dict[obj] is not None:
                    if settings['custom_emoji_enable'] and not args and (report_var == 'EN' or report_var == 'ES' or report_var == 'DE'):
                        return custom_emoji(" (" + names_dict[obj] + ")")
                    return " (" + names_dict[obj] + ")"
                else:
                    return ""
            else:
                return ""


def participants(obj):
    """Function saves all participant in an group or broadcast"""
    sql_string_group = "SELECT jid, admin FROM group_participants WHERE gjid='" + str(obj) + "'"
    sql_consult_group = cursor.execute(sql_string_group)
    report_group = ""
    random.seed(0)  # For reproducible color assignment with 'random.choice(hexcolor)'.
    for i in sql_consult_group:
        if i[0]:  # Others
            hexcolor = ["#800000", "#00008B", "#006400", "#800080", "#8B4513", "#FF4500", "#2F4F4F", "#DC143C", "#696969", "#008B8B", "#D2691E", "#CD5C5C", "#4682B4"]
            color[i[0].split("@")[0]] = random.choice(hexcolor)
            global current_color
            current_color = color.get(i[0].split("@")[0])

            if i[1] and i[1] == 0:  # User
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    report_group += "<font color=\"{}\"> {} </font>, ".format(current_color, i[0].split("@")[0] + gets_name(i[0]))
                else:
                    report_group += i[0].split("@")[0] + " " + Fore.YELLOW + gets_name(i[0]) + Fore.RESET + ", "
            elif i[1] and i[1] > 0:  # Admin
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    report_group += "<font color=\"{}\"> {} </font> ***Admin***, ".format(current_color, i[0].split("@")[0] + gets_name(i[0]))

                else:
                    report_group += i[0].split("@")[0] + Fore.YELLOW + gets_name(i[0]) + Fore.RESET + Fore.RED + "(Admin)" + Fore.RESET + ", "
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    report_group += "<font color=\"{}\"> {} </font>, ".format(current_color, i[0].split("@")[0] + gets_name(i[0]))
                else:
                    report_group += i[0].split("@")[0] + " " + Fore.YELLOW + gets_name(i[0]) + Fore.RESET + ", "
        else:  # Me
            current_color = "#000000"
            if i[1] and i[1] == 0:  # User
                if report_var == 'EN':
                    report_group += "Phone user, "
                elif report_var == 'ES':
                    report_group += "Usuario del teléfono, "
                elif report_var == 'DE':
                    report_group += "Telefon-Benutzer, "
                else:
                    report_group += lang_en_me + ", "
            elif i[1] and i[1] > 0:  # Admin
                if report_var == 'EN':
                    report_group += "<font color=\"{}\"> Phone user </font> *** Admin ***, ".format(current_color)
                elif report_var == 'ES':
                    report_group += "<font color=\"{}\"> Usuario del teléfono </font> *** Admin ***, ".format(current_color)
                elif report_var == 'DE':
                    report_group += "<font color=\"{}\"> Telefon-Benutzer </font> *** Admin ***, ".format(current_color)
                else:
                    report_group += lang_en_me + Fore.RED + " (Admin)" + Fore.RESET + ", "
            else:  # Broadcast no user, no admin
                if report_var == 'EN':
                    report_group += "<font color=\"{}\"> Phone user </font>, ".format(current_color)
                elif report_var == 'ES':
                    report_group += "<font color=\"{}\"> Usuario del teléfono </font>, ".format(current_color)
                elif report_var == 'DE':
                    report_group += "<font color=\"{}\"> Telefon-Benutzer </font>, ".format(current_color)
                else:
                    report_group += lang_en_me + ", "

    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
        report_group = "<p style=\"border: 2px solid #CCCCCC; padding: 10px; background-color: #CCCCCC; color: black; font-family: arial,helvetica; font-size: 14px; font-weight: bold;\">" + report_group[:-2] + "</p>"

    return report_group, color


def report(obj, html, local):
    """Function that generates the report."""

    # Copia los estilos
#    os.makedirs(local + "cfg", exist_ok=True)

    rep_ini = """<!DOCTYPE html>
<html lang=""" + "\"" + report_var + "\"" + """>

<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="""
    rep_ini += "\""
    if report_var == 'ES':
        rep_ini += "Informe creado por"
    elif report_var == 'DE':
        rep_ini += "Bericht erstellt von"
    else:
        rep_ini += "Report created by"
    rep_ini += " WhatsApp Parser v" + version + """">
    <meta name="author" content="B16f00t">
    <link rel="shortcut icon" href="../images/logo.png">
    <title>WhatsApp Parser v""" + version + """ Report - """ + arg_group + gets_name(arg_group) + arg_user + gets_name(arg_user + "@s.whatsapp.net") + """</title>
    <!-- Custom styles for this template -->
    <link href="../cfg/chat.css" rel="stylesheet">
    <style>
    table {
        font-family: arial, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    td, th {
        border: 1px solid #000000;
        text-align: left;
        padding: 8px;
    }
    tr:nth-child(even) {
        background-color: #cdcdcd;
    }
    #map {
        height: 100px;
        width: 100%;
    }
    </style>
</head>

<body"""
    if settings['bg_report']:
        rep_ini += " background=\"." + settings['bg_report'] + "\""
    rep_ini += """>
    <!-- Fixed navbar -->
    <div class="container theme-showcase">
        <div class="header">"""
    if settings['logo']:
        rep_ini += """
            <h1 align="left"><img src=".""" + settings['logo']
        if settings['html_img_alt_enable']:
            rep_ini += "\" alt=\"." + settings['logo']
        rep_ini += "\" height=\"" + settings['logo_height'] + "\" align=\"center\" onError=\"this.onerror=null; this.src='." + settings['html_img_noimage_pic'] + "';\">&nbsp;" + settings['company'] + "</h1>"
    if settings['record'] + settings['unit'] + settings['examiner'] + settings['notes']:
        rep_ini += """
            <table style="width:100%">
                <tr>"""
        if report_var == 'ES':
            rep_ini += """
                    <th>Registro</th>
                    <th>Unidad / Compañia</th>
                    <th>Examinador</th>
                    <th>Fecha</th>"""
        elif report_var == 'DE':
            rep_ini += """
                    <th>Datensatz</th>
                    <th>Abteilung / Firma</th>
                    <th>Bearbeiter</th>
                    <th>Datum</th>"""
        else:
            rep_ini += """
                    <th>Record</th>
                    <th>Unit / Company</th>
                    <th>Examiner</th>
                    <th>Date</th>"""
        rep_ini += """
                </tr>
                <tr>
                    <td>""" + settings['record'] + """</td>
                    <td>""" + settings['unit'] + """</td>
                    <td>""" + settings['examiner'] + "</td>"
        if report_var == 'DE':
            rep_ini += """
                    <td>""" + time.strftime('%d.%m.%Y %H:%M:%S', time.localtime()) + "</td>"
        else:
            rep_ini += """
                    <td>""" + time.strftime('%d-%m-%Y %H:%M:%S', time.localtime()) + "</td>"
        rep_ini += """
                </tr>
                <tr>
                    <th colspan="4">"""
        if report_var == 'ES':
            rep_ini += "Observaciones"
        elif report_var == 'DE':
            rep_ini += "Bemerkungen"
        else:
            rep_ini += "Notes"
        rep_ini += """</th>
                </tr>
                <tr>
                    <td colspan="4">""" + settings['notes'] + """</td>
                </tr>
            </table>"""
        if settings['profile_pics_enable']:
            rep_ini += """
            <br>"""
    if settings['profile_pics_enable']:
        rep_ini += """
            <br>
            <table style="width:100%;">
                <tr>
                <td style="border:none; padding:0px;"></td>
                <td style="border:none; text-align:center; padding:0px; font-family:none; width:1%;">
                    <a href=""" + "\"" + media_rel_path + profile_picture(arg_group, arg_user) + "\"><img src=\"" + media_rel_path + profile_picture(arg_group, arg_user)
        if settings['html_img_alt_enable']:
            rep_ini += "\" alt=\"" + media_rel_path + profile_picture(arg_group, arg_user)
        rep_ini += "\" height=\"" + settings['profile_pics_size_report'] + """" align="right" style="padding-right:20px;" onError="this.onerror=null; this.src='.""" + settings['html_img_noimage_pic'] + """';"></a>
                </td>
                <td style="border:none; text-align:center; padding:0px; font-family:none; width:1%; white-space:nowrap;">
                    <h2 align=center>"""
        if report_var == 'ES':
            rep_ini += "Conversación"
        elif report_var == 'DE':
            rep_ini += "Chat"
        else:
            rep_ini += "Chat"
        rep_ini +="""</h2>
                    <h3 align=center>""" + arg_group + gets_name(arg_group) + arg_user + gets_name(arg_user + "@s.whatsapp.net") + """</h3>
                </td>
                <td style="border:none; padding:0px;"></td>
                </tr>
            </table>
            <br>"""
    else:
        rep_ini += """
            <h2 align=center>"""
        if report_var == 'ES':
            rep_ini += "Conversación"
        elif report_var == 'DE':
            rep_ini += "Chat"
        else:
            rep_ini += "Chat"
        rep_ini +="""</h2>
            <h3 align=center>""" + arg_group + gets_name(arg_group) + arg_user + gets_name(arg_user + "@s.whatsapp.net") + """</h3>"""
    if report_group:
        rep_ini += """
            """ + report_group
    rep_ini += """
        </div>
        <ul>"""

    rep_end = """
            <li>
                <div class="bubble_empty">
                </div>
            </li>
        </ul>
    </div><!-- /container -->
</body>
</html>
"""

    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local + html, 'w', encoding="utf-8", errors="ignore") as f:
        f.write(rep_ini + obj + rep_end)
        f.close()


def index_report(obj, html, local):
    """Function that makes the index report """
    rep_ini = """<!DOCTYPE html>
<html lang=""" + "\"" + report_var + "\"" + """>

<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="""
    rep_ini += "\""
    if report_var == 'ES':
        rep_ini += "Índice del informe creado por"
    elif report_var == 'DE':
        rep_ini += "Verzeichnis der Berichte erstellt von"
    else:
        rep_ini += "Report index created by"
    rep_ini += " WhatsApp Parser v" + version + """">
    <meta name="author" content="B16f00t">
    <link rel="shortcut icon" href="../images/logo.png">
    <title>WhatsApp Parser v""" + version + """ - Report Index</title>
    <!-- Custom styles for this template -->
    <link href="../cfg/chat.css" rel="stylesheet">
    <style>
    table {
        font-family: arial, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    td, th {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 8px;
    }
    tr:nth-child(even) {
        background-color: #dddddd;
    }
    #map {
        height: 100px;
        width: 100%;
    }
    </style>
</head>

<body"""
    if settings['bg_index']:
        rep_ini += " background=\"." + settings['bg_index'] + "\""
    rep_ini += """>
    <!-- Fixed navbar -->
    <div class="containerindex theme-showcase">"""
    if settings['logo']:
        rep_ini += """
        <h1 align="left"><img src=".""" + settings['logo']
        if settings['html_img_alt_enable']:
            rep_ini += "\" alt=\"." + settings['logo']
        rep_ini += "\" height=\"" + settings['logo_height'] + "\" align=\"center\" onError=\"this.onerror=null; this.src='." + settings['html_img_noimage_pic'] + "';\">&nbsp;" + settings['company'] + "</h1>"
    rep_ini += """
        <h2 align=center>"""
    if report_var == 'ES':
        rep_ini += "Listado de conversaciones"
    elif report_var == 'DE':
        rep_ini += "Liste der Chats"
    else:
        rep_ini += "Chats List"
    rep_ini += """</h2>
        <div class="header">
            <table style="width:100%">""" + obj + """
            </table>
        </div>
    </div><!-- /containerindex -->
</body>
</html>
"""

    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local + html, 'w', encoding="utf-8", errors="ignore") as f:
        f.write(rep_ini)
        f.close()


def reply(_id, local):
    """Function look out answer messages"""
    sql_reply_str = "SELECT key_remote_jid, key_from_me, key_id, status, data, timestamp, media_url, media_mime_type, media_wa_type, media_size, media_name, media_caption, media_duration, latitude, longitude, " \
                "remote_resource, edit_version, thumb_image, recipient_count, raw_data, starred, quoted_row_id, forwarded FROM messages_quotes WHERE _id = " + str(_id)
    sql_answer = cursor_rep.execute(sql_reply_str)
    rep = sql_answer.fetchone()
    ans = ""
    reply_msg = ""
    if rep is not None:  # Message not deleted
        if (str(rep[0]).split('@'))[1] == "g.us":
            if int(rep[1]) == 1:  # I post a message in a group
                if report_var == 'EN':
                    reply_msg = "<font color=\"#FF0000\">" + lang_en_me + "</font>"
                elif report_var == 'ES':
                    reply_msg = "<font color=\"#FF0000\">" + lang_es_me + "</font>"
                elif report_var == 'DE':
                    reply_msg = "<font color=\"#FF0000\">" + lang_de_me + "</font>"
                else:
                    ans = lang_en_me
            elif int(rep[1]) == 0:  # Somebody post a message in a group
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg = "<font color=\"#FF0000\">" + (str(rep[15]).split('@'))[0] + gets_name(rep[15]) + "</font>"
                else:
                    ans = (str(rep[15]).split('@'))[0] + gets_name(rep[15])
        elif (str(rep[0]).split('@'))[1] == "s.whatsapp.net":
            if int(rep[1]) == 1:  # I send message to somebody
                if report_var == 'EN':
                    reply_msg = "<font color=\"#FF0000\">" + lang_en_me + "</font>"
                elif report_var == 'ES':
                    reply_msg = "<font color=\"#FF0000\">" + lang_es_me + "</font>"
                elif report_var == 'DE':
                    reply_msg = "<font color=\"#FF0000\">" + lang_de_me + "</font>"
                else:
                    ans = lang_en_me
            elif int(rep[1]) == 0:  # Someone sends me a message
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg = "<font color=\"#FF0000\">" + (str(rep[0]).split('@'))[0] + gets_name(rep[0]) + "</font>"
                else:
                    ans = (str(rep[0]).split('@'))[0] + gets_name(rep[0])
        elif str(rep[0]) == "status@broadcast":
            status_dir = os.path.abspath(os.path.join(local, "./Media/.Statuses"))
            if os.path.isfile(status_dir) is False:
                distutils.dir_util.mkpath(status_dir)
                if int(rep[1]) == 1:  # I post a Status
                    if report_var == 'EN':
                        reply_msg = "<font color=\"#FF0000\">" + lang_en_me + "</font>"
                    elif report_var == 'ES':
                        reply_msg = "<font color=\"#FF0000\">" + lang_es_me + "</font>"
                    elif report_var == 'DE':
                        reply_msg = "<font color=\"#FF0000\">" + lang_de_me + "</font>"
                    else:
                        ans = lang_en_me
                elif int(rep[1]) == 0:  # Somebody posts a Status
                    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                        reply_msg = "<font color=\"#FF0000\">" + (str(rep[15]).split('@'))[0] + gets_name(rep[15]) + "</font>"
                    else:
                        ans = (str(rep[15]).split('@'))[0] + gets_name(rep[15])

        if rep[22] and int(rep[22]) > 0:  # Forwarded
            if int(rep[22]) < 5:
                if report_var == 'EN':
                    reply_msg += "<br><font color=\"#8b8878\">&#10150; Forwarded</font>"
                elif report_var == 'ES':
                    reply_msg += "<br><font color=\"#8b8878\">&#10150; Reenviado</font>"
                elif report_var == 'DE':
                    reply_msg += "<br><font color=\"#8b8878\">&#10150; Weitergeleitet</font>"
                else:
                    ans += Fore.GREEN + " - Forwarded" + Fore.RESET + "\n"
            else:
                if report_var == 'EN':
                    reply_msg += "<font color=\"#8b8878\" >&#10150;&#10150; Forwarded many times</font><br>"
                elif report_var == 'ES':
                    reply_msg += "<font color=\"#8b8878\" >&#10150;&#10150; Reenviado muchas veces</font><br>"
                elif report_var == 'DE':
                    reply_msg += "<br><font color=\"#8b8878\">&#10150; Häufig weitergeleitet</font>"
                else:
                    ans += Fore.RED + "Forwarded many times" + Fore.RESET + "\n"

        if int(rep[8]) == 0:  # media_wa_type 0, text message
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                reply_msg += "<br>" + html.escape(rep[4])
            else:
                ans += Fore.RED + " - Message: " + Fore.RESET + rep[4]

        elif int(rep[8]) == 1:  # media_wa_type 1, Image
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # Image doesn't exist
                thumb = local + "Media/WhatsApp Images/IMG-" + str(rep[2]) + "-NotDownloaded.jpg"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                if thumb != "Not downloaded":
                    thumb = local + thumb[2:]

                if os.path.isfile(thumb) is False:
                    distutils.dir_util.mkpath(local + "Media/WhatsApp Images")
                    if rep[19]:  # raw_data exists
                        with open(thumb, 'wb') as profile_file:
                            profile_file.write(rep[19])
            if rep[11]:  # media_caption
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local) + " - " + html.escape(rep[11])
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + Fore.RED + " - Caption: " + Fore.RESET + rep[11] + "\n"
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local)
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + "\n"
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                number = thumb.rfind("Media/WhatsApp Images/")
#                thumb = thumb[number - 1:].replace("\\", "/")
                thumb = os.path.relpath(thumb, local)
                reply_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb) + "</a>"

        elif int(rep[8]) == 2:  # media_wa_type 2, Audio
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # Image doesn't exist
                thumb = "Not downloaded"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                reply_msg += "<br>" + thumb + " " + size_file(rep[9]) + " - " + duration_file(rep[12]) + "<br><audio controls><source src=\"." + thumb + "\" type=\"" + rep[7] + "\"></audio>"
            else:
                ans += Fore.RED + " - Name: " + Fore.RESET + thumb + "\n"
                ans += Fore.RED + "Type: " + Fore.RESET + rep[7] + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + Fore.RED + " - Duration: " + Fore.RESET + duration_file(rep[12]) + "\n"

        elif int(rep[8]) == 3:  # media_wa_type 3 Video
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # Video doesn't exist
                thumb = local + "Media/WhatsApp Video/VID-" + str(rep[2]) + "-NotDownloaded.mp4"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                if rep[19]:  # raw_data exists
                    if thumb != "Not downloaded":
                        thumb = local + thumb[2:]

                    if os.path.isfile(thumb) is False:
                        distutils.dir_util.mkpath(local + "Media/WhatsApp Video")
                        with open(thumb, 'wb') as profile_file:
                            profile_file.write(rep[19])
                    # Save separate thumbnail image for video content.
                    if os.path.isfile(thumb + ".jpg") is False:
                        distutils.dir_util.mkpath(local + "Media/WhatsApp Video")
                        with open(thumb + ".jpg", 'wb') as profile_file:
                            profile_file.write(rep[19])
            if rep[11]:  # media_caption
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local) + " - " + html.escape(rep[11])
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + Fore.RED + " - Caption: " + Fore.RESET + rep[11] + "\n"
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local)
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + "\n"
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                number = thumb.rfind("Media/WhatsApp Video/")
#                thumb = thumb[number - 1:].replace("\\", "/")
                thumb = os.path.relpath(thumb, local)
                reply_msg += " " + size_file(rep[9]) + " - " + duration_file(rep[12])
                reply_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"
            else:
                ans += Fore.RED + "Type: " + Fore.RESET + rep[7] + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + Fore.RED + " - Duration: " + Fore.RESET + duration_file(rep[12]) + "\n"

        elif int(rep[8]) == 4:  # media_wa_type 4, Contact
            vcard_data, vcard_names = vcard_data_extract(rep[4])
            vcard_tooltip = html_vcard_tooltip(vcard_data)
            if settings['contact_vcard_dir']:
                vcard_file_name = os.path.abspath(os.path.join(local, settings['contact_vcard_dir'], arg_group + arg_user + "-" + rep[2] + ".vcf"))
                vcard_file_create(vcard_file_name, vcard_data)
                vcard_file_name = media_rel_path + os.path.relpath(vcard_file_name, local)
                if report_var == 'EN':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contact vCard</a>"
                elif report_var == 'ES':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contacto vCard</a>"
                elif report_var == 'DE':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Kontakt vCard</a>"
                else:
                    ans += Fore.GREEN + "Name: " + Fore.RESET + rep[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"
            else:
                if report_var == 'EN':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Contact vCard"
                elif report_var == 'ES':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Contacto vCard"
                elif report_var == 'DE':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Kontakt vCard"
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + rep[10] + Fore.RED + " - Type:" + Fore.RESET + " Contact vCard\n"

        elif int(rep[8]) == 5:  # media_wa_type 5, Location
            if rep[6]:  # media_url exists
                if rep[10]:  # media_name exists
                    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                        reply_msg += "<br>" + html.escape(rep[6]) + " - " + html.escape(rep[10]) + "<br>"
                    else:
                        ans += Fore.RED + " - Url: " + Fore.RESET + rep[6] + Fore.RED + " - Name: " + Fore.RESET + rep[10] + "\n"
                else:
                    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                        reply_msg += "<br>" + html.escape(rep[6]) + "<br>"
                    else:
                        ans += Fore.RED + " - Url: " + Fore.RESET + rep[6] + "\n"
            else:
                if rep[10]:
                    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                        reply_msg += "<br>" + html.escape(rep[10]) + "<br>"
                    else:
                        ans += Fore.RED + " - Name: " + Fore.RESET + rep[10] + "\n"
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                reply_msg += "<br><iframe width=\"300\" height=\"150\" id=\"gmap_canvas\" src=\"https://maps.google.com/maps?q={}%2C{}&t=&z=15&ie=UTF8&iwloc=&output=embed\" frameborder=\"0\" scrolling=\"no\" marginheight=\"0\" marginwidth=\"0\"></iframe>".format(str(rep[13]), str(rep[14]))
            else:
                ans += Fore.RED + "Type: " + Fore.RESET + "Location" + Fore.RED + " - Lat: " + Fore.RESET + str(rep[13]) + Fore.RED + " - Long: " + Fore.RESET + str(rep[14]) + "\n"

        elif int(rep[8]) == 8:  # media_wa_type 8, Audio / Video Call
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                reply_msg += "<br>" + "&#128222; " + str(rep[11]).capitalize() + " " + duration_file(rep[12])
            else:
                ans += Fore.RED + " - Call :" + Fore.RESET + str(rep[11]).capitalize() + Fore.RED + " - Duration: " + Fore.RESET + duration_file(rep[12]) + "\n"

        elif int(rep[8]) == 9:  # media_wa_type 9, Application
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # App doesn't exist
                thumb = local + "Media/WhatsApp Documents/DOC-" + str(rep[2]) + "-NotDownloaded"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                if thumb != "Not downloaded":
                    thumb = local + thumb[2:]

                if os.path.isfile(thumb) is False:
                    distutils.dir_util.mkpath(local + "Media/WhatsApp Documents")
                    if rep[19]:  # raw_data exists
                        with open(thumb +"jpg", 'wb') as profile_file:
                            profile_file.write(rep[19])
            if rep[11]:  # media_caption
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local) + " - " + html.escape(rep[11])
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + Fore.RED + " - Caption: " + Fore.RESET + rep[11] + "\n"
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local)
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + "\n"
            if rep[12] >= 0:
                if report_var == 'EN':
                    reply_msg += " " + size_file(rep[9]) + " - " + str(rep[12]) + " pages"
                elif report_var == 'ES':
                    reply_msg += " " + size_file(rep[9]) + " - " + str(rep[12]) + " páginas"
                elif report_var == 'DE':
                    reply_msg += " " + size_file(rep[9]) + " - " + str(rep[12]) + " Seiten"
                else:
                    ans += Fore.RED + "Type: " + Fore.RESET + rep[7] + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + Fore.RED + " - Pages: " + Fore.RESET + str(rep[12]) + "\n"
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += " " + size_file(rep[9])
                else:
                    ans += Fore.RED + "Type: " + Fore.RESET + rep[7] + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + "\n"
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                number = thumb.rfind("Media/WhatsApp Documents/")
#                thumb = thumb[number - 1:].replace("\\", "/")
                thumb = os.path.relpath(thumb, local)
                reply_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"

        elif int(rep[8]) == 10:  # media_wa_type 10, Video/Audio call lost
            reply_msg_call = ""
            if rep[11]:
                reply_msg_call = str(rep[11]).capitalize() + " "
            if report_var == 'EN':
                reply_msg += "<br>" + "&#128222; Missed " + reply_msg_call + "call."
            elif report_var == 'ES':
                reply_msg += "<br>" + "&#128222; " + reply_msg_call + "llamada perdida."
            elif report_var == 'DE':
                reply_msg += "<br>" + "&#128222; Verpasster " + reply_msg_call + "Anruf."
            else:
                ans += Fore.RED + " - Message: " + Fore.RESET + "Missed " + reply_msg_call + "call\n"

        elif int(rep[8]) == 13:  # media_wa_type 13 Gif
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # GIF doesn't exist
                thumb = local + "Media/WhatsApp Animated Gifs/VID-" + str(rep[2]) + "-NotDownloaded.mp4"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                if thumb != "Not downloaded":
                    thumb = local + thumb[2:]

                if os.path.isfile(thumb) is False:
                    distutils.dir_util.mkpath(local + "Media/WhatsApp Animated Gifs")
                    if rep[19]:  # raw_data exists
                        with open(thumb, 'wb') as profile_file:
                            profile_file.write(rep[19])
                # Save separate thumbnail image for video content.
                if os.path.isfile(thumb + ".jpg") is False:
                    distutils.dir_util.mkpath("./Media/WhatsApp Animated Gifs")
                    if rep[19]:  # raw_data exists
                        with open(thumb + ".jpg", 'wb') as profile_file:
                            profile_file.write(rep[19])

            if rep[11]:  # media_caption
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local) + " - " + html.escape(rep[11])
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + Fore.RED + " - Caption: " + Fore.RESET + rep[11] + "\n"
            else:
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    reply_msg += "<br>" + "./" + os.path.relpath(thumb, local)
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + thumb + "\n"

            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                number = thumb.rfind("Media/WhatsApp Animated Gifs/")
#                thumb = thumb[number - 1:].replace("\\", "/")
                thumb = os.path.relpath(thumb, local)
                reply_msg += " - Gif - " + size_file(rep[9]) + " " + duration_file(rep[12]) + "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"
            else:
                ans += Fore.RED + "Type: " + Fore.RESET + "Gif" + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + Fore.RED + " - Duration: " + Fore.RESET + duration_file(rep[12]) + "\n"

        elif int(rep[8]) == 14:  # Vcard Multiple
            vcard_data, vcard_names = vcard_data_extract(rep[19])
            vcard_tooltip = html_vcard_tooltip(vcard_data)
            if settings['contact_vcard_dir']:
                vcard_file_name = os.path.abspath(os.path.join(local, settings['contact_vcard_dir'], arg_group + arg_user + "-" + rep[2] + ".vcf"))
                vcard_file_create(vcard_file_name, vcard_data)
                vcard_file_name = media_rel_path + os.path.relpath(vcard_file_name, local)
                vcard_names_html = ''.join(["<br>" + html.escape(str(vc_name)) for vc_name in vcard_names])
                if report_var == 'EN':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contact vCard:" + vcard_names_html + "</a>"
                elif report_var == 'ES':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contacto vCard:</br></a>" + vcard_names_html
                elif report_var == 'DE':
                    reply_msg += html.escape(rep[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Kontakt vCard:</br></a>" + vcard_names_html
                else:
                    ans += Fore.GREEN + "Name: " + Fore.RESET + rep[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"
            else:
                if report_var == 'EN':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Contact vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                elif report_var == 'ES':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Contacto vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                elif report_var == 'DE':
                    reply_msg += "<br>" + html.escape(rep[10]) + "<br>&#9742; Kontakt vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                else:
                    ans += Fore.RED + " - Name: " + Fore.RESET + rep[10] + Fore.RED + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"

        elif int(rep[8]) == 15:  # media_wa_type 15, Deleted Object
            if int(rep[16]) == 5:  # edit_version 5, deleted for me
                if report_var == 'EN':
                    reply_msg += "<br>" + "Message deleted for me."
                elif report_var == 'ES':
                    reply_msg += "<br>" + "Mensaje eliminado para mí."
                elif report_var == 'DE':
                    reply_msg += "<br>" + "Nachricht für mich gelöscht."
                else:
                    ans += Fore.RED + " - Message: " + Fore.RESET + "Message deleted for me.\n"

            elif int(rep[16]) == 7:  # edit_version 7, deleted for all
                if report_var == 'EN':
                    reply_msg += "<br>" + "Message deleted for all participants."
                elif report_var == 'ES':
                    reply_msg += "<br>" + "Mensaje eliminado para todos los destinatarios."
                elif report_var == 'DE':
                    reply_msg += "<br>" + "Nachricht für alle Teilnehmer gelöscht."
                else:
                    ans += Fore.RED + " - Message: " + Fore.RESET + "Message deleted for all participants.\n"

        elif int(rep[8]) == 16:  # media_wa_type 16, Share location
            caption = ""
            if rep[11]:
                caption = " - " + rep[11]
            if report_var == 'EN':
                reply_msg += "<br>" + "Real time location (" + str(rep[13]) + ", " + str(rep[14]) + ")" + html.escape(caption) + "\n"
#                reply_msg += " <br><a href=\"https://www.google.es/maps/search/(" + str(rep[13]) + "," + str(rep[14]) + ")\" target=\"_self\"><img src=\"https://maps.google.com/maps/api/staticmap?center=" + str(rep[13]) + "," + str(rep[14]) + "&zoom=16&size=300x150&markers=size:mid|color:red|label:A|" + str(rep[13]) + "," + str(rep[14]) + "&sensor=false\"/></a>"
            elif report_var == 'ES':
                reply_msg += "<br>" + "Ubicación en tiempo real (" + str(rep[13]) + ", " + str(rep[14]) + ")" + html.escape(caption) + "\n"
            elif report_var == 'DE':
                reply_msg += "<br>" + "Live-Standort (" + str(rep[13]) + ", " + str(rep[14]) + ")" + html.escape(caption) + "\n"
            else:
                ans += Fore.RED + " - Type: " + Fore.RESET + "Real time location " + Fore.RED + "- Caption: " + Fore.RESET + caption + Fore.RED + " - Lat: " + Fore.RESET + str(rep[13]) + Fore.RED + " - Long: " + Fore.RESET + str(rep[14]) + Fore.RED + " - Duration: " + Fore.RESET + duration_file(rep[12]) + "\n"

            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                reply_msg += "<br><iframe width=\"300\" height=\"150\" id=\"gmap_canvas\" src=\"https://maps.google.com/maps?q={}%2C{}&t=&z=15&ie=UTF8&iwloc=&output=embed\" frameborder=\"0\" scrolling=\"no\" marginheight=\"0\" marginwidth=\"0\"></iframe>".format(str(rep[13]), str(rep[14]))

        elif int(rep[8]) == 20:  # media_wa_type 20 Sticker
            chain = rep[17].split(b'\x77\x02')[0]
            i = chain.rfind(b"Media/")
            b = len(chain)
            if i == -1:  # Sticker doesn't exist
                thumb = "Not downloaded"
            else:
                thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                number = thumb.rfind("Media/WhatsApp Stickers/")
#                thumb = thumb[number - 1:].replace("\\", "/")
                thumb = os.path.abspath(os.path.join(local, thumb))     # The sticker path from the WhatsApp database is relative!
                thumb = os.path.relpath(thumb, local)
                reply_msg += "<br>" + "Sticker - " + size_file(rep[9]) + "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb) + "</a>"
            else:
                ans += Fore.RED + " - Type: " + Fore.RESET + "Sticker" + Fore.RED + " - Size: " + Fore.RESET + str(rep[9]) + " bytes " + size_file(rep[9]) + Fore.RED + "\n"

        else:  # Deleted Message
            if report_var == 'EN':
                reply_msg = "<br>" + "Deleted message."
            elif report_var == 'ES':
                reply_msg = "<br>" + "Mensaje eliminado."
            elif report_var == 'DE':
                reply_msg = "<br>" + "Nachricht gelöscht."
            else:
                ans += " - Deleted message"

    return ans, reply_msg


def messages(consult, rows, report_html, local):
    """Function that show database messages"""
    global count_errors
    try:
        n_mes = 0
        rep_med = ""  # Saves the complete chat

        if arg_group and report_var == "None":
            print(Fore.RED + "Participants" + Fore.RESET)
            print(report_group)

        for data in consult:
            try:
                report_msg = ""   # Saves each message
                report_name = ""  # Saves the chat sender
                message = ""      # Saves each msg
                sys.stdout.write("\rMessage {}/{} - ID {}".format(str(n_mes+1), str(rows), str(data[23])))
                sys.stdout.flush()

                if int(data[8]) != -1:   # media_wa_type -1 "Start DB"
                    # Groups
                    if (str(data[0]).split('@'))[1] == "g.us":
                        if int(data[1]) == 1:
                            if int(data[3]) == 6:  # Group System Message
                                if report_var == 'EN':
                                    report_name = lang_en_sys_msg
                                elif report_var == 'ES':
                                    report_name = lang_es_sys_msg
                                elif report_var == 'DE':
                                    report_name = lang_de_sys_msg
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + data[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"
                            else:  # I send message to a group
                                if report_var == 'EN':
                                    report_name = lang_en_me
                                elif report_var == 'ES':
                                    report_name = lang_es_me
                                elif report_var == 'DE':
                                    report_name = lang_de_me
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + lang_en_me + Fore.GREEN + " to " + Fore.RESET + data[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"
                        elif int(data[1]) == 0:  # Somebody post a message in a group
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                current_color = color.get((str(data[15]).split('@'))[0])
                                if not current_color:
                                    current_color = "#5586e5"
                                report_name = "<font color=\"{}\"> {} </font>".format(current_color, (str(data[15]).split('@'))[0] + gets_name(data[15]))
                            else:
                                message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                message += Fore.GREEN + "From " + Fore.RESET + data[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + Fore.GREEN + ", participant " + Fore.RESET + (str(data[15]).split('@'))[0] + " " + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + "\n"
                    # Users
                    elif (str(data[0]).split('@'))[1] == "s.whatsapp.net":
                        if data[15] and (str(data[15]).split('@'))[1] == "broadcast":
                            if int(data[1]) == 1:  # I send to somebody message by broadcast
                                if report_var == 'EN':
                                    report_name = "&#128227; " + lang_en_me
                                elif report_var == 'ES':
                                    report_name = "&#128227; " + lang_es_me
                                elif report_var == 'DE':
                                    report_name = "&#128227; " + lang_de_me
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From" + Fore.RESET + " " + lang_en_me + Fore.GREEN + " to " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET +  Fore.GREEN + " by broadcast" + Fore.RESET + "\n"
                            elif int(data[1]) == 0:  # Someone sends me a message by broadcast

                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_name = "&#128227;" + (str(data[0]).split('@'))[0] + gets_name(data[0])
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + Fore.GREEN + " to" + Fore.RESET + " " + lang_en_me + Fore.GREEN + " by broadcast" + Fore.RESET + "\n"
                        else:
                            if int(data[1]) == 1:
                                if int(data[3]) == 6:  # User system message
                                    if report_var == 'EN':
                                        report_name = lang_en_sys_msg
                                    elif report_var == 'ES':
                                        report_name = lang_es_sys_msg
                                    elif report_var == 'DE':
                                        report_name = lang_de_sys_msg
                                    else:
                                        message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                        message += Fore.GREEN + "From " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"
                                else:  # I send message to someone
                                    if report_var == 'EN':
                                        report_name = lang_en_me
                                    elif report_var == 'ES':
                                        report_name = lang_es_me
                                    elif report_var == 'DE':
                                        report_name = lang_de_me
                                    else:
                                        message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                        message += Fore.GREEN + "From" + Fore.RESET + " " + lang_en_me + Fore.GREEN + " to " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"
                            elif int(data[1]) == 0:  # Someone sends me a message
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_name = (str(data[0]).split('@'))[0] + gets_name(data[0])
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + Fore.GREEN + " to" + Fore.RESET + " " + lang_en_me + "\n"
                    # Broadcast and Status
                    elif (str(data[0]).split('@'))[1] == "broadcast":
                        # Status
                        if str(data[0]) == "status@broadcast":
                            status_dir = os.path.abspath(os.path.join(local, "./Media/.Statuses"))
                            if os.path.isfile(status_dir) is False:
                                distutils.dir_util.mkpath(status_dir)
                            if int(data[1]) == 1:  # I post a Status
                                if report_var == 'EN':
                                    report_name = lang_en_me
                                elif report_var == 'ES':
                                    report_name = lang_es_me
                                elif report_var == 'DE':
                                    report_name = lang_de_me
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + lang_en_me + " - Post status" + "\n"
                            elif int(data[1]) == 0:  # Somebody posts a Status
                                if report_var == 'EN':
                                    report_name = "Posts Status - " + (str(data[15]).split('@'))[0] + gets_name(data[15])
                                elif report_var == 'ES':
                                    report_name = "Publica Estado - " + (str(data[15]).split('@'))[0] + gets_name(data[15])
                                elif report_var == 'DE':
                                    report_name = "Status veröffentlicht - " + (str(data[15]).split('@'))[0] + gets_name(data[15])
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + (str(data[15]).split('@'))[0] + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + Fore.GREEN + " posts status" + Fore.RESET + "\n"
                        # Broadcast
                        else:
                            if int(data[3]) == 6:  # Broadcast system message
                                if report_var == 'EN':
                                    report_name = lang_en_sys_msg
                                elif report_var == 'ES':
                                    report_name = lang_es_sys_msg
                                elif report_var == 'DE':
                                    report_name = lang_de_sys_msg
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From " + Fore.RESET + (str(data[0]).split('@'))[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"
                            else:  # I send a message to a broadcast list
                                list_broadcast = (str(data[15])).replace(',', '').split('@s.whatsapp.net')
                                list_copy = []
                                for i in list_broadcast:
                                    list_copy.append(i + " " + Fore.YELLOW +  gets_name(i + "@s.whatsapp.net") + Fore.RESET)
                                list_copy.pop()
                                list_copy = ", ".join(list_copy)

                                if report_var == 'EN':
                                    report_name = "&#128227; " + lang_en_me
                                elif report_var == 'ES':
                                    report_name = "&#128227; " + lang_es_me
                                elif report_var == 'DE':
                                    report_name = "&#128227; " + lang_de_me
                                else:
                                    message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"
                                    message += Fore.GREEN + "From" + Fore.RESET + " " + lang_en_me + Fore.GREEN + " to " + Fore.RESET + list_copy + " " + Fore.YELLOW + gets_name(list_copy) + Fore.RESET + Fore.GREEN + " by broadcast" + Fore.RESET + "\n"

                    if int(data[8]) == 0:  # media_wa_type 0, text message
                        if int(data[3]) == 6:  # Status 6, system message
                            if data[9] == 1:  # if media_size value change
                                if data[17]:    # The subject was changed from an existing one to a new one.
                                    if report_var == 'EN':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " changed the subject from \"" + html.escape(data[17][7:].decode('UTF-8', 'ignore')) + "\" to \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'ES':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " cambió el asunto de \"" + html.escape(data[17][7:].decode('UTF-8', 'ignore')) + "\" a \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'DE':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat den Betreff von \"" + html.escape(data[17][7:].decode('UTF-8', 'ignore')) + "\" zu \"" + html.escape(data[4]) + "\" geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the subject from \"" + data[17][7:].decode('UTF-8', 'ignore') + "\" to \"" + data[4] + "\".\n"
                                else:           # The subject was changed from an empty one to a new one.
                                    if report_var == 'EN':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " changed the subject to \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'ES':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " cambió el asunto a \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'DE':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat den Betreff zu \"" + html.escape(data[4]) + "\" geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the subject to \"" + data[4] + "\".\n"

                            elif data[9] == 4:
                                if report_var == 'EN':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " was added to the group."
                                elif report_var == 'ES':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " fue añadido al grupo."
                                elif report_var == 'DE':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " wurde hinzugefügt."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " was added to the group.\n"

                            elif data[9] == 5:
                                if report_var == 'EN':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " left the group."
                                elif report_var == 'ES':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " dejó el grupo."
                                elif report_var == 'DE':
                                    report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat die Gruppe verlassen."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " left the group.\n"

                            elif data[9] == 6:
                                if data[17]:
                                    if len(data[17].split(b'\xFF\xD8\xFF\xE0')) >= 2:   # The group icon was changed.
                                        if report_var == 'EN':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " changed the group icon."
                                        elif report_var == 'ES':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " cambió el icono del grupo."
                                        elif report_var == 'DE':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat das Gruppenbild geändert."
                                        else:
                                            message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the group icon.\n"
                                            message += "The last picture is stored on the phone path '/data/data/com.whatsapp/cache/Profile Pictures/" + (data[0].split('@'))[0] + ".jpg'\n"

                                        file_created = local + "Media/WhatsApp Profile Pictures/" + (data[0].split('@'))[0] + "-" + str(data[2]) + ".jpg"
                                        if os.path.isfile(file_created) is False:
                                            distutils.dir_util.mkpath(local + "Media/WhatsApp Profile Pictures")
                                            thumb = data[17].split(b'\xFF\xD8\xFF\xE0')[1]
                                            with open(file_created, 'wb') as profile_file:
                                                profile_file.write(b'\xFF\xD8\xFF\xE0' + thumb)

                                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                            report_msg += "<br>./Media/WhatsApp Profile Pictures/" + (data[0].split('@'))[0] + "-" + str(data[2]) + ".jpg"
                                            report_msg += "<br><a href=\"" + media_rel_path + "Media/WhatsApp Profile Pictures/" + (data[0].split('@'))[0] + "-" + str(data[2]) + ".jpg\" target=\"_self\">" + \
                                                html_preview_file("./Media/WhatsApp Profile Pictures/" +  (data[0].split('@'))[0] + "-" + str(data[2]) + ".jpg") + "</a>"
                                        else:
                                            message += "Thumbnail stored on local path './Media/WhatsApp Profile Pictures/" + (data[0].split('@'))[0] + "-" + ".jpg'\n"
                                    else:   # The group icon was deleted.
                                        if report_var == 'EN':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " deleted the group icon."
                                        elif report_var == 'ES':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " borró el icono del grupo."
                                        elif report_var == 'DE':
                                            report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat das Gruppenbild gelöscht."
                                        else:
                                            message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " deleted the group icon.\n"
                                else:   # A new group icon was set.
                                    if report_var == 'EN':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " changed the group icon."
                                    elif report_var == 'ES':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " cambió el icono del grupo."
                                    elif report_var == 'DE':
                                        report_msg += str(data[15].strip("@s.whatsapp.net")) + gets_name(data[15]) + " hat das Gruppenbild geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the group icon.\n"

                            elif data[9] == 7:
                                if report_var == 'EN':
                                    report_msg += " Removed " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " from the list."
                                elif report_var == 'ES':
                                    report_msg += " Removío " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " de la lista."
                                elif report_var == 'DE':
                                    report_msg += " Entferne " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " von der Liste."
                                else:
                                    message += Fore.GREEN + "Message:" + Fore.RESET + " Removed " + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " from the list.\n"

                            elif data[9] == 9:
                                list_broadcast = (str(data[17][58:]).split("\\x00\\x1a"))[1:]
                                list_copy = []
                                for i in list_broadcast:
                                    list_copy.append(i.split("@")[0] + gets_name(i.split("@")[0] + "@s.whatsapp.net"))

                                if report_var == 'EN':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " created a broadcast list with " + ", ".join(list_copy) + " recipients."
                                elif report_var == 'ES':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " creó una lista de difusión con " + ", ".join(list_copy) + " destinatarios."
                                elif report_var == 'DE':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat eine Broadcast-Liste mit " + ", ".join(list_copy) + " Empfängern erstellt."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " created a broadcast list with " + ", ".join(list_copy) + " recipients.\n"

                            elif data[9] == 10:
                                if report_var == 'EN':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " changed to " + (data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + gets_name((data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + "@s.whatsapp.net.")
                                elif report_var == 'ES':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " cambió a " + (data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + gets_name((data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + "@s.whatsapp.net.")
                                elif report_var == 'DE':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat zu " + (data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + gets_name((data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + "@s.whatsapp.net gewechselt.")
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed to " + (data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + Fore.YELLOW + gets_name((data[17][7:].decode('UTF-8', 'ignore').split('@'))[0] + "@s.whatsapp.net") + Fore.RESET + ".\n"

                            elif data[9] == 11:
                                if report_var == 'EN':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " created the group \"" + html.escape(data[4]) + "\"."
                                elif report_var == 'ES':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " creó el grupo \"" + html.escape(data[4]) + "\"."
                                elif report_var == 'DE':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat die Gruppe \"" + html.escape(data[4]) + "\" erstellt."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " created the group \"" + data[4] + "\".\n"

                            elif data[9] == 12:
                                if data[15]:  # If exists remote_resource - Group
                                    report_msg_user_added = (data[17][60:].decode('UTF-8', 'ignore').split('@'))[0]
                                    # Remove potential binary garbage.
                                    if report_msg_user_added.find('\x00\x1b') > 0:
                                        report_msg_user_added = report_msg_user_added[report_msg_user_added.find('\x00\x1b')+2:]
                                    if report_var == 'EN':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " added " + report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " to the group."
                                    elif report_var == 'ES':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " añadió " + report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " al grupo."
                                    elif report_var == 'DE':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat " + report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " hinzugefügt."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " added " + report_msg_user_added + Fore.YELLOW + gets_name(report_msg_user_added + "@s.whatsapp.net") + Fore.RESET + " to the group.\n"

                                else:  # User
                                    if report_var == 'EN':
                                        report_msg += report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " added to the group."
                                    elif report_var == 'ES':
                                        report_msg += "Se añadió " + report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " al grupo."
                                    elif report_var == 'DE':
                                        report_msg += report_msg_user_added + gets_name(report_msg_user_added + "@s.whatsapp.net") + " wurde hinzugefügt."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + report_msg_user_added + Fore.YELLOW + gets_name(report_msg_user_added + "@s.whatsapp.net") + Fore.RESET + "added to the group.\n"

                            elif data[9] == 13:
                                list_broadcast = (str(data[17][58:]).split("\\x00\\x1a"))[1:]
                                list_copy = []
                                for i in list_broadcast:
                                    list_copy.append(i.split("@")[0] + gets_name(i.split("@")[0] + "@s.whatsapp.net"))

                                if report_var == 'EN':
                                    report_msg += ", ".join(list_copy) + " left the group."
                                elif report_var == 'ES':
                                    report_msg += ", ".join(list_copy) + " dejaron el grupo."
                                elif report_var == 'DE':
                                    report_msg += ", ".join(list_copy) + " hat die Gruppe verlassen."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + ", ".join(list_copy) + " left the group.\n"

                            elif data[9] == 14:
                                report_msg_user_eliminated = (data[17][60:].decode('UTF-8', 'ignore').split('@'))[0]
                                # Remove potential binary garbage.
                                if report_msg_user_eliminated.find('\x00\x1b') > 0:
                                    report_msg_user_eliminated = report_msg_user_eliminated[report_msg_user_eliminated.find('\x00\x1b')+2:]
                                if data[15]:    # Somebody eliminated somebody from the group.
                                    if report_var == 'EN':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " eliminated " + report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " from the group."
                                    elif report_var == 'ES':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " eliminó " + report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " del grupo."
                                    elif report_var == 'DE':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat " + report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " entfernt."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " eliminated " + report_msg_user_eliminated + Fore.YELLOW + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + Fore.RESET + " from the group.\n"
                                else:   # Somebody was eliminated from the group.
                                    if report_var == 'EN':
                                        report_msg += report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " eliminated from the group."
                                    elif report_var == 'ES':
                                        report_msg += "Se eliminó " + report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " del grupo."
                                    elif report_var == 'DE':
                                        report_msg += report_msg_user_eliminated + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + " wurde entfernt."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + report_msg_user_eliminated + Fore.YELLOW + gets_name(report_msg_user_eliminated + "@s.whatsapp.net") + Fore.RESET + " eliminated from the group.\n"

                            elif data[9] == 15:
                                if data[15]:    # Someone made you administrator.
                                    if report_var == 'EN':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " made you an admin."
                                    elif report_var == 'ES':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " te hizo administrador."
                                    elif report_var == 'DE':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat Dich zum Admin gemacht."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + "made you an administrator.\n"
                                else:   # You became an administrator, because all other administrators have left the group.
                                    if report_var == 'EN':
                                        report_msg += "You're now an admin."
                                    elif report_var == 'ES':
                                        report_msg += "Ahora eres administrador."
                                    elif report_var == 'DE':
                                        report_msg += "Du bist jetzt ein Admin."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + "You're now an administrator.\n"

                            elif data[9] == 18:
                                if data[15]:
                                    if report_var == 'EN':
                                        report_msg += "The security code of " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " changed."
                                    elif report_var == 'ES':
                                        report_msg += "El código de seguridad de " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " cambió."
                                    elif report_var == 'DE':
                                        report_msg += "Die Sicherheitsnummer von " + data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat sich geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + "The security code of " + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed.\n"

                                else:
                                    if report_var == 'EN':
                                        report_msg += "The security code of " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " changed."
                                    elif report_var == 'ES':
                                        report_msg += "El código de seguridad de " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " cambió."
                                    elif report_var == 'DE':
                                        report_msg += "Die Sicherheitsnummer von " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " hat sich geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + "The security code of " + data[0].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + " changed.\n"

                            elif data[9] == 19:
                                if report_var == 'EN':
                                    report_msg += "Messages and calls in this chat are now protected with end-to-end encryption."
                                elif report_var == 'ES':
                                    report_msg += "Los mensajes y llamadas en este chat ahora están protegidos con cifrado de extremo a extremo."
                                elif report_var == 'DE':
                                    report_msg += "Nachrichten in diesem Chat sowie Anrufe sind jetzt mit Ende-zu-Ende-Verschlüsselung geschützt."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + "Messages and calls in this chat are now protected with end-to-end encryption.\n"

                            elif data[9] == 20:
                                report_msg_user_joined = (data[17][60:].decode('UTF-8', 'ignore').split('@'))[0]
                                # Remove potential binary garbage.
                                if report_msg_user_joined.find('\x00\x1b') > 0:
                                    report_msg_user_joined = report_msg_user_joined[report_msg_user_joined.find('\x00\x1b')+2:]
                                if report_var == 'EN':
                                    report_msg += report_msg_user_joined + gets_name(report_msg_user_joined + "@s.whatsapp.net") + " joined using an invitation link from this group."
                                elif report_var == 'ES':
                                    report_msg += report_msg_user_joined + gets_name(report_msg_user_joined + "@s.whatsapp.net") + " se unió usando un enlace de invitación de este grupo."
                                elif report_var == 'DE':
                                    report_msg += report_msg_user_joined + gets_name(report_msg_user_joined + "@s.whatsapp.net") + " ist dieser Gruppe mit dem Einladungslink beigetreten."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + report_msg_user_joined + Fore.YELLOW + gets_name(report_msg_user_joined + "@s.whatsapp.net") + Fore.RESET + " joined using an invitation link from this group.\n"

                            elif data[9] == 22:
                                if report_var == 'EN':
                                    report_msg += "This chat could be with a company account."
                                elif report_var == 'ES':
                                    report_msg += "Este chat podría ser con una cuenta de empresa."
                                elif report_var == 'DE':
                                    report_msg += "Dieser Chat könnte mit einem Firmenkonto geführt werden."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + "This chat could be with a company account.\n"

                            elif data[9] == 27:
                                if data[4] != "":
                                    if report_var == 'EN':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " changed the group description to \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'ES':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " cambió la descripción del grupo a \"" + html.escape(data[4]) + "\"."
                                    elif report_var == 'DE':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat die Gruppenbeschreibung zu \"" + html.escape(data[4]) + "\" geändert."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the group description to \"" + data[4] + "\".\n"

                                else:
                                    if report_var == 'EN':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " deleted the group description."
                                    elif report_var == 'ES':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " borró la descripción del grupo."
                                    elif report_var == 'DE':
                                        report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat die Gruppenbeschreibung gelöscht."
                                    else:
                                        message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " deleted the group description\n"
                            elif data[9] == 28:
                                if report_var == 'EN':
                                    report_msg += data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " changed the phone number."
                                elif report_var == 'ES':
                                    report_msg += data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " cambió su número de teléfono."
                                elif report_var == 'DE':
                                    report_msg += data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " hat die Telefonnummer geändert."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[0].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + " changed the phone number.\n"
                            elif data[9] == 46:
                                if report_var == 'EN':
                                    report_msg += "This chat is with a company account."
                                elif report_var == 'ES':
                                    report_msg += "Este chat es con una cuenta de empresa."
                                elif report_var == 'DE':
                                    report_msg += "Dieser Chat ist mit einem Firmenkonto."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + "This chat is with a company account.\n"
                            elif data[9] == 29:
                                if report_var == 'EN':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " changed the settings for the group " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + "."
                                elif report_var == 'ES':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " cambió la configuración del grupo " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + "."
                                elif report_var == 'DE':
                                    report_msg += data[15].strip("@s.whatsapp.net") + gets_name(data[15]) + " hat die Einstellungen für die Gruppe " + data[0].strip("@s.whatsapp.net") + gets_name(data[0]) + " geändert."
                                else:
                                    message += Fore.GREEN + "Message: " + Fore.RESET + data[15].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[15]) + Fore.RESET + " changed the settings for the group " + data[0].strip("@s.whatsapp.net") + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + ".\n"

                            else:
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_msg += ""
                                else:
                                    message += Fore.RED + "Unknow system message: {}, Message ID {}, Timestamp {}".format(data[9], str(data[23]), time.strftime('%d-%m-%Y %H:%M', time.localtime(data[5] / 1000))) + Fore.RESET
                                print("\nUnknow system message: {}, Message ID {}, Timestamp {}".format(data[9], str(data[23]), time.strftime('%d-%m-%Y %H:%M', time.localtime(data[5] / 1000))))
                                print("Contact the creator of Whapa to include this new type of identified control messaging.")

                        else:
                            if data[24] and int(data[24]) > 0:  # Forwarded
                                if report_var == 'EN':
                                    report_msg += "<font color=\"#8b8878\">&#10150; Forwarded</font><br>"
                                elif report_var == 'ES':
                                    report_msg += "<font color=\"#8b8878\">&#10150; Reenviado</font><br>"
                                elif report_var == 'DE':
                                    report_msg += "<font color=\"#8b8878\">&#10150; Weitergeleitet</font><br>"
                                else:
                                    message += Fore.GREEN + "Forwarded " + Fore.RESET + "\n"

                            if data[21] and int(data[21]) > 0:  # Reply
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_msg = "<p style=\"border-left: 6px solid blue; background-color: lightgrey;border-radius:5px;\">" + \
                                                 linkify(reply(data[21], local)[1]) + "</p>"
                                else:
                                    message += Fore.RED + "Replying to: " + Fore.RESET + reply(data[21], local)[0] + "\n"

                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += linkify(html.escape(data[4]))
                            else:
                                message += Fore.GREEN + "Message: " + Fore.RESET + data[4] + "\n"

                    elif int(data[8]) == 1:  # media_wa_type 1, Image
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Image doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if data[11]:  # media_caption
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb + " - " + html.escape(data[11])
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + Fore.GREEN + " - Caption: " + Fore.RESET + data[11] + "\n"
                        else:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + "\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += " " + size_file(data[9])
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + "image/jpeg" + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + "\n"

                        if thumb != "Not downloaded":
                            thumb = local + thumb[2:]

                        if os.path.isfile(thumb) is False:
                            distutils.dir_util.mkpath(local + "Media/WhatsApp Images/Sent")
                            if thumb == "Not downloaded":
                                if int(data[1]) == 1:
                                    thumb = local + "Media/WhatsApp Images/Sent/IMG-" + str(data[2]) + "-NotDownloaded.jpg"
                                else:
                                    thumb = local + "Media/WhatsApp Images/IMG-" + str(data[2]) + "-NotDownloaded.jpg"

                            with open(thumb, 'wb') as profile_file:
                                if data[19]:    # raw_data exists
                                    profile_file.write(data[19])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                elif data[22]:  # Gets the thumbnail of the message_thumbnails
                                    profile_file.write(data[22])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                else:
                                    profile_file.write(b"")

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                            number = thumb.rfind("Media/WhatsApp Images/")
#                            thumb = thumb[number-1:].replace("\\", "/")
                            thumb = os.path.relpath(thumb, local)
                            report_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb) + "</a>"

                        report_msg = linkify(report_msg)

                    elif int(data[8]) == 2:  # media_wa_type 2, Audio
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Audio doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += "<br>" + thumb + " " + size_file(data[9]) + " - " + duration_file(data[12]) + "<br><audio controls><source src=\"." + thumb + "\" type=\"" + data[7] + "\"></audio>"
                        else:
                            message += Fore.GREEN + "Name: " + Fore.RESET + thumb + "\n"
                            message += Fore.GREEN + "Type: " + Fore.RESET + data[7] + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[12]) + "\n"

                        report_msg = linkify(report_msg)

                    elif int(data[8]) == 3:  # media_wa_type 3 Video
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Video doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if data[11]:  # media_caption
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb + " - " + html.escape(data[11])
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + Fore.GREEN + " - Caption: " + Fore.RESET + data[11] + "\n"
                        else:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + "\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += " " + size_file(data[9]) + " - " + duration_file(data[12])
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + data[7] + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[12]) + "\n"

                        if thumb != "Not downloaded":
                            thumb = local + thumb[2:]

                        if os.path.isfile(thumb) is False:
                            distutils.dir_util.mkpath(local + "Media/WhatsApp Video/Sent")
                            if thumb == "Not downloaded":
                                if int(data[1]) == 1:
                                    thumb = local + "Media/WhatsApp Video/Sent/VID-" + str(data[2]) + "-NotDownloaded.mp4"
                                else:
                                    thumb = local + "Media/WhatsApp Video/VID-" + str(data[2]) + "-NotDownloaded.mp4"

                            with open(thumb, 'wb') as profile_file:
                                if data[19]:  # raw_data exists
                                    profile_file.write(data[19])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                elif data[22]:  # Gets the thumbnail of the message_thumbnails
                                    profile_file.write(data[22])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                else:
                                    profile_file.write(b"")


                        # Save separate thumbnail image for video content.
                        if os.path.isfile(thumb + ".jpg") is False:
                            with open(thumb + ".jpg", 'wb') as profile_file:
                                if data[19]:  # raw_data exists
                                    profile_file.write(data[19])
                                elif data[22]:  # Gets the thumbnail of the message_thumbnails
                                    profile_file.write(data[22])
                                else:
                                    profile_file.write(b"")

                            if report_var == 'None':
                                message += "Thumbnail for video '" + thumb + "' was saved on local path '" + thumb + ".jpg" + "'\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                            number = thumb.rfind("Media/WhatsApp Video/")
#                            thumb = thumb[number-1:].replace("\\", "/")
                            thumb = os.path.relpath(thumb, local)
                            report_msg += "<br/><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"

                        report_msg = linkify(report_msg)

                    elif int(data[8]) == 4:  # media_wa_type 4, Contact
                        vcard_data, vcard_names = vcard_data_extract(data[4])
                        vcard_tooltip = html_vcard_tooltip(vcard_data)
                        if settings['contact_vcard_dir']:
                            vcard_file_name = os.path.abspath(os.path.join(local, settings['contact_vcard_dir'], arg_group + arg_user + "-" + data[2] + ".vcf"))
                            vcard_file_create(vcard_file_name, vcard_data)
                            vcard_file_name = media_rel_path + os.path.relpath(vcard_file_name, local)
                            if report_var == 'EN':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contact vCard</a>"
                            elif report_var == 'ES':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contacto vCard</a>"
                            elif report_var == 'DE':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Kontakt vCard</a>"
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + data[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"
                        else:
                            if report_var == 'EN':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Contact vCard"
                            elif report_var == 'ES':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Contacto vCard"
                            elif report_var == 'DE':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Kontakt vCard"
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + data[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"

                    elif int(data[8]) == 5:  # media_wa_type 5, Location
                        if data[6]:  # media_url exists
                            if data[10]:  # media_name exists
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_msg += html.escape(data[6]) + " - " + html.escape(data[10]) + "<br>"
                                else:
                                    message += Fore.GREEN + "Url: " + Fore.RESET + data[6] + Fore.GREEN + " - Name: " + Fore.RESET + data[10] + "\n"
                            else:
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_msg += html.escape(data[6]) + "<br>"
                                else:
                                    message += Fore.GREEN + "Url: " + Fore.RESET + data[6] + "\n"
                        else:
                            if data[10]:
                                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                    report_msg += html.escape(data[10]) + "<br>"
                                else:
                                    message += Fore.GREEN + "Name: " + Fore.RESET + data[10] + "\n"

                        report_msg = linkify(report_msg)

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += "<iframe width=\"300\" height=\"150\" id=\"gmap_canvas\" src=\"https://maps.google.com/maps?q={}%2C{}&t=&z=15&ie=UTF8&iwloc=&output=embed\" frameborder=\"0\" scrolling=\"no\" marginheight=\"0\" marginwidth=\"0\"></iframe>".format(str(data[13]), str(data[14]))
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + "Location" + Fore.GREEN + " - Lat: " + Fore.RESET + str(data[13]) + Fore.GREEN + " - Long: " + Fore.RESET + str(data[14]) + "\n"

                    elif int(data[8]) == 8:  # media_wa_type 8, Audio / Video Call
                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += "&#128222; " + str(data[11]).capitalize() + " " + duration_file(data[12])
                        else:
                            message += Fore.GREEN + "Call: " + Fore.RESET + str(data[11]).capitalize() + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[12]) + "\n"

                    elif int(data[8]) == 9:  # media_wa_type 9, Application
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Image doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if data[11]:  # media_caption
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb + " - " + html.escape(data[11])
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + Fore.GREEN + " - Caption: " + Fore.RESET + data[11] + "\n"
                        else:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + "\n"

                        if data[12] >= 0:
                            if report_var == 'EN':
                                report_msg += " " + size_file(data[9]) + " - " + str(data[12]) + " pages"
                            elif report_var == 'ES':
                                report_msg += " " + size_file(data[9]) + " - " + str(data[12]) + " páginas"
                            elif report_var == 'DE':
                                report_msg += " " + size_file(data[9]) + " - " + str(data[12]) + " Seiten"
                            else:
                                message += Fore.GREEN + "Type: " + Fore.RESET + data[7] + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + Fore.GREEN + " - Pages: " + Fore.RESET + str(data[12]) + "\n"
                        else:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += " " + size_file(data[9])
                            else:
                                message += Fore.GREEN + "Type: " + Fore.RESET + data[7] + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + "\n"

                        if thumb != "Not downloaded":
                            thumb = local + thumb[2:]

                        if os.path.isfile(thumb + ".jpg") is False:
                            distutils.dir_util.mkpath(local + "Media/WhatsApp Documents/Sent")
                            if thumb == "Not downloaded":
                                if int(data[1]) == 1:
                                    thumb = local + "Media/WhatsApp Documents/Sent/DOC-" + str(data[2]) + "-NotDownloaded"
                                else:
                                    thumb = local + "Media/WhatsApp Documents/DOC-" + str(data[2]) + "-NotDownloaded"

                            with open(thumb + ".jpg", 'wb') as profile_file:
                                if data[19]:
                                    profile_file.write(data[19])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + ".jpg'\n"
                                elif data[22]:
                                    profile_file.write(data[22])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + ".jpg'\n"
                                else:
                                    profile_file.write(b"")

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                            number = thumb.rfind("Media/WhatsApp Documents/")
#                            thumb = thumb[number-1:].replace("\\", "/")
                            thumb = os.path.relpath(thumb, local)
                            report_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"

                        report_msg = linkify(report_msg)

                    elif int(data[8]) == 10:  # media_wa_type 10, Video/Audio call lost
                        report_msg_call = ""
                        if data[11]:
                            report_msg_call = str(data[11]).capitalize() + " "
                        if report_var == 'EN':
                            report_msg += "&#128222; Missed " + report_msg_call + "call."
                        elif report_var == 'ES':
                            report_msg += "&#128222; " + report_msg_call + "llamada perdida."
                        elif report_var == 'DE':
                            report_msg += "&#128222; Verpasster " + report_msg_call + "Anruf."
                        else:
                            message += Fore.GREEN + "Message: " + Fore.RESET + "Missed " + report_msg_call + " call\n"

                    elif int(data[8]) == 11:  # media_wa_type 11, Waiting for message
                        if report_var == 'EN':
                            report_msg += "<p style=\"color:#FF0000\";>&#9842; Waiting for message. This may take time.</p>"
                        elif report_var == 'ES':
                            report_msg += "<p style=\"color:#FF0000\";>&#9842; Esperando mensaje. Esto puede tomar tiempo.</p>"
                        elif report_var == 'DE':
                            report_msg += "<p style=\"color:#FF0000\";>&#9842; Warten auf eine Nachricht. Dies kann einige Zeit dauern.</p>"
                        else:
                            message += Fore.GREEN + "Message: " + Fore.RESET + "Waiting for message. This may take time.\n"

                    elif int(data[8]) == 13:  # media_wa_type 13 Gif
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Gif doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if data[11]:  # media_caption
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb + " - " + html.escape(data[11])
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + Fore.GREEN + " - Caption: " + Fore.RESET + data[11] + "\n"
                        else:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += thumb
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + thumb + "\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += " - Gif - " + size_file(data[9]) + " " + duration_file(data[12])
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + "Gif" + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[12]) + "\n"

                        if thumb != "Not downloaded":
                            thumb = local + thumb[2:]

                        if os.path.isfile(thumb) is False:
                            distutils.dir_util.mkpath(local + "Media/WhatsApp Animated Gifs/Sent")
                            if thumb == "Not downloaded":
                                if int(data[1]) == 1:
                                    thumb = local + "Media/WhatsApp Animated Gifs/Sent/VID-" + str(data[2]) + "-NotDownloaded.mp4"
                                else:
                                    thumb = local + "Media/WhatsApp Animated Gifs/VID-" + str(data[2]) + "-NotDownloaded.mp4"

                            with open(thumb, 'wb') as profile_file:
                                if data[19]:  # raw_data exists
                                    profile_file.write(data[19])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                elif data[22]:  # Gets the thumbnail of the message_thumbnails
                                    profile_file.write(data[22])
                                    if report_var == 'None':
                                        message += "Thumbnail was saved on local path '" + thumb + "'\n"
                                else:
                                    profile_file.write(b"")

                        # Save separate thumbnail image for video content.
                        if os.path.isfile(thumb + ".jpg") is False:
                            with open(thumb + ".jpg", 'wb') as profile_file:
                                if data[19]:  # raw_data exists
                                    profile_file.write(data[19])
                                elif data[22]:  # Gets the thumbnail of the message_thumbnails
                                    profile_file.write(data[22])
                                else:
                                    profile_file.write(b"")

                            if report_var == 'None':
                                message += "Thumbnail for video '" + thumb + "' was saved on local path '" + thumb + ".jpg" + "'\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                            number = thumb.rfind("Media/WhatsApp Animated Gifs/")
#                            thumb = thumb[number-1:].replace("\\", "/")
                            thumb = os.path.relpath(thumb, local)
                            report_msg += "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb + ".jpg") + "</a>"

                        report_msg = linkify(report_msg)

                    elif int(data[8]) == 14:  # media_wa_type 14  Vcard multiples
                        vcard_data, vcard_names = vcard_data_extract(data[19])
                        vcard_tooltip = html_vcard_tooltip(vcard_data)
                        if settings['contact_vcard_dir']:
                            vcard_file_name = os.path.abspath(os.path.join(local, settings['contact_vcard_dir'], arg_group + arg_user + "-" + data[2] + ".vcf"))
                            vcard_file_create(vcard_file_name, vcard_data)
                            vcard_file_name = media_rel_path + os.path.relpath(vcard_file_name, local)
                            vcard_names_html = ''.join(["<br>" + html.escape(str(vc_name)) for vc_name in vcard_names])
                            if report_var == 'EN':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contact vCard:" + vcard_names_html + "</a>"
                            elif report_var == 'ES':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Contacto vCard:</br></a>" + vcard_names_html
                            elif report_var == 'DE':
                                report_msg += html.escape(data[10]) + "<br><a href=\"" + vcard_file_name + "\"" + vcard_tooltip + ">&#9742; Kontakt vCard:</br></a>" + vcard_names_html
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + data[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"
                        else:
                            if report_var == 'EN':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Contact vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                            elif report_var == 'ES':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Contacto vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                            elif report_var == 'DE':
                                report_msg += html.escape(data[10]) + "<br>&#9742; Kontakt vCard:</br>" + vcard_data.replace("\r", "").replace("\n", "<br>")
                            else:
                                message += Fore.GREEN + "Name: " + Fore.RESET + data[10] + Fore.GREEN + " - Type:" + Fore.RESET + " Contact vCard:\n" + vcard_data + "\n"

                    elif int(data[8]) == 15:  # media_wa_type 15, Deleted Object
                        if int(data[16]) == 5:  # edit_version 5, deleted for me
                            if report_var == 'EN':
                                report_msg += "Message deleted for me."
                            elif report_var == 'ES':
                                report_msg += "Mensaje eliminado para mí."
                            elif report_var == 'DE':
                                report_msg += "Nachricht für mich gelöscht."
                            else:
                                message += Fore.GREEN + "Message: " + Fore.RESET + "Message deleted for me.\n"

                        elif int(data[16]) == 7:  # edit_version 7, deleted for all
                            if report_var == 'EN':
                                report_msg += "Message deleted for all participants."
                            elif report_var == 'ES':
                                report_msg += "Mensaje eliminado para todos los destinatarios."
                            elif report_var == 'DE':
                                report_msg += "Nachricht für alle Teilnehmer gelöscht."
                            else:
                                message += Fore.GREEN + "Message: " + Fore.RESET + "Message deleted for all participants\n"

                    elif int(data[8]) == 16:  # media_wa_type 16, Share location
                        caption = ""
                        if data[11]:
                            caption = " - " + data[11]

                        if report_var == 'EN':
                            report_msg += "Real time location (" + str(data[13]) + ", " + str(data[14]) + ")" + html.escape(caption) + "\n"
#                            report_msg += " <br><a href=\"https://www.google.es/maps/search/(" + str(data[13]) + "," + str(data[14]) + ")\" target=\"_self\"><img src=\"https://maps.google.com/maps/api/staticmap?center=" + str(data[13]) + "," + str(data[14]) + "&zoom=16&size=300x150&markers=size:mid|color:red|label:A|" + str(data[13]) + "," + str(data[14]) + "&sensor=false\"/></a>"
                        elif report_var == 'ES':
                            report_msg += "Ubicación en tiempo real (" + str(data[13]) + ", " + str(data[14]) + ")" + html.escape(caption) + "\n"
                        elif report_var == 'DE':
                            report_msg += "Live-Standort (" + str(data[13]) + ", " + str(data[14]) + ")" + html.escape(caption) + "\n"
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + "Real time location " + Fore.GREEN + "- Caption: " + Fore.RESET + caption + Fore.GREEN + " - Lat: " + Fore.RESET + str(data[13]) + Fore.GREEN + " - Long: " + Fore.RESET + str(data[14]) + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[12]) + "\n"

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                            report_msg += "<br><iframe width=\"300\" height=\"150\" id=\"gmap_canvas\" src=\"https://maps.google.com/maps?q={}%2C{}&t=&z=15&ie=UTF8&iwloc=&output=embed\" frameborder=\"0\" scrolling=\"no\" marginheight=\"0\" marginwidth=\"0\"></iframe>".format(str(data[13]), str(data[14]))

                    elif int(data[8]) == 20:  # media_wa_type 20 Sticker
                        chain = data[17].split(b'\x77\x02')[0]
                        i = chain.rfind(b"Media/")
                        b = len(chain)
                        if i == -1:  # Audio doesn't exist
                            thumb = "Not downloaded"
                        else:
                            thumb = (b"./" + chain[i:b]).decode('UTF-8', 'ignore')

                        if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
#                            number = thumb.rfind("Media/WhatsApp Stickers/")
#                            thumb = thumb[number-1:].replace("\\", "/")
                            thumb = os.path.abspath(os.path.join(local, thumb))     # The sticker path from the WhatsApp database is relative!
                            thumb = os.path.relpath(thumb, local)
                            report_msg += " Sticker - " + size_file(data[9]) + "<br><a href=\"" + media_rel_path + thumb + "\" target=\"_self\">" + html_preview_file(thumb) + "</a>"
                        else:
                            message += Fore.GREEN + "Type: " + Fore.RESET + "Sticker" + Fore.GREEN + " - Size: " + Fore.RESET + str(data[9]) + " bytes " + size_file(data[9]) + Fore.GREEN + "\n"

                    if data[20]:
                        if int(data[20]) == 1:
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_msg += "<br> &#127775;"
                            else:
                                message += Fore.YELLOW + "Starred message " + Fore.RESET + "\n"

                    main_status, report_status = status(int(data[3]))

                    if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                        report_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[5] / 1000))
                        if report_var == 'DE':
                            report_time = time.strftime('%d.%m.%Y %H:%M:%S', time.localtime(data[5] / 1000))
                        if ((report_name == lang_en_me) or (report_name == "&#128227; " + lang_en_me) or
                            (report_name == lang_es_me) or (report_name == "&#128227; " + lang_es_me) or
                            (report_name == lang_de_me) or (report_name == "&#128227; " + lang_de_me)):
                            rep_med += """
            <li>
                <div class="bubble2">
                    <span class="personSay2">""" + html_report_message(report_msg) + """</span><br>
                    <span class="time2 round">""" + report_time + "&nbsp;" + report_status + """</span><br>
                </div>
            </li>"""
                        elif ((report_name == lang_en_sys_msg) or
                            (report_name == lang_es_sys_msg) or
                            (report_name == lang_de_sys_msg)):
                            rep_med += """
            <li>
                <div class="bubble-system">
                    <span class="time-system round">""" + report_time + "&nbsp;" + report_status + """</span><br>
                    <span class="person-System">""" + report_msg + """</span><br>
                </div>
            </li>"""
                        else:
                            rep_med += """
            <li>
                <div class="bubble">
                    <span class="personName">""" + report_name + """</span><br>
                    <span class="personSay">""" + html_report_message(report_msg) + """</span><br>
                    <span class="time round">""" + report_time + "&nbsp;" + report_status + """</span><br>
                </div>
            </li>"""
                    elif report_var == 'None':
                        message += Fore.GREEN + "Timestamp: " + Fore.RESET + time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[5] / 1000)) + Fore.GREEN + " - Status: " + Fore.RESET + main_status + "\n"
                        print(message)
                n_mes += 1

            except Exception as e:
                print("\n" + prefix_error + "Error showing message details: {}, Message ID {}, Timestamp {}".format(e, str(data[23]), time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[5] / 1000))))
                n_mes += 1
                count_errors += 1
                continue

        if report_var != "None":
            report(rep_med, report_html, local)
            try:
                shutil.copy("./cfg/chat.css", local + "cfg/chat.css")
                shutil.copy("./cfg/logo.png", local + "cfg/logo.png")
                shutil.copy("./images/background.png", local + "cfg/background.png")
                shutil.copy("./images/background-index.png", local + "cfg/background-index.png")
            except:
                pass

    except Exception as e:
        print("\n" + prefix_error + "An error occurred connecting to the database:", e)
        count_errors += 1

    global count_messages
    count_messages += n_mes


def info(opt, local):
    """Function that shows info"""
    if opt == '1':  # Status
        print(Fore.RED + "Status" + Fore.RESET)
        rep_med = ""
        sql_string = " SELECT messages.key_remote_jid, messages.key_from_me, messages.key_id, messages.status, messages.data, messages.timestamp, messages.media_url, messages.media_mime_type," \
                     " messages.media_wa_type, messages.media_size, messages.media_name, messages.media_caption, messages.media_duration, messages.latitude, messages.longitude, " \
                     " messages.remote_resource, messages.edit_version, messages.thumb_image, messages.recipient_count, messages.raw_data, messages.starred, messages.quoted_row_id, " \
                     " message_thumbnails.thumbnail, messages._id, messages.forwarded  FROM messages LEFT JOIN message_thumbnails ON messages.key_id = message_thumbnails.key_id WHERE messages.key_remote_jid='status@broadcast'"
        sql_count = "SELECT COUNT(*) FROM messages WHERE key_remote_jid='status@broadcast'"
        print("Loading data ...")
        result = cursor.execute(sql_count)
        result = cursor.fetchone()
        print("Number of messages: {}".format(str(result[0])))
        sql_consult = cursor.execute(sql_string)
        report_html = settings['report_prefix'] + "status.html"
        messages(sql_consult, result[0], report_html, local)
        print(prefix_info + "Finished")

    elif opt == '2':  # Calls
        print(Fore.RED + "Calls" + Fore.RESET)
        rep_med = ""
        epoch_start = "0"
        epoch_end = str(1000 * int(time.mktime(time.strptime(time.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S'))))

        if args.time_start:
            epoch_start = 1000 * int(time.mktime(time.strptime(args.time_start, '%d-%m-%Y %H:%M:%S')))
        if args.time_end:
            epoch_end = 1000 * int(time.mktime(time.strptime(args.time_end, '%d-%m-%Y %H:%M:%S')))

        sql_string = "SELECT jid.raw_string, call_log.from_me, call_log.timestamp, call_log.video_call, call_log.duration FROM call_log LEFT JOIN jid ON call_log.jid_row_id = jid._id WHERE " \
                     " call_log.timestamp BETWEEN " + str(epoch_start) + " AND " + str(epoch_end) + ";"
        sql_count = "SELECT count(*) FROM call_log WHERE timestamp BETWEEN " + str(epoch_start) + " AND " + str(epoch_end) + ";"
        print("Loading data ...")
        result = cursor.execute(sql_count)
        result = cursor.fetchone()
        print("Number of messages: {}".format(str(result[0])))
        consult = cursor.execute(sql_string)
        for data in consult:
            if report_var == 'None':
                message = Fore.RED + "\n--------------------------------------------------------------------------------" + Fore.RESET + "\n"

            if data[1] == 1:  # I Call
                if report_var == 'EN':
                    report_name = lang_en_me
                elif report_var == 'ES':
                    report_name = lang_es_me
                elif report_var == 'DE':
                    report_name = lang_de_me
                else:
                    message += Fore.GREEN + "From:" + Fore.RESET + " " + lang_en_me + " " + Fore.GREEN + "to " + Fore.RESET +  str(data[0]).split('@')[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + "\n"

            else:  # Somebody calls me
                if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                    report_name = str(data[0]).split('@')[0] + gets_name(data[0])
                else:
                    message += Fore.GREEN + "From: " + Fore.RESET + str(data[0]).split('@')[0] + Fore.YELLOW + gets_name(data[0]) + Fore.RESET + Fore.GREEN + " to " + Fore.RESET + lang_en_me + "\n"

            if data[3] == 0:   # Audio
                if report_var == 'EN':
                    report_msg = "&#127897; Incoming audio call.<br>"
                elif report_var == 'ES':
                    report_msg = "&#127897; Audio llamada entrante.<br>"
                elif report_var == 'DE':
                    report_msg = "&#127897; Eingehender Sprachanruf.<br>"
                else:
                    message += Fore.GREEN + "Message: " + Fore.RESET + "Incoming audio call\n"

            else:   # Video
                if report_var == 'EN':
                    report_msg = "&#127909; Incoming video call.<br>"
                elif report_var == 'ES':
                    report_msg = "&#127909; Video llamada entrante.<br>"
                elif report_var == 'DE':
                    report_msg = "&#127909; Eingehender Videoanruf.<br>"
                else:
                    message += Fore.GREEN + "Message: " + Fore.RESET + "Incoming video call\n"

            if report_var == 'None':
                message += Fore.GREEN + "Timestamp: " + Fore.RESET + time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[2] / 1000))

            if data[4] > 0:
                if report_var == 'EN':
                    report_msg += "Connection established - Duration: " + duration_file(data[4]) + "<br>"
                elif report_var == 'ES':
                    report_msg += "Conexión establecida - Duración: " + duration_file(data[4]) + "<br>"
                elif report_var == 'DE':
                    report_msg += "Verbindung hergestellt - Dauer: " + duration_file(data[4]) + "<br>"
                else:
                    message += Fore.GREEN + " - Status: " + Fore.RESET + "Established" + Fore.GREEN + " - Duration: " + Fore.RESET + duration_file(data[4])

            else:
                if report_var == 'EN':
                    report_msg += "Connection lost.<br>"
                elif report_var == 'ES':
                    report_msg += "Conexión perdida.<br>"
                elif report_var == 'DE':
                    report_msg += "Verbindung verloren.<br>"
                else:
                    message += Fore.GREEN + " - Status: " + Fore.RESET + "Lost."

            report_status = ""
            if report_var == 'EN':
                report_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[2] / 1000))
            elif report_var == 'ES':
                report_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data[2] / 1000))
            elif report_var == 'DE':
                report_time = time.strftime('%d.%m.%Y %H:%M:%S', time.localtime(data[2] / 1000))
            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                if ((report_var == 'EN' and report_name == lang_en_me) or
                    (report_var == 'ES' and report_name == lang_es_me) or
                    (report_var == 'DE' and report_name == lang_de_me)):
                    rep_med += """
                                       <li>
                                       <div class="bubble2"><span class="personName">""" + report_name + """</span><br>
                                           <span class="personSay2">""" + html_report_message(report_msg) + """</span></div>
                                       <span class=" time2 round ">""" + report_time + "&nbsp;" + report_status + """</span></li>"""
                else:
                    rep_med += """
                                       <li>
                                       <div class="bubble"><span class="personName2">""" + report_name + """</span><br>
                                           <span class="personSay">""" + html_report_message(report_msg) + """</span></div>
                                       <span class=" time round ">""" + report_time + "&nbsp;" + report_status + """</span></li>"""
            else:
                print(message)

        if report_var != "None":
            report_html = settings['report_prefix'] + "calls.html"
            print("[+] Creating report ...")
            report(rep_med, report_html, local)
            try:
                shutil.copy("./cfg/chat.css", local + "cfg/chat.css")
                shutil.copy("./cfg/logo.png", local + "cfg/logo.png")
                shutil.copy("./images/background.png", local + "cfg/background.png")
                shutil.copy("./images/background-index.png", local + "cfg/background-index.png")
            except:
                pass

        print("\n" + prefix_info + "Finished")

    elif opt == '3':  # Chat list
        print(Fore.RED + "Actives chat list" + Fore.RESET)

        sql_string_consult = "SELECT key_remote_jid FROM chat_list ORDER BY sort_timestamp DESC"
        sql_consult_chat = cursor.execute(sql_string_consult)
        for i in sql_consult_chat:
            show = i[0]
            if str(i[0]).split('@')[1] == 's.whatsapp.net':
                show = str(i[0]).split('@')[0]
            print("{} {}".format(show, Fore.YELLOW + gets_name(i[0]) + Fore.RESET))


def system_slash(string):
    """ Change / or \\ depend on the OS"""

    if sys.platform == "win32" or sys.platform == "win64" or sys.platform == "cygwin":
        return string.replace("/", "\\")

    else:
        return string.replace("\\", "/")


def get_configs():
    """Function that gets report config"""
    try:
        # Create the settings file if it does not exist.
        whautils.create_settings_file()
        # Read the settings from the settings file.
        settings = whautils.read_settings_file()
    except Exception as e:
        print(prefix_fatal + "The file '{0:s}' is missing or corrupt! Error:".format(whautils.settingsFile), e)
        sys.exit(1)


def extract(obj, total, local):
    """Function that extracts thumbnails."""
    global count_errors
    i = 1
    for data in obj:
        try:
            chain = str(data[2]).split('w\\x02')[0]
            a = chain.rfind("Media/")
            if a == -1:  # Image doesn't exist
                thumb = "Not downloaded"
            else:
                a = chain.rfind("/")
                b = len(chain)
                thumb = "./thumbnails" + (str(data[2]))[a:b]

            if thumb != "Not downloaded":
                thumb = local + thumb[2:]

            if os.path.isfile(thumb) is False:
                distutils.dir_util.mkpath(local + "thumbnails")

            if thumb == "Not downloaded":
                epoch = time.strftime("%Y%m%d", time.localtime((int(data[4]) / 1000)))
                thumb = local + "thumbnails/IMG-" + epoch + "-" + str(int(data[4]) / 1000) + "-NotDownloaded.jpg"

            if int(data[1]) == 9:
                thumb += ".jpg"

            with open(thumb, 'wb') as profile_file:
                if data[3]:  # raw_data exists
                    profile_file.write(data[3])
                elif data[5]:  # Gets the thumbnail of the message_thumbnails
                    profile_file.write(data[5])
                else:
                    profile_file.write(b"")

            sys.stdout.write("\rExtracting thumbnail " + str(i) + " / " + str(total))
            sys.stdout.flush()
            i += 1
        except Exception as e:
            print("\n" + prefix_error + "Error extracting: {}, Message ID {}".format(e, str(data[8])))
            count_errors += 1

    print("\n")
    print("Extraction Complete. Thumbnails save in './thumbnails' path")


#  Initializing
if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser(description="To start choose a database and a mode with options.")
    parser.add_argument("database", help="Database file path - './msgstore.db' by default", metavar="DATABASE", nargs='?', default="./msgstore.db")
    mode_parser = parser.add_mutually_exclusive_group()
    mode_parser.add_argument("-m", "--messages", help="*** Message Mode ***", action="store_true")
    mode_parser.add_argument("-i", "--info", help="*** Info Mode *** 1 Status - 2 Calls log - 3 Actives chat list")
    mode_parser.add_argument("-e", "--extract", help="*** Extract Mode ***", action="store_true")
    user_parser = parser.add_mutually_exclusive_group()
    user_parser.add_argument("-u", "--user", help="Show chat with a phone number, e.g. 34123456789")
    user_parser.add_argument("-ua", "--user_all", help="Show messages made by a phone number.")
    user_parser.add_argument("-g", "--group", help="Show chat with a group number, e.g. 34123456-14508@g.us")
    user_parser.add_argument("-a", "--all", help="Show all chat messages classified by phone number, group number and broadcast list.", action="store_true")
    parser.add_argument("-wa", "--wa_file", help="Show names along with numbers.")
    parser.add_argument("-t", "--text", help="Show messages by text match.")
    parser.add_argument("-w", "--web", help="Show messages made by WhatsApp Web.", action="store_true")
    parser.add_argument("-s", "--starred", help="Show messages starred by owner.", action="store_true")
    parser.add_argument("-b", "--broadcast", help="Show messages send by broadcast.", action="store_true")
    parser.add_argument("-ts", "--time_start", help="Show messages by start time (dd-mm-yyyy HH:MM).")
    parser.add_argument("-te", "--time_end", help="Show messages by end time (dd-mm-yyyy HH:MM).")
    parser.add_argument("-r", "--report", help='Make an HTML report in \'EN\' English, \'ES\' Spanish or \'DE\' German. If specified together with the option \'-a\', it generates a report for each chat.', const='EN', nargs='?', choices=['EN', 'ES', 'DE'])
    parser.add_argument("-c", "--carving", help="Carving in the database", action="store_true")
    parser.add_argument("-o", "--output", help="Output path")
    filter_parser = parser.add_mutually_exclusive_group()
    filter_parser.add_argument("-tt", "--type_text", help="Show text messages.", action="store_true")
    filter_parser.add_argument("-ti", "--type_image", help="Show image messages.", action="store_true")
    filter_parser.add_argument("-ta", "--type_audio", help="Show audio messages.", action="store_true")
    filter_parser.add_argument("-tv", "--type_video", help="Show video messages.", action="store_true")
    filter_parser.add_argument("-tc", "--type_contact", help="Show contact messages.", action="store_true")
    filter_parser.add_argument("-tl", "--type_location", help="Show location messages.", action="store_true")
    filter_parser.add_argument("-tx", "--type_call", help="Show audio/video call messages.", action="store_true")
    filter_parser.add_argument("-tp", "--type_application", help="Show application messages.", action="store_true")
    filter_parser.add_argument("-tg", "--type_gif", help="Show GIF messages.", action="store_true")
    filter_parser.add_argument("-td", "--type_deleted", help="Show deleted object messages.", action="store_true")
    filter_parser.add_argument("-tr", "--type_share", help="Show Real time location messages.", action="store_true")
    filter_parser.add_argument("-tk", "--type_stickers", help="Show Stickers messages.", action="store_true")
    filter_parser.add_argument("-tm", "--type_system", help="Show system messages.", action="store_true")

    args = parser.parse_args()
    init()

    if len(sys.argv) == 1:
        show_help()
    else:
        if args.output:
            local = os.path.abspath(r"{}".format(args.output)) + os.sep
        else:
            local = os.path.join(os.getcwd(), "reports") + os.sep
        if args.messages:
            if args.wa_file:
                names(args.wa_file)
            cursor, cursor_rep = db_connect(args.database)
            sql_string = "SELECT messages.key_remote_jid, messages.key_from_me, messages.key_id, messages.status, messages.data, messages.timestamp, messages.media_url, messages.media_mime_type," \
                         " messages.media_wa_type, messages.media_size, messages.media_name, messages.media_caption, messages.media_duration, messages.latitude, messages.longitude, " \
                         " messages.remote_resource, messages.edit_version, messages.thumb_image, messages.recipient_count, messages.raw_data, messages.starred, messages.quoted_row_id, " \
                         " message_thumbnails.thumbnail, messages._id, messages.forwarded  FROM messages LEFT JOIN message_thumbnails ON messages.key_id = message_thumbnails.key_id WHERE messages.timestamp BETWEEN '"
            sql_count = "SELECT COUNT(*) FROM messages LEFT JOIN message_thumbnails ON messages.key_id = message_thumbnails.key_id WHERE messages.timestamp BETWEEN '"
            try:
                epoch_start = "0"
                """ current date in Epoch milliseconds string """
                epoch_end = str(1000 * int(time.mktime(time.strptime(time.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S'))))

                if args.time_start:
                    epoch_start = 1000 * int(time.mktime(time.strptime(args.time_start, '%d-%m-%Y %H:%M:%S')))
                if args.time_end:
                    epoch_end = 1000 * int(time.mktime(time.strptime(args.time_end, '%d-%m-%Y %H:%M:%S')))
                sql_string += str(epoch_start) + "' AND '" + str(epoch_end) + "'"
                sql_count += str(epoch_start) + "' AND '" + str(epoch_end) + "'"

#                if args.output:
#                    local = args.output
#                else:
#                    local = os.getcwd() + "/reports/"

                if args.text:
                    sql_string += " AND messages.data LIKE '%" + str(args.text) + "%'"
                    sql_count += " AND messages.data LIKE '%" + str(args.text) + "%'"
                if args.web:
                    sql_string += " AND messages.key_id LIKE '3EB0%'"
                    sql_count += " AND messages.key_id LIKE '3EB0%'"
                if args.starred:
                    sql_string += " AND messages.starred = 1"
                    sql_count += " AND messages.starred = 1"
                if args.broadcast:
                    sql_string += " AND messages.remote_resource LIKE '%broadcast%'"
                    sql_count += " AND messages.remote_resource LIKE '%broadcast%'"
                if args.report:
                    report_var = args.report
                    get_configs()
                if args.type_text:
                    sql_string += " AND messages.media_wa_type = 0"
                    sql_count += " AND messages.media_wa_type = 0"
                if args.type_image:
                    sql_string += " AND messages.media_wa_type = 1"
                    sql_count += " AND messages.media_wa_type = 1"
                if args.type_audio:
                    sql_string += " AND messages.media_wa_type = 2"
                    sql_count += " AND messages.media_wa_type = 2"
                if args.type_video:
                    sql_string += " AND messages.media_wa_type = 3"
                    sql_count += " AND messages.media_wa_type = 3"
                if args.type_contact:
                    sql_string += " AND messages.media_wa_type = 4 OR messages.media_wa_type = 14"
                    sql_count += " AND messages.media_wa_type = 4 OR messages.media_wa_type = 14"
                if args.type_location:
                    sql_string += " AND messages.media_wa_type = 5"
                    sql_count += " AND messages.media_wa_type = 5"
                if args.type_call:
                    sql_string += " AND messages.media_wa_type = 8 OR messages.media_wa_type = 10"
                    sql_count += " AND messages.media_wa_type = 8 OR messages.media_wa_type = 10"
                if args.type_application:
                    sql_string += " AND messages.media_wa_type = 9"
                    sql_count += " AND messages.media_wa_type = 9"
                if args.type_gif:
                    sql_string += " AND messages.media_wa_type = 13"
                    sql_count += " AND messages.media_wa_type = 13"
                if args.type_deleted:
                    sql_string += " AND messages.media_wa_type = 15"
                    sql_count += " AND messages.media_wa_type = 15"
                if args.type_share:
                    sql_string += " AND messages.media_wa_type = 16"
                    sql_count += " AND messages.media_wa_type = 16"
                if args.type_stickers:
                    sql_string += " AND messages.media_wa_type = 20"
                    sql_count += " AND messages.media_wa_type = 20"
                if args.type_system:
                    sql_string += " AND messages.media_wa_type = 0 AND messages.status = 6"
                    sql_count += " AND messages.media_wa_type = 0 AND messages.status = 6"

                if args.user_all:
                    sql_string += " AND (messages.key_remote_jid LIKE '%" + str(args.user_all) + "%@s.whatsapp.net' OR messages.remote_resource LIKE '%" + str(args.user_all) + "%')"
                    sql_count += " AND (messages.key_remote_jid LIKE '%" + str(args.user_all) + "%@s.whatsapp.net' OR messages.remote_resource LIKE '%" + str(args.user_all) + "%')"
                    arg_user = args.user_all
                    report_html = os.path.join(local, settings['report_prefix'] + "user_all_" + args.user_all + ".html")

                elif args.user:
                    sql_string += " AND messages.key_remote_jid LIKE '%" + str(args.user) + "%@s.whatsapp.net'"
                    sql_count += " AND messages.key_remote_jid LIKE '%" + str(args.user) + "%@s.whatsapp.net'"
                    report_html = os.path.join(local, settings['report_prefix'] + "user_chat_" + args.user + ".html")
                    arg_user = args.user

                elif args.group:
                    sql_string += " AND messages.key_remote_jid LIKE '%" + str(args.group) + "%'"
                    sql_count += " AND messages.key_remote_jid LIKE '%" + str(args.group) + "%'"
                    arg_group = args.group
                    if arg_group.split("@")[1] == "g.us":
                        report_html = os.path.join(local, settings['report_prefix'] + "group_chat_" + args.group + ".html")
                        report_group, color = participants(args.group)
                    else:
                        report_html = os.path.join(local, settings['report_prefix'] + "broadcast_chat_" + args.group + ".html")
                        report_group, color = participants(args.group)

                elif args.all:
                    get_configs()
                    sql_string_consult = "SELECT raw_string_jid FROM chat_view ORDER BY sort_timestamp DESC"
                    sql_consult_chat = cursor.execute(sql_string_consult)
                    chats_live = []
                    for i in sql_consult_chat:
                        chats_live.append(i[0])
                    report_med = ""
                    report_med_newline = "\n                "
                    print("Loading data ...")
                    for i in chats_live:
                        sql_string_copy = sql_string
                        sql_count_copy = sql_count
                        profile_picture_img_tag = ""

                        if i.split('@')[1] == "g.us":
                            report_med += report_med_newline
                            if settings['profile_pics_enable']:
                                profile_picture_img_tag = "<img src=\"" + media_rel_path + profile_picture(i, "")
                                if settings['html_img_alt_enable']:
                                    profile_picture_img_tag += "\" alt=\"" + media_rel_path + profile_picture(i, "")
                                profile_picture_img_tag += "\" height=\"" + settings['profile_pics_size_index'] + "\" style=\"padding-right:10px; vertical-align:middle;\" onError=\"this.onerror=null; this.src='." + settings['html_img_noimage_pic'] + "';\">"
                            if report_var == 'EN':
                                report_med_group = "Group"
                            elif report_var == 'ES':
                                report_med_group = "Grupo"
                            elif report_var == 'DE':
                                report_med_group = "Gruppe"
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_med += "<tr><th>" + report_med_group + "</th><th style=\"padding:2px; padding-left:8px\"><a href=\"" + settings['report_prefix'] + "group_chat_" + i + ".html" + "\" target=\"_blank\">" + profile_picture_img_tag + i + gets_name(i) + "</a></th></tr>"
                                report_html = settings['report_prefix'] + "group_chat_" + i + ".html"
                            sql_string_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            sql_count_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            arg_group = i
                            arg_user = ""
                            result = cursor.execute(sql_count_copy)
                            result = cursor.fetchone()
                            print("\nNumber of messages: {}".format(str(result[0])))
                            print(Fore.RED + "--------------------------------------------------------------------------------" + Fore.RESET)
                            print(Fore.CYAN + "GROUP CHAT " + i + Fore.RESET + Fore.YELLOW + gets_name(i, "preserve_emoji") + Fore.RESET)
                            report_group, color = participants(arg_group)
                            count_group_chats += 1

                        elif i.split('@')[1] == "s.whatsapp.net":
                            report_med += report_med_newline
                            if settings['profile_pics_enable']:
                                profile_picture_img_tag = "<img src=\"" + media_rel_path + profile_picture("", i.split('@')[0])
                                if settings['html_img_alt_enable']:
                                    profile_picture_img_tag += "\" alt=\"" + media_rel_path + profile_picture("", i.split('@')[0])
                                profile_picture_img_tag += "\" height=\"" + settings['profile_pics_size_index'] + "\" style=\"padding-right:10px; vertical-align:middle;\" onError=\"this.onerror=null; this.src='." + settings['html_img_noimage_pic'] + "';\">"
                            if report_var == 'EN':
                                report_med_user = "User"
                            elif report_var == 'ES':
                                report_med_user = "Usuario"
                            elif report_var == 'DE':
                                report_med_user = "Nutzer"
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_med += "<tr><th>" + report_med_user + "</th><th style=\"padding:2px; padding-left:8px\"><a href=\"" + settings['report_prefix'] + "user_chat_" + i.split('@')[0] + ".html" + "\" target=\"_blank\">" + profile_picture_img_tag + i.split('@')[0] + gets_name(i) + "</a></th></tr>"
                                report_html = settings['report_prefix'] + "user_chat_" + i.split('@')[0] + ".html"
                            sql_string_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            sql_count_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            arg_group = ""
                            arg_user = i.split('@')[0]
                            result = cursor.execute(sql_count_copy)
                            result = cursor.fetchone()
                            print("\nNumber of messages: {}".format(str(result[0])))
                            print(Fore.RED + "--------------------------------------------------------------------------------" + Fore.RESET)
                            print(Fore.CYAN + "USER CHAT " + arg_user + Fore.RESET + Fore.YELLOW + gets_name(i, "preserve_emoji") + Fore.RESET)
                            report_group = ""
                            count_user_chats += 1

                        elif i.split('@')[1] == "broadcast":
                            report_med += report_med_newline
                            if report_var == 'EN':
                                report_med_broadcast = "Broadcast"
                            elif report_var == 'ES':
                                report_med_broadcast = "Difusión"
                            elif report_var == 'DE':
                                report_med_broadcast = "Broadcast"
                            if report_var == 'EN' or report_var == 'ES' or report_var == 'DE':
                                report_med += "<tr><th>" + report_med_broadcast + "</th><th><a href=\"" + settings['report_prefix'] + "broadcast_chat_" + i.split('@')[0] + ".html" + "\" target=\"_blank\">" + i + gets_name(i) + "</a></th></tr>"
                                report_html = settings['report_prefix'] + "broadcast_chat_" + i.split('@')[0] + ".html"
                            sql_string_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            sql_count_copy += " AND messages.key_remote_jid LIKE '%" + i + "%'"
                            arg_group = ""
                            arg_user = i
                            result = cursor.execute(sql_count_copy)
                            result = cursor.fetchone()
                            print("\nNumber of messages: {}".format(str(result[0])))
                            print(Fore.RED + "--------------------------------------------------------------------------------" + Fore.RESET)
                            print(Fore.CYAN + "BROADCAST CHAT " + i + Fore.RESET + Fore.YELLOW + gets_name(i) + Fore.RESET)
                            report_group, color = participants(arg_user)

                        sql_consult = cursor.execute(sql_string_copy)
                        messages(sql_consult, result[0], report_html, local)
                        print()

                    if args.report:
                        index_report(report_med, "index.html", local)
                    print("\n" + prefix_info + "Finished")
                    print(prefix_info + "Messages processed: {0:d}    Group chats: {1:d}    User chats: {2:d}".format(count_messages, count_group_chats, count_user_chats), end='')
                    if settings['debug_warnings_enable']:
                        print("    Warnings: {0:d}".format(count_warnings), end='')
                    if settings['debug_errors_enable']:
                        print("    Errors: {0:d}".format(count_errors), end='')
                    print()
                    exit()

                print("Loading data ...")
                result = cursor.execute(sql_count)
                result = cursor.fetchone()
                print("Number of messages: {}".format(str(result[0])))
                sql_consult = cursor.execute(sql_string)
                messages(sql_consult, result[0], report_html, local)
                print("\n" + prefix_info + "Finished")

            except Exception as e:
                print(prefix_error, e)
                count_errors += 1

        elif args.info:

#            if args.output:
#                local = r"{}".format(args.output)
#            else:
#                local = os.getcwd() + "/"

            if args.wa_file:
                names(args.wa_file)
            cursor, cursor_rep = db_connect(args.database)
            if args.report:
                report_var = args.report
                get_configs()
            else:
                report_var = "None"
            info(args.info, local)

        elif args.extract:
            try:
#                if args.output:
#                    local = args.output
#                else:
#                    local = os.getcwd() + "/"

                cursor, cursor_rep = db_connect(args.database)
                print("Calculating number of images to extract")
                epoch_start = "0"
                """ current date in Epoch milliseconds string """
                epoch_end = str(1000 * int(time.mktime(time.strptime(time.strftime('%d-%m-%Y %H:%M:%S'), '%d-%m-%Y %H:%M:%S'))))

                if args.time_start:
                    epoch_start = 1000 * int(time.mktime(time.strptime(args.time_start, '%d-%m-%Y %H:%M:%S')))
                if args.time_end:
                    epoch_end = 1000 * int(time.mktime(time.strptime(args.time_end, '%d-%m-%Y %H:%M:%S')))

                sql_string = ""
                if args.user_all:
                    sql_string += " AND (messages.key_remote_jid LIKE '%" + str(args.user_all) + "%@s.whatsapp.net' OR messages.remote_resource LIKE '%" + str(args.user_all) + "%@s.whatsapp.net' )"
                elif args.user:
                    sql_string += " AND (messages.key_remote_jid LIKE '%" + str(args.user) + "%@s.whatsapp.net')"
                elif args.group:
                    sql_string += " AND messages.key_remote_jid LIKE '%" + str(args.group) + "%'"

                sql_count = "SELECT COUNT(*) FROM messages LEFT JOIN message_thumbnails ON messages.key_id = message_thumbnails.key_id WHERE messages.timestamp" \
                            " BETWEEN " + str(epoch_start) + " AND " + str(epoch_end) + " AND messages.media_wa_type IN (1, 3, 9, 13) " + sql_string + ";"
                cursor.execute(sql_count)
                result = cursor.fetchone()
                print(result[0], "Images found")
                sql_string_extract = "SELECT messages.key_id, messages.media_wa_type, messages.thumb_image, messages.raw_data, messages.timestamp, message_thumbnails.thumbnail, messages.key_remote_jid, messages.remote_resource, messages._id FROM messages LEFT JOIN message_thumbnails " \
                                     "ON messages.key_id = message_thumbnails.key_id WHERE messages.timestamp BETWEEN " + str(epoch_start) + " AND " + str(epoch_end) + " AND messages.media_wa_type IN (1, 3, 9, 13) " + sql_string + ";"
                sql_consult_extract = cursor.execute(sql_string_extract)
                extract(sql_consult_extract, result[0], local)
            except Exception as e:
                print(prefix_error + "Error extracting:", e)
                count_errors += 1

        elif args.database:
            if args.wa_file:
                names(args.wa_file)
                db_connect(args.database)

