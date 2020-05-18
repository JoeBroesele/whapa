Changelog
====
All notable changes to this project will be documented in this file.

May 2020

    [+] whapa-gui.py v1.21
        [-] Version number incremented.
    [+] whapa.py v1.7
        [-] Option to use custom emoji implemented.
        [-] Improved formatting of text: Spaces are now preserved.
        [-] Some bug fixes.

    [+] whapa-gui.py v1.20
        [-] Option for reports in German added.
    [+] whapa.py v1.6
        [-] Reports can now be created in German.
        [-] Fixed the Google real time location for reports in English.
        [-] Some fixes and improvements, mainly related to support different languages.
        [-] Error handling of missing picutres implemented.
        [-] Timestamps include seconds.

    [+] General:
        [-] Central definition of versions in 'whautils.py'.
    [+] whapa-gui.py v1.19
        [-] Version number incremented.
    [+] whapa.py v1.5
        [-] Option added to turn the HTML 'alt' tag for images on or off. If off, a broken image
            symbol will be displayed instead of the alternative text, which may be preferrable.
        [-] Improved generation of links from URLs in messages.
        [-] Unified HTML report templates for English and Spanish.
        [-] Several improvements and fixes in the generation of the reports.

    [+] whapa-gui.py v1.18
        [-] Version number incremented.
    [+] whapa.py v1.4
        [-] Better differentiation of system messages, eliminating some errors.
        [-] Line breaks in messages are now displayed in the report.
        [-] Optimized the HTML layout of the reports.
        [-] Improved processing of contact vCards with the option to save them as files and
            display the vCard information on tooltips in raw and pretty format.

    [+] whapa-gui.py v1.17
        [-] Improved update notification.
    [+] whapa.py v1.3
        [-] Option added to include profile pictures in the reports and the report index.
        [-] Links to media are now opened in the same browser window.

    [+] General:
        [-] New 'whautils.py' library for improved creation and reading of 'settings.cfg' file.
        [-] Added the shell script 'reports2pdf.sh' to convert all HTML reports into PDF files.
    [+] whapa-gui.py v1.16
        [-] Fixed update notification.
    [+] whapa.py v1.2
        [-] More options available in 'settings.cfg':
            size of logo, prefix of report files, background image for the index and report files
        [-] Thumbnail images are now displayed maintaining the aspect ratio.
        [-] Removed unused code from reports.

Apr 2020

    [+] General:
        [-] Made all Python scripts executable.
        [-] Ignore backup files and WhatsApp files, databases, media and report in git.
        [-] Added '.pylintrc' files to filter out some warnings from pylint3.
    [+] whacipher.py v1.1
        [-] Replaced 'Crypto.Cipher' with 'Cryptodome.Cipher'.
    [+] whagodri.py v1.1
        [-] Ask for Google password in console, if 'passw' in 'settings.cfg' is empty or 'yourpassword'.
    [+] whapa.py v1.1
        [-] Save separate thumbnail images for videos.
        [-] Added background image in English report index.
        [-] Omit logo, if 'logo' is empty in 'settings.cfg'.
        [-] Omit header table if 'record', 'unit', 'examiner' and 'notes' in 'settings.cfg' is empty.
        [-] Include chat name in the HTML title.
        [-] Reproducible color assignment in group chats.

Mar 2020

    [+] whapa-gui.py v1.15
    [+] whagodri.py
        [-] Fixed Google Drive crash

Oct 2019

    [+] whapa-gui.py v1.14
        [-] fixed bug in downloading files individually

    [+] whapa-gui.py v1.13
        [-] whagodri tab changes, Only one download method and new options for downloading files.
    [+] whagodri.py
        [-] Removed restriction from '00' or '+' in the settings file.
        [-] Videos, images, audios, backups, documents can be recovered independently.

Sep 2019

    [+] The whole project has been updated and improved to python3, now it is managed from a graphical interface.
    [+] Fixed major bugs
    [+] whapa-gui.py v1.12
        [-] Check at the beginning if there is any update
        [-] whagodri tab changes, Add two method to download (Original and Alternative)
        [-] whagodri tab changes, It's added option to choose an output path
    [+] whagodri.py v1.11
        [-] Fixed Limit of 5000 files to download.
        [-] It works with new google drive backup.

May 2019

    [+] whapa.py v0.6
        [-] Disappears the option to decrypt database (new tool)
    [+] whamerge.py v0.1 (replaces to a whademe.py)
        [-] Merge new fields
    [+] whacipher.py is added

May 2018

    [+] whapa.py v0.5
        [-] Improved parses speed
        [-] When parse the database extracts all thumbnails
        [-] Reports are sorted in "./reports" path
        [-] Make an index of the reports ("index.hml"), when you use the -a -r flag
        [-] Added flag "-e", Extract mode, extracts all media thumbnails of the database in "./thumbnails" path
        [-] Fix minor bugs
    [+] whademe.py v0.1
    [+] whagodri.py v0.1 (replaces to a whagdext3.py)

April 2018

    [+] whapa.py v0.4
        [-] Added flag "--update" to update WhatsApp Parser Tool
        [-] Added flag in message mode, "-ua" Show all messages mades by a number phone
        [-] Added flag in message mode, "-a" Show all chat messages classified by phone number, group number and broadcast list
        [-] Added System Message, when the number is a company
        [-] Added System Message, group description
    [+] whapa.py v0.3
        [-] Added in info mode, the phone numbers with which the user have interacted
        [-] Changed the format of some flags, now they are all in lowercase
        [-] Fix minor bugs

March 2018

    [+] whapa.py v0.2
        [-] Added interactive html report
        [-] Added pdf report
        [-] Added making reports in spanish or english language
        [-] If you have "wa.db" database translates the phone numbers with name
        [-] Fixed minor bugs
        [-] Removed whapas.py

February 2018

    [i] whapa.py v0.1
        [-] Fixed minor bugs
        [-] Added whapas.py

