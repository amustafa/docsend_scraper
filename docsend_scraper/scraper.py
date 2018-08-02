import os
import io
import json
import asyncio
import requests
import aiohttp
from PIL import Image
from configparser import ConfigParser
from reportlab.pdfgen import canvas
from .exceptions import InfoRequiredError, AuthError
from . import doc_info


__root_location__ = os.path.realpath(os.path.dirname(__file__))
CONFIG = ConfigParser()

CONFIG.read(os.path.join(__root_location__, 'config.ini'))

BASE_URL = CONFIG['DEFAULT']['base_url']
REQUEST_HEADERS_FILE_LOC = CONFIG['DEFAULT']['request_headers_file']


# Load headers that will be used with all the queries
with open(os.path.join(__root_location__, REQUEST_HEADERS_FILE_LOC), 'r') as f:
    HEADERS = json.load(f)


def is_valid_doc_id(doc_id, request_response=None):
    """
    Attempts to pull the main page of the doc with doc_id. If it fails,
    this returns false.

    :doc_id: (str) id of the document
    :request_response: (requests.response) Option response in case this action
                            was already performed elsewhere.

    :returns: (bool) True if the request was successful
    """
    if request_response is None:
        doc_url = doc_info.get_url_from_id(doc_id)
        resp = requests.get(doc_url, headers=HEADERS)
    if resp.status_code == 200:
        return True
    else:
        return False


async def get_document_html(doc_id):
    """
    Requests the main html page of the document. Mainly used to collect
    information about the document to be scraped.

    :doc_id: (str) id of the document
    """
    doc_url = doc_info.get_url_from_id(doc_id)
    document_url_response = requests.get(doc_url, headers=HEADERS)
    document_html = document_url_response.text
    return document_html


async def gather_document_info(doc_id):
    """
    Collects all the needed information from the document text to be used
        in other parts of the program.

    Note: If doc_id is invalid, this will reponse with is_valid being False.

    :doc_id: (str) id of the document

    :returns: (dict) document information
    """
    doc_url = doc_info.get_url_from_id(doc_id)
    document_url_response = requests.get(doc_url, headers=HEADERS)
    if document_url_response.status_code == 200:
        document_html = document_url_response.text
        cookies = document_url_response.cookies

        # Check Authentication requirements
        passcode_required = doc_info.check_passcode_required(document_html)
        email_required = doc_info.check_email_required(document_html)

        info = {
            'id': doc_id,
            'url': doc_url,
            'html': document_html,
            'cookies': cookies,
            'email_required': email_required,
            'passcode_required': passcode_required,
            'page_count': doc_info.find_page_count(document_html),
            'authenticity_token': doc_info.find_auth_token(document_html),
            'is_valid': True
        }
    else:
        info = {
            'id': doc_id,
            'url': doc_url,
            'is_valid': False
        }

    return info


def authenticate_cookie(doc_info, cookies, authenticity_token,
                        email, passcode=None):
    """
    Registers the email and optionally a passcode with docsend to
    get the document.

    :doc_info: (dict) dict containing the url of the document
    :cookies: (dict) cookies to authenticate
    :authenticity_token: (str) authenticity token taken from the document html
    :email: (str) email to use in auth
    :passcode: (str) Optional passcode to auth

    :returns: (request.Response)
    """
    form_data = {
        "utf8": "✓",
        "_method": "patch",
        "authenticity_token": authenticity_token,
        "visitor[email]": email,
        "commit": "Continue"
    }

    if passcode is not None:
        form_data['visitor[passcode]'] = passcode

    doc_url = doc_info['url']
    document_url_response = requests.post(
        doc_url, headers=HEADERS, data=form_data, cookies=cookies)

    return document_url_response


