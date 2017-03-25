FROM rcarmo/alpine-python:3.6-onbuild

RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords rslp pattern

ADD . /app
WORKDIR /app
EXPOSE 8000
