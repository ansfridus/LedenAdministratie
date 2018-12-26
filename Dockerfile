FROM python:3.5-alpine

# Set the file maintainer (your name - the file's author)
MAINTAINER Rients Brandsma

COPY LedenAdministratie /srv/LedenAdministratie

RUN apk update && \
    apk add nginx mariadb-dev zlib-dev gcc musl-dev jpeg-dev freetype-dev && \
    pip3 install --no-cache-dir -r /srv/LedenAdministratie/requirements.txt && \
    apk del gcc musl-dev && \
    pip install mysql-python

WORKDIR /srv
RUN mkdir static logs /run/nginx

COPY nginx.conf /etc/nginx/nginx.conf

# Port to expose
EXPOSE 80

# Copy entrypoint script into the image
WORKDIR /srv/LedenAdministratie
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
