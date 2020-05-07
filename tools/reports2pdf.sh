#!/bin/sh
#
# File: reports2pdf.sh
# Auth: Joe Broesele
# Mod.: Joe Broesele
# Date: 05 May 2020
# Rev.: 07 May 2020
#
# Convert HTML reports into PDF files.
#



# Configuration.
REPORTS_DIR="reports"
PDF_DIR="PDF"
MEDIA_DIR="Media"



# Set the working directory to the whapa directory, which is the parent
# directory of the script directory.
SCRIPT_DIR="`dirname $0`"
WORKING_DIR="`dirname ${SCRIPT_DIR}`"



# Check command line arguments.
if [ $# -ge 1 ]; then
    if [ "x$1" = "x-h" -o "x$1" = "x--help" ]; then
        echo "Convert HTML report files into PDF files."
        echo
        echo "Usage: `basename $0` [FILES]"
        echo
        echo "If no files are specified, all HTML files in the folder \`${REPORTS_DIR}' will be converted."
        echo
    else
        HTML_FILES=$@
    fi
else
    # Check if reports directory exists.
    if [ ! -d "${REPORTS_DIR}" ]; then
        echo "ERROR: Reports directory \`${REPORTS_DIR}' not found!"
        exit 1
    fi
    HTML_FILES=`/bin/ls "${WORKING_DIR}/${REPORTS_DIR}/"*.html`
fi



# Check if `wkhtmltopdf' is installed.
WKHTMLTOPDF=`which wkhtmltopdf 2>/dev/null`
if [ $? -ne 0 -o -z "${WKHTMLTOPDF}" ]; then
    echo "ERROR: Please install \`wkhtmltopdf'!"
    exit 1
fi



# Create PDF output directory.
mkdir -p "${WORKING_DIR}/${PDF_DIR}"
if [ ! -d "${WORKING_DIR}/${PDF_DIR}" ]; then
    echo "ERROR: Cannot access the PDF directory \`${WORKING_DIR}/${PDF_DIR}'!"
    exit 1
fi



# Increase the number of file descriptors.
ulimit -n 1048576



# Set custom options for `wkhtmltopdf'.
# Hints:
# - Increase the number of the option `--javascript-delay' if you get this
#   warning:
#       "Warning: Received createRequest signal on a disposed ResourceObject's
#       NetworkAccessManager. This might be an indication of an iframe taking
#       too long to load."
WKHTMLTOPDF_OPTIONS="--javascript-delay 1000"



# Convert file by file and replace absolute links with relative links in the
# PDF.
for html_file in ${HTML_FILES}; do
    pdf_file="${WORKING_DIR}/${PDF_DIR}/"`basename ${html_file} | sed -e "s/\.html$/.pdf/"`
    if [ ! -r "${html_file}" ]; then
        echo "ERROR: Cannot open file \`${html_file}'"
    else
        echo "***** Processing HTML file: \`${html_file}' *****"
        ${WKHTMLTOPDF} ${WKHTMLTOPDF_OPTIONS} "${html_file}" - | \
            sed -e "s/^\/URI (file:\/\/\/.*\/${REPORTS_DIR}\/\(.*\)\.html)$/\/URI (\1\.pdf)/" | \
            sed -e "s/^\/URI (file:\/\/\/.*\/${MEDIA_DIR}\/\(.*\))$/\/URI (..\/${MEDIA_DIR}\/\1)/" >| \
            "${pdf_file}"
    fi
done

