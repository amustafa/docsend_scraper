import sys
import asyncio
from . import scraper
import doc_info


async def main(id_list):
    coros = []
    for d in id_list:
        coros.append(scraper.download_docsend(*d))
    return await asyncio.gather(*coros)

id_list = []
global_email = None

next_is_passcode = False
next_is_email = False
next_is_global_email = False

for arg in sys.argv[1:]:
    if next_is_passcode:
        next_is_passcode = False
        id_list[-1][2] = arg

    elif next_is_email:
        next_is_email = False
        id_list[-1][1] = arg

    elif next_is_global_email:
        next_is_global_email = False
        assert global_email is None, 'global email can only be selected once'
        global_email = arg

    elif arg == "-e":
        next_is_email = True
    elif arg == "-ge":
        next_is_global_email = True
    elif arg == "-p":
        next_is_passcode = True

    else:
        if '.com' in arg:
            doc_id = doc_info.get_id_from_url(arg)
        else:
            doc_id = arg

        id_list.append([doc_id, None, None])

if global_email is not None:
    for d in id_list:
        if d[1] is None:
            d[1] = global_email

loop = asyncio.get_event_loop()
loop.run_until_complete(main(id_list))
