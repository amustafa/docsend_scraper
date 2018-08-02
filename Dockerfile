############################################################
# Dockerfile to build Flask App
# Based on
############################################################

# Set the base image
FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./docsend_scraper_web" ]

EXPOSE 8000

