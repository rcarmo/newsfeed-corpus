FROM rcarmo/alpine-python:3.6-onbuild

ADD . /app
WORKDIR /app
EXPOSE 8000