async def get_document_img_urls(doc_info):
    """
    Using the document info from gather_document_info, this gets all the image
    urls from the server.

    :doc_info: (dict) dict containing the info of the document

    :returns: (list) a list of urls retrieved from the server than can be used
                        to pull the images in the document.
    """
    image_url_coros = []
    doc_url = doc_info['url']
    cookies = doc_info['cookies']
    page_count = doc_info['page_count']

    async with aiohttp.ClientSession(headers=HEADERS, cookies=cookies) \
            as session:
        # Pages start at count 1
        for page in range(1, page_count+1):
            doc_info_link = f"{doc_url}/page_data/{page}"
            image_url_coros.append(session.get(doc_info_link))
            # image_info = requests.get(
            #     doc_info_link, cookies=cookies, headers=HEADERS)

        # Gather coros to get them all at the same time.
        image_url_responses = await asyncio.gather(*image_url_coros)
        images_info = await asyncio.gather(*[resp.json()
                                             for resp in image_url_responses])
        image_urls = [image_info['imageUrl'] for image_info in images_info]

        return image_urls


async def download_image_for_document(cookies, image_url):
    """
    Given a cookie and image url, this returns a PIL.Image.

    :cookies: (dict) dict with cookie data for the remote server.
                Note: Cookie should already be authenticated
    :image_url: (str) url to pull image from

    :return: (PIL.Image) image from the server.
    """
    async with aiohttp.ClientSession(headers=HEADERS, cookies=cookies) \
            as session:
        img_response = await session.get(image_url)
        img_data = await img_response.read()
        return Image.open(io.BytesIO(img_data))


async def download_docsend_with_doc_id(doc_id, email=None, passcode=None,
                                       output_path=None, output_canvas=None,
                                       save_output=True):
    doc_info = await gather_document_info(doc_id)
    return await download_docsend(doc_info, email, passcode,
                                  output_path, output_canvas, save_output)


async def download_docsend(doc_info, email=None, passcode=None,
                           output_path=None, output_canvas=None,
                           save_output=True):
    """
    Downloads the document from the server and converts to a pdf.
    Notes:
        * email and passcode are not used if function does not detect it
            is needed.
        * If canvas is provided then output_path is not utilized since the
            path must be designated at the time of creation.


    :doc_id: (str) id of the document to be downloaded
    :email: (str) email to use to authenticate if needed
    :passcode: (str) passcode to use to authenticate if needed

    :output_path: (str) path to use when saving file.
    :output_canvas: (reportlab.pdfgen.canvas.Canvas) preconfigured canvas to
                    save the downloaded document to.
    :save_output: (bool) flag to save the output before exiting function
    """
    # Gather basic information and get cookies
    doc_id = doc_info['id']
    cookies = doc_info['cookies']

    if doc_info['passcode_required'] and passcode is None:
        raise InfoRequiredError(doc_id, passcode_required=True)
    elif doc_info['email_required'] and email is None:
        raise InfoRequiredError(doc_id)

    # Authenticate
    if doc_info['email_required'] or doc_info['passcode_required']:
        auth_response = authenticate_cookie(doc_info, cookies,
                                            doc_info['authenticity_token'],
                                            email, passcode)
        if auth_response.status_code not in [200, 302] \
                or "review the problems" in auth_response.text:
            raise AuthError(auth_response.status_code)

    # Retrieve Image Urls
    image_urls = await get_document_img_urls(doc_info)

    # Download Images
    imgs_coros = []
    for image_url in image_urls:
        imgs_coros.append(download_image_for_document(cookies, image_url))
    imgs = await asyncio.gather(*imgs_coros)

    # Generate PDF
    output_path = '' if output_path is None else output_path
    output_filename = f'Docsend-{doc_id}.pdf'
    output_file = os.path.join(output_path, output_filename)
    if output_canvas is None:
        c = canvas.Canvas(output_file)
    else:
        c = output_canvas

    c.setTitle(doc_id)
    for img in imgs:
        c.setPageSize(img.size)
        c.drawInlineImage(img, 0, 0)
        c.showPage()
    if save_output:
        c.save()
    return c
