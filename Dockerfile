FROM rcarmo/ubuntu-python:3.6-onbuild-x86_64

# Install nltk data we need
RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt rslp averaged_perceptron_tagger

# Bake code into containers rather than use the Compose mount point
#ADD . /app
WORKDIR /app
EXPOSE 8000
