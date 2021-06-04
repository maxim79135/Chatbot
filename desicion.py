#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disicion module for Vyatsu bot"""

import pickle
from typing import List

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


    def choice(message: str) -> tuple[int, str]:
        faq_answer, faq_prob = self.faq_model(message)  # [answer, 0-1] 
        sent_score = self.sent_model(message)  # list of float [0.34, 0.22, 0.44] 'negative', 'neutral', 'positive'
        synt = self.synt_model(message)  # 0-1

        res = _make_desicion(faq_prob, sent, synt)
        if res == self.FAQ:
            return (res, faq_answer)
        elif res == self.FEEDBACK:
            return (res, sent)
        return (res, '')

    def _make_desicion(faq: float, sent: List[int], synt: float):
        """Super mystery function"""

        return self.FAQ
        return self.OTHER
        return self.FEEDBACK


