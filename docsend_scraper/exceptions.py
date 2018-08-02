"""
exceptions.py

Exceptions used in scraper.
"""


class InfoRequiredError(ValueError):
    """
    Raised when a document needs more information. This always indicates an
    email is required. If passcode_required is True, then it also needs a
    passcode.
    """

    def __init__(self, doc_id, *args, passcode_required=False, **kwargs):
        self.doc_id = doc_id
        self.passcode_required = passcode_required
        ValueError.__init__(self, *args, **kwargs)

    def __str__(self):
        s = f'Document "{self.doc_id}" requires an email'
        if self.passcode_required:
            s = f"{s} and a passcode to access."


class AuthError(RuntimeError):
    """
    Raised when document authentication fails for any reason.
    """

    def __init__(self, response_code, *args, **kwargs):
        self.response_code = response_code
        RuntimeError.__init__(self, *args, **kwargs)
