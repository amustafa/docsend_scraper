===============
Docsend Scraper
===============

Tools to download pdf documents from docsend.com

,,,,,,,,,
Parts
,,,,,,,,,

docsend_scraper python library
------------------------------
A python library built for scraping from docsend.com

Docsend Scraper Web
-------------------
A UI built using Sanic for downloading documents from docsend.com and uses the python library.

,,,,,,,,,
Deploy
,,,,,,,,,
Instructions for deployment.

Using Docker
------------------------------

This repo includes a Dockerfile for simple deployment. To run, use the following steps:

1. Install Docker (https://docs.docker.com/install/)
2. Start Docker Daemon
3. Enter the directory
4. Run: ``run_web_docker``

From FileSystem
----------------

1. Install python 3.6+ 
2. Download contents of this repo and enter directory
3. Run  ``install --no-cache-dir -r requirements.txt``
4. Run ``python docsend_scraper_web``

,,,,,,,,,
Docs
,,,,,,,,,
Includes design notes and implementation details that show how to use and install the tools.

Other Notes
-----------
Things that are missing from this repo are:

* Tests: In the interest of time, I didn't put in any tests
* setup.py: This should not be installed via pip
* This uses the basic Sanic server. In a production environment, I'd use Apache or Ngix

