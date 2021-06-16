#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disicion module for Vyatsu bot"""

import pickle
from typing import List
import re
import logging

logging.basicConfig(
    #  filename='bot.log', filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)


class Desicion():

    OTHER = -1
    FAQ = 0
    FEEDBACK = 1

    def __init__(self):
        try:
            with open('faq_model.pkl', 'rb') as mf:
                self.faq_model = pickle.load(mf)
        except FileNotFoundError:
            logger.error('Not found FAQ model file')
            self.faq_model = lambda message: ['', 0]

        try:
            with open('sent_model.pkl', 'rb') as mf:
                self.faq_model = pickle.load(mf)
        except FileNotFoundError:
            logger.error('Not found SENT model file')
            self.sent_model = lambda message: 'neutral'

        try:
            with open('synt_model.pkl', 'rb') as mf:
                self.faq_model = pickle.load(mf)
        except FileNotFoundError:
            logger.error('Not found SYNT model file')
            self.synt_model = lambda message: 0

    def choice(self, message: str):
        faq_answer, faq_prob = self.faq_model(message)  # answer, [0;1]
        #  sent_score = self.sent_model(message)  # list of float [0.34, 0.22, 0.44] 'negative', 'neutral', 'positive'
        sent_score = self.sent_model_interval(message)  # answer, [-1;1]
        synt_score = self.synt_model(message)  # answer, [0;1]
        
        res = self._make_desicion(faq_prob, sent_score, synt_score, self._sent_count(message))
        if res == self.FAQ:
            return (res, faq_answer)
        elif res == self.FEEDBACK:
            return (res, sent_score)
        return (res, '')

    def _sent_count(self, text: str) -> int:
        new_text = re.sub(r'[.!?]\s', r'|', text)
        return len(new_text.split('|'))

    def sent_model_interval(self, message):
        sent_scores = self.sent_model(message)
        return sent_scores[2] - sent_scores[0]

    def _make_desicion(self, faq: float, sent: float, synt: float, sent_count: int):
        """Super mystery function"""

        def sent_transform(sent):
            return abs(sent) # TODO: make transformations

        w_faq = 1
        w_sent = 1
        w_synt = 1

        faq_score = (w_faq * faq) * (w_sent * (1 - sent_transform(sent))) * (w_synt * synt) * (1/sent_count)

        feedback_score = (w_faq * (1 - faq)) * (w_sent * sent_transform(sent)) * (w_synt * (1 - synt)) * (sent_count)

        other_score = (w_faq * (1 - faq)) * (w_sent * (1 - sent_transform(sent))) * (w_synt * (1 - synt)) * (1/sent_count)

        if faq_score > feedback_score and faq_score > other_score:
            return self.FAQ
        elif feedback_score > other_score:
            return self.FEEDBACK

        return self.OTHER
