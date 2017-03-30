from operator import itemgetter
from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from sys import maxunicode
from unicodedata import category

# RAKE extractor - requires python -m nltk.downloader stopwords punkt 

PUNCTUATION = dict.fromkeys([i for i in range(maxunicode) if category(chr(i)).startswith('P')])

def _extract_phrases(sentences, language="english"):
    def is_punctuation(word):
        return len(word) == 1 and ord(word) in PUNCTUATION
    
    lang_stopwords = set(stopwords.words(language))

    phrase_list = []
    for sentence in sentences:
        # NOTE: word_tokenize can't quote cope with rich quotes, so we'll need to clean up after it deals with punctuation
        words = map(lambda x: "|" if x in lang_stopwords else x, word_tokenize(sentence.lower(), language))
        phrase = []
        for word in words:
            if word == "|" or is_punctuation(word):
                if len(phrase) > 0:
                    phrase_list.append(phrase)
                    phrase = []
            else:
                print(word)
                phrase.append(word.translate(PUNCTUATION)) # remove unicode quotes
    return phrase_list


def _score_words(phrase_list):
    def is_numeric(word):
        try:
            int(word.replace(',','').replace('.',''))
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
    phrase_scores = {}
    for phrase in phrase_list:
        phrase_score = 0
        # cumulative score of words
        for word in phrase:
            phrase_score += word_scores[word]
        phrase_scores[" ".join(phrase)] = phrase_score
    return phrase_scores


def extract_keywords(text, language="en", scores=False):
    lang = {"en": "english",
            "pt": "portuguese"}[language]
    sentences = sent_tokenize(text, lang)
    phrase_list = _extract_phrases(sentences, lang)
    word_scores = _score_words(phrase_list)
    phrase_scores = _score_phrases(phrase_list, word_scores)
    sorted_scores = sorted(phrase_scores.items(), key=itemgetter(1), reverse=True)
    if scores:
        return sorted_scores
    else:
        return list(map(lambda x: x[0], sorted_scores))