#!/bin/env python3
# Rui Carmo, 2017
# Miscellaneous helpers for NLTK

from operator import itemgetter
from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem.porter import PorterStemmer
from nltk.stem import RSLPStemmer
from sys import maxunicode
from unicodedata import category
from logging import getLogger
from traceback import format_exc

log = getLogger()

STOPWORDS = {'en': stopwords.words('english'), 
             'pt': stopwords.words('portuguese')}

STEMMERS = {'en': PorterStemmer(),
            'pt': RSLPStemmer()}

# RAKE extractor - requires python -m nltk.downloader stopwords punkt 

# Build a full unicode punctuation dictionary based on glyph category 
# (strings.punctuation doesn't cut it)
PUNCTUATION = dict.fromkeys([i for i in range(maxunicode) if category(chr(i)).startswith('P')])

def _extract_phrases(sentences, language="english"):
    """Extract phrases from a list of sentences"""

    def is_punctuation(word):
        return len(word) == 1 and ord(word) in PUNCTUATION

    lang_stopwords = set(stopwords.words(language))

    phrase_list = []
    for sentence in sentences:
        # NOTE: word_tokenize can't quote cope with rich quotes, 
        # so we'll need to clean up after it deals with punctuation
        words = map(lambda x: "|" if x in lang_stopwords else x, word_tokenize(sentence.lower(), language))
        phrase = []
        for word in words:
            if word == "|" or is_punctuation(word):
                if len(phrase) > 0:
                    phrase_list.append(phrase)
                    phrase = []
            else:
                phrase.append(word.translate(PUNCTUATION)) # remove unicode quotes
    return phrase_list


def _score_words(phrase_list):
    """Score words based on frequency"""

    def is_numeric(word):
        # NOTE: this is a quick and dirty way to cope with multi-digit figures
        # but will be confused by currency
        try:
            int(word.replace(',', '').replace('.', ''))
            return True
        except ValueError:
            return False

    word_freq = FreqDist()
    word_degree = FreqDist()

    for phrase in phrase_list:
        degree = len(list(filter(lambda x: not is_numeric(x), phrase))) - 1
        for word in phrase:
            word_freq[word] += 1
            word_degree[word] += degree

    for word in word_freq.keys():
        word_degree[word] = word_degree[word] + word_freq[word] # itself
    
    # word score = deg(w) / freq(w)
    word_scores = {}
    for word in word_freq.keys():
        word_scores[word] = word_degree[word] / word_freq[word]
    return word_scores


def _score_phrases(phrase_list, word_scores):
    """Score a phrase by tallying individual word scores"""

    phrase_scores = {}
    for phrase in phrase_list:
        phrase_score = 0
        # cumulative score of words
        for word in phrase:
            phrase_score += word_scores[word]
        phrase_scores[" ".join(phrase)] = phrase_score
    return phrase_scores


def extract_keywords(text, language="en", scores=False):
    """RAKE extractor"""

    try:
        lang = {"en": "english",
                "pt": "portuguese"}[language]
    except KeyError:
        log.error(format_exc())
        return
                
    sentences = sent_tokenize(text, lang)
    phrase_list = _extract_phrases(sentences, lang)
    word_scores = _score_words(phrase_list)
    phrase_scores = _score_phrases(phrase_list, word_scores)
    sorted_scores = sorted(phrase_scores.items(), key=itemgetter(1), reverse=True)
    if scores:
        return sorted_scores
    else:
        return list(map(lambda x: x[0], sorted_scores))


def tokenize(plaintext, language):
    """tokenize into stemmed tokens"""

    try:
        stop_words = STOPWORDS[language]
        stemmer = STEMMERS[language]
    except KeyError:
        log.error(format_exc())
        return

    # Tokenize, remove stop words and stem
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = [stemmer.stem(i) for i in tokenizer.tokenize(plaintext.lower()) if not i in stop_words]
    return tokens