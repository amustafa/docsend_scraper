import jinja2
import os
import asyncio
from sanic import Sanic
from sanic.response import json, html, stream, raw
from reportlab.pdfgen import canvas
import docsend_scraper
from io import BytesIO


__root_location__ = os.path.realpath(os.path.dirname(__file__))

TEMPLATES_FOLDER = os.path.join(__root_location__, 'templates')

_templateLoader = jinja2.FileSystemLoader(searchpath=TEMPLATES_FOLDER)
templateEnv = jinja2.Environment(loader=_templateLoader)

app = Sanic()
app.static('/js', os.path.join(__root_location__, 'static/js'))
app.static('/img', os.path.join(__root_location__, 'static/img'))
app.static('/css', os.path.join(__root_location__, 'static/css'))
app.static('/vendor', os.path.join(__root_location__, 'static/vendor'))

DOC_INFO_CACHE = {}


@app.route('/')
def index(request):
    template = templateEnv.get_template('index.html')
    html_content = template.render()
    return html(html_content)


@app.route('/is_valid_doc_id/<doc_id>')
def is_valid_doc_id(doc_id):
    is_valid = docsend_scraper.is_valid_doc_id(doc_id)
    return json({'result': is_valid})


@app.route('/get_document_info/<doc_id>')
async def get_document_info(request, doc_id):
    doc_info = await docsend_scraper.gather_document_info(doc_id)
    del doc_info['html']
    print(doc_id, doc_info)
    global DOC_INFO_CACHE
    DOC_INFO_CACHE[doc_id] = doc_info
    return json(doc_info)


@app.route('/download2/<doc_id>')
async def download_docsend(request, doc_id):
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
    global DOC_INFO_CACHE
    if doc_id in DOC_INFO_CACHE:
        doc_info = DOC_INFO_CACHE[doc_id]
    else:
        doc_info = await docsend_scraper.gather_document_info(doc_id)

    cookies = doc_info['cookies']

    email = passcode = None
    if doc_info['passcode_required']:
        if 'passcode' in request.args:
            passcode = request.args['passcode']
        else:
            return json(
                {'message': 'Missing Information: Passcode'},
                status=400
            )

    if doc_info['email_required']:
        if 'email' in request.args:
            email = request.args['email']
        else:
            return json(
                {'message': 'Missing Information: Email'},
                status=400
            )

    try:
        c = await docsend_scraper.download_docsend(doc_info, email, passcode)
    except docsend_scraper.AuthError:
        return json(
            {
                'message': 'Authentication Error',
                'id': doc_id
            },
            status=400
        )

        # Authenticate
    # if doc_info['email_required'] or doc_info['passcode_required']:
    #     auth_response = docsend_scraper.authenticate_cookie(
    #         doc_info['url'],
    #         cookies,
    #         doc_info['authenticity_token'],
    #         email, passcode)

    #     if auth_response.status_code not in [200, 302] \
    #             or "review the problems" in auth_response.text:
    #         return json(
    #             {
    #                 'message': 'Authentication Error',
    #                 'id': doc_id
    #             },
    #             status=400
    #         )

    # Retrieve Image Urls
    image_urls = await docsend_scraper.get_document_img_urls(doc_info)

    # Download Images
    imgs_coros = []
    for image_url in image_urls:
        imgs_coros.append(
            docsend_scraper.download_image_for_document(cookies, image_url))
    imgs = await asyncio.gather(*imgs_coros)

    # Generate PDF
    output_filename = f'Docsend-{doc_id}.pdf'
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    for img in imgs:
        c.setPageSize(img.size)
        c.drawInlineImage(img, 0, 0)
        c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    async def streaming_fn(response):
        response.write(pdf)

    headers = {
        'Content-Disposition': 'attachment; filename="{}"'.format(
            output_filename)
    }
    return stream(streaming_fn, content_type='application/pdf',
                  headers=headers)


@app.route('/download/<doc_id>')
async def download_docsend(request, doc_id):
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
    global DOC_INFO_CACHE
    if doc_id in DOC_INFO_CACHE:
        doc_info = DOC_INFO_CACHE[doc_id]
    else:
        doc_info = await docsend_scraper.gather_document_info(doc_id)

    email = passcode = None
    if 'passcode' in request.args:
        passcode = request.args['passcode']
    if 'email' in request.args:
        email = request.args['email']

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    try:
        await docsend_scraper.download_docsend(doc_info, email, passcode,
                                               output_canvas=c)
    except docsend_scraper.InfoRequiredError as e:
        if e.passcode_required:
            return json(
                {'message': 'Missing Information: Passcode'},
                status=400
            )
        else:
            return json(
                {'message': 'Missing Information: Email'},
                status=400
            )

    except docsend_scraper.AuthError:
        return json(
            {
                'message': 'Authentication Error',
                'id': doc_id
            },
            status=400
        )

    pdf = buffer.getvalue()
    buffer.close()

    async def streaming_fn(response):
        response.write(pdf)
    output_filename = f'Docsend-{doc_id}.pdf'
    headers = {
        'Content-Disposition': 'attachment; filename="{}"'.format(
            output_filename)
    }
    return stream(streaming_fn, content_type='application/pdf',
                  headers=headers)
