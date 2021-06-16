#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disicion module for Vyatsu bot"""

import pickle
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

        self.synt_module = SyntaxModule()

    def choice(self, message: str):
        faq_answer, faq_prob = self.faq_model(message)  # answer, [0;1]
        #  sent_score = self.sent_model(message)  # list of float [0.34, 0.22, 0.44] 'negative', 'neutral', 'positive'
        sent_score = self.sent_model_interval(message)  # answer, [-1;1]
        synt_score = self.synt_module.question_prob(message)  # answer, [0;1]
        
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

        if sent_count > 1:
            if sent > 0.2:
                return self.FEEDBACK 
            else:
                return self.OTHER 
        else:
            if synt < 0.6:
                if sent > 0.2:
                    return self.FEEDBACK 
                else:
                    return self.OTHER 
            else:
                if faq > 0.6:
                    return self.FAQ 
                else:
                    if sent > 0.2:
                        return self.OTHER 
                    else:
                        if faq > 0.4:
                            return self.FAQ 
                        else:
                            return self.OTHER 
        return self.OTHER 






        #  if faq_score > feedback_score and faq_score > other_score:
            #  return self.FAQ
        #  elif feedback_score > other_score:
            #  return self.FEEDBACK
#
        #  return self.OTHER
