======================
Command Line Interface
======================


The command line interface is very simple.


    python docsend_scraper [-ge EMAIL]  [DOC_ID_OR_URL] [-e EMAIL] [-p PASSCODE]


+-------+--------------+------------------------------------------------------------------------------------+
| Arg   | Arg Name     | Description                                                                        |
+=======+==============+====================================================================================+
|   -ge | Global Email | an email to use for every document in the list unless otherwise specified.         |
+-------+--------------+------------------------------------------------------------------------------------+
|  -e   |     Email    | Sets the email for the preceding document. Takes precendence over the global email |
+-------+--------------+------------------------------------------------------------------------------------+
| -p    | Passcode     | sets the passcode for the preceding document.                                      |
+-------+--------------+------------------------------------------------------------------------------------+

