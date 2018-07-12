FROM python:2.7.14-alpine3.6

MAINTAINER zxl, <xinleizhang1997@gmail.com>

LABEL "OS_version"="alpine:3.6"
LABEL "Python_version"="2.7.14" 

RUN apk -U add \
    g++ \
    gcc \
    git \
    libffi-dev \
    openssl-dev \
    python-dev

RUN pip install elastalert==0.1.32

COPY "./elastalert_modules/" "/usr/local/lib/python2.7/site-packages/elastalert_modules"


ENTRYPOINT ["/usr/local/bin/elastalert"]

