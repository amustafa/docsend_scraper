"""
doc_info.py

All function here deal with the document's information but should not make
any contact with the server. As this library scrapes information, the function
here take the document text and use regex or string search to find the relevant
info.
"""
import re
from configparser import ConfigParser
import os

__root_location__ = os.path.realpath(os.path.dirname(__file__))
CONFIG = ConfigParser()
CONFIG.read(os.path.join(__root_location__, 'config.ini'))

BASE_URL = CONFIG['DEFAULT']['base_url']
PAGE_COUNT_REGEX = CONFIG['DEFAULT']['page_count_regex']
AUTH_TOKEN_REGEX = CONFIG['DEFAULT']['auth_token_regex']


def get_url_from_id(doc_id):
    """
    Gets the document url from the id. Does not check if it is a valid id.

    :doc_id: (str) id of the document
    :return: (str) url of the document
    """
    return f"{BASE_URL}/view/{doc_id}"


def get_id_from_url(url):
    """
    Gets the document id from the url. Does not check if it is a valid url.

    :url: (str) url to be scraped
    :return: (str) id of the document
    """
    doc_id_regex = r'.*docsend.com/view/(?P<doc_id>.*)'
    search = re.search(doc_id_regex, url)
    if search:
        doc_id = search.group('doc_id')
        return doc_id


def check_passcode_required(document_html):
    """
    If a passcode is required, the document text will contain the string
        "visitor[passcode]".

    :document_html: (str) text from the view page of the document

    :return: (bool) if a passcode is required to access document
    """
    if "visitor[passcode]" in document_html:
        return True
    else:
        return False


def check_email_required(document_text):
    """
    If an email is required, the document text will contain the string
        "visitor[email]".

    :document_html: (str) text from the view page of the document

    :return: (bool) if an email is required to access document
    """
    if "visitor[email]" in document_text:
        return True
    else:
        return False


def find_auth_token(document_html):
    """
    A cookie authentication requires and auth token from the document.
    This searches and returns it.

    :document_html: (str) text from the view page of the document

    :returns: (str) auth token from the document. None if it couldn't find one
    """
    search_result = re.search(AUTH_TOKEN_REGEX, document_html)
    if search_result:
        return search_result.group('auth_token')


def find_page_count(document_html):
    """
    Searches the initial html document to get the page count.

    :document_html: (str) text response from the document's view page.

    :return: (int) page count
    """
    search_result = re.search(PAGE_COUNT_REGEX, document_html)
    if search_result:
        return int(search_result.group('page_count')) - 1
