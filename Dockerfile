FROM rcarmo/alpine-python:3.6-onbuild

# Install nltk data we need
RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt rslp pattern averaged_perceptron_tagger

ADD . /app
WORKDIR /app
EXPOSE 8000
