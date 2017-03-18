FROM rcarmo/alpine-python:3.5-onbuild

ADD . /app
WORKDIR /app
EXPOSE 8000