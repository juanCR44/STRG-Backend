FROM python:3.10.0a1-alpine3.12

COPY requirements.txt /app/requirements.txt
RUN pip install pipenv
RUN pip install ez_setup
RUN apk add g++ jpeg-dev zlib-dev libjpeg make


RUN pip install --upgrade pip setuptools wheel
RUN apk --no-cache add musl-dev linux-headers g++
RUN apk add --no-cache --virtual .build-deps musl-dev linux-headers g++ gcc zlib-dev make python3-dev jpeg-dev
RUN pip install matplotlib

RUN set -ex \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

ADD . .

EXPOSE 8000

CMD [ "gunicorn", "--bind", ":8000", "--workers", "3", "core.wsgi:application"]
