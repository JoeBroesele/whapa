<p align="center">
  <img  src="https://github.com/JoeBroesele/whapa/blob/master/doc/whapa.png">
</p>

WhatsApp Parser Toolset
====
Updated: May 2020

WhatsApp Messenger Version 2.19.244

Whapa is a forensic graphical toolset for analyzing WhatsApp in Android. All the tools have been
written in Python 3.X and have been tested on linux and windows 10 systems.

Note: Whapa provides 10x more performance and fewer bugs on linux systems than on windows.

Whapa is included as standard in distributions such as Tsurugi Linux (Digital Forensics) and
BlackArch Linux (Penetration Testing).

Whapa toolset is divided in four tools:

* **Whapa**     (WhatsApp Parser)
* **Whamerge**  (WhatsApp Merger)
* **Whagodri**  (Whataspp Google Drive Extractor)
* **Whacipher** (WhatsApp Encryption/Decryption)


**Do you like this project? Support it by donating**
- ![Paypal](https://raw.githubusercontent.com/reek/anti-adblock-killer/gh-pages/images/paypal.png) Paypal: [Donate](https://paypal.me/b16f00t?locale.x=es_ES)
- ![btc](https://github.com/nullablebool/crypto-icons/blob/master/16x16/BTC-16.png) Bitcoin: 13h2rupiKBr8bFygKdCunfXrn2pAaVoaTQ


Changelog
====
https://github.com/JoeBroesele/whapa/blob/master/doc/CHANGELOG.md


Prerequisites
====
Ubuntu 20.04:

    sudo apt install git
    sudo apt install python3-colorama python3-gpsoauth python3-pycryptodome python3-tk
    sudo apt install

Ubuntu 18.04:

    sudo apt install git
    sudo apt install python3-colorama python3-pip python3-pycryptodome python3-tk

Optional, for automatic conversion of the reports to PDF files:

    sudo apt install wkhtmltopdf


Installation
====
You can download the latest version of whapa by cloning the GitHub repository:

    git clone https://github.com/JoeBroesele/whapa.git
then:

    pip3 install -r ./doc/requirements.txt


Start
====
If you use Linux system:
* python3 whapa-gui.py

If you use Windows system:
* python whapa-gui.py
    or
* click on whapa-gui.bat

<p align="center">
  <img src="https://raw.githubusercontent.com/JoeBroesele/whapa/master/doc/software.jpg" width="720" height="576">
</p>


WHAPA
====
```whapa.py``` is an Android WhatsApp database parser which automates the process and presents the
data handled by the Sqlite database in a way that is comprehensible to the analyst.

If you copy the ```wa.db``` database into the same directory as the script, the phone number will be
displayed along with the name.

Please note that this project is an early stage. As such, you could find errors. Use it at your own
risk!


Reports
=====
To create reports the first thing you need to do is to configure the file ```./cfg/settings.cfg```.
E.g.:

    [report]
    logo = ./cfg/logo.png
    logo_height = 128
    company = Foo S.L
    record = 1337
    unit = Research group
    examiner = B16f00t
    notes = Chat maintained between the murderer and the victim
    report_prefix = report_
    bg_index = ./images/background-index.png
    bg_report = ./images/background.png
    profile_pics_enable = yes
    preview_pics_size = 100
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

Here you must put our company logo, company or unit name, as well as the assigned registration
number, unit or group where you belong, who is the examiner and you can also specify notes on the
report.

Hints:
* By leaving ```logo``` blank, the logo and company name will be omitted from the reports.  
* By leaving ```record```, ```unit```, ```examiner``` and ```notes``` blank, the header table will
  be omitted from the reports.  
* The directory and file locations in ```./cfg/settings.cfg``` can either be relative to the
  WhatsApp Parser Toolset base directory or you can specify an absolut path.
* To use custom emoji, you need to add the emoji images in PNG format to the directory defined by
  ```custom_emoji_dir```. By default, it is ```./images/emoji```.  
  Hints:  
    - Emoji can e.g. be downloaded from these locations:  
      [Emojipedia - WhatsApp Emoji](https://emojipedia.org/whatsapp/)  
      [OpenMoji](https://openmoji.org/)  
    - The names of the emoji files must be like this: ```0023-FE0F-20E3.png```, ```1F44B-1F3FB.png```  
      I.e. Upper case hexadecimal codes like in
      [emoji-test.txt](https://unicode.org/Public/emoji/13.0/emoji-test.txt)
      with 4 or 5 digits. If an emoji uses more than one code, the codes are combined with dashes
      ```-```. The file extension is ```.png```.
    - For an overview of official Unicode emoji, please see:  
      [Full Emoji List, v13.0](https://unicode.org/emoji/charts/full-emoji-list.html)  
    - For chats held with older versions of WhatsApp prior to early 2015, you will need
      emoji images with non-standard codes E000 ... EFFF. You can find them
      [here](https://github.com/andreas-mausch/whatsapp-viewer/tree/master/resources/smileys).
      To use these emoji images, please remove the leading '0' from the file names and change
      the file extension to lower case, i.e. ```0E001.PNG``` -> ```E001.png```.  
      Alternatively, you can extract them from the WhatsApp APK file. The best choice for this
      purpose is
      [WhatsApp Messenger 2.12.90](https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/whatsapp-2-12-90-release/whatsapp-2-12-90-android-apk-download/).
      Also these file you need to rename as described above.

To generate the report, you must specify the option "English", "Spanish" or "German" if you want
the report in English, Spanish or "German".

If you copy the ```wa.db``` database into the same directory as the script, the phone number will be
displayed along with the name.
For the report to contains the images, videos, documents... you must copy the "WhatsApp/Media"
folder of your phone to the whapa directory, otherwise the program will generate thumbnails.

If you want to print the document or create the report in PDF, it is recommended to set the print
option -> scale the view <= 60% or 70%, otherwise the report will be displayed too large.

In order to automatically convert all reports and the report index into PDF files, simply run the
script ```./tools/reports2pdf.sh```.


WHAMERGE
====
```whamerge``` is a tool to joins backups in a new database, to be able to be analyzed and obtain
more information, such as deleted groups, messages, etc...

Warning: Do not join restored databases with old copies, since they repeat the same ids and the copy
will not be done correctly.


WHAGODRI
=====
```whagodri.py``` is a tool which allows WhatsApp users on Android to extract their backed up
WhatsApp data from Google Drive.

Make sure of:
* Disable 2FA in your Google Account
* Download the latest version of whapa
* Install the requirements
* Settings:

Edit only the values of the./cfg/settings.cfg file

        [auth]
        gmail = alias@gmail.com
        passw = yourpassword
        devid = Device ID (optional, if specified get more information)
        celnumbr = BackupPhoneNumber (ex. 3466666666666)
* If you request it, log in to your browser and then click here:
  [https://accounts.google.com/DisplayUnlockCaptcha](https://accounts.google.com/DisplayUnlockCaptcha)
* If you have problems remove special characters in your password.


WHACIPHER
=====
```whacipher.py``` is a tool which allows decrypt or encrypt WhatsApp database. You must have the
key of your phone to decrypt, and additionally a encrypted database as reference to encrypt a new
database.


Get in touch
=====
Acknowledgements, suggestions, languages, improvements...

Telegram Channel and discuss group

    https://t.me/bigfoot_whapa


Disclaimer
=====
The developer is not responsible, and expressly disclaims all liability for damages of any kind
arising from the use, reference or reliance on the software. The information provided by the
software is not guaranteed to be correct, complete and up-to-date.

