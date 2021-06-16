#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""VyatSU bot sentiment module"""

import logging
from typing import List

import keras
import nltk
import numpy as np
import pymorphy2
import pickle
from keras.preprocessing.sequence import pad_sequences
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')

logging.basicConfig(
    #  filename='bot.log', filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)


class ModelStub():

    def predict(self, sent):
        return [0, 1, 0]


class SentimentModule():

    def __init__(self):
        try:
            self.model = keras.models.load_model('sent_model.h5')

            with open('sent_vectorizer.dmp', 'rb') as vf:
                self.vectorizer = pickle.load(vf)
                logger.info('-------------------------------')
        except OSError:
            logger.error('Not found SYNT model file')
            self.model = ModelStub()
            self.vectorizer = TfidfVectorizer(max_features=1)
            self.vectorizer.fit(['ааа ббб ввв'])

    morph = pymorphy2.MorphAnalyzer()
    MAXLEN = 50

    def normalize_sent(self, sent: str) -> str:
        """ Normalize words in text. Remove punktuation."""
        sent.replace('\n', ' ')
        words = nltk.word_tokenize(sent)
        word_tokens = []
        filter_fn = lambda x: x.isalpha() and not x.isspace()
        for word in words:
            word_tokens.append(self.morph.parse(word)[0].normal_form)
        res = list(filter(filter_fn, word_tokens))

        return ' '.join(res)

    def text_to_seq(self, text: str):
        """Convert text to sequence of word id's. ID from TfidfVectorizer"""
        seq = []
        words = text.split(' ')
        for word in words:
            try:
                seq.append(self.vectorizer.vocabulary_[word] + 1)  # 0 - empty char

            except KeyError:
                pass
        return seq

    def texts_to_seqs(texts: List[str]) -> List[List[int]]:
        """Convert texts to sequence of word id's. ID from TfidfVectorizer"""
        seqs = []
        for text in texts:
            seqs.append(text_to_seq(text))

        return seqs

    def get_sentiment(self, sent: str):
        vects_tmp = self.text_to_seq(sent)
        vects_pad = pad_sequences([vects_tmp], maxlen=self.MAXLEN)
        return self.model.predict(vects_pad)

    def get_sentiment_interval(self, sent: str):
        sent_scores = self.get_sentiment(sent)
        return sent_scores[2] - sent_scores[0]
