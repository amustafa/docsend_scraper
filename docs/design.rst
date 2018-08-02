==============
General Design
==============

Python Library
--------------
The python library breaks up the task of downloading a document into multiple steps.
Since there is a lot of I/O involved, to speed things up, everything is async using python's
asyncio library (python 3.4+). Python GIL would normally when waiting for a response from the but using the asyncio library it frees up the process to run other things while the system waits for remote responses.


Parts of a Scrape
-----------------

1. Getting the document id and url
    * The id is part of the url so knowing one means you know the other. 
    * A document and it's information is referenced everywhere by it's docId
2. Gathering information
    * This is where all the the document information is gathered, included email/passcode requirements, cookie information, and page count. 
3. Image Url Collecting
    * Docsend represents a documents as a series of images. Each image come from a url that has to be properly formed and authenticated. As a result, the url must be requested at download time. 
4. Image Downloads
    * Once all the image urls are collected, they are downloaded.
5. PDF Generation
    * The images are then combined to create a pdf



Web UI
------
The web ui works on the total task in very discrete chunks. This allows for load balancing if the need would ever arise.
