#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""VyatSU bot syntax module"""

import pymorphy2
from keras.preprocessing.sequence import pad_sequences
import logging
import keras

logging.basicConfig(
    #  filename='bot.log', filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)


class ModelStub():

    def predict(self, sent):
        return 0


class SyntaxModule():

    def __init__(self):
        try:
            self.model = keras.models.load_model('synt_model.h5')
        except OSError:
            logger.error('Not found SYNT model file')
            self.model = ModelStub()

    morph = pymorphy2.MorphAnalyzer()
    #  morph = pymorphy2.MorphAnalyzer(lang='ru')

    TAG_VECTOR_LEN = 12
    MAXLEN = 12

    pos = {
        'NOUN': 1,  # имя существительное
        'ADJF': 2,  # имя прилагательное (полное)
        'ADJS': 3,  # имя прилагательное (краткое)
        'COMP': 4,  # компаратив
        'VERB': 5,  # глагол (личная форма)
        'INFN': 6,  # глагол (инфинитив)
        'PRTF': 7,  # причастие (полное)
        'PRTS': 8,  # причастие (краткое)
        'GRND': 9,  # деепричастие
        'NUMR': 10,  # числительное
        'ADVB': 11,  # наречие
        'NPRO': 12,  # местоимение-существительное
        'PRED': 13,  # предикатив
        'PREP': 14,  # предлог
        'CONJ': 15,  # союз
        'PRCL': 16,  # частица
        'INTJ': 17  # междометие
    }

    animacy = {
        'anim': 1,  # одушевлённое
        'inan': 2  # неодушевлённое
    }

    genders = {
        'masc': 1,  # мужской род
        'femn': 2,  # женский род
        'neut': 3  # средний род
    }

    numbers = {
        'sing': 1,  # единственное число
        'plur': 2  # множественное число
    }

    cases = {
        'nomn': 1,  # именительный падеж
        'gent': 2,  # родительный падеж
        'datv': 3,  # дательный падеж
        'accs': 4,  # винительный падеж
        'ablt': 5,  # творительный падеж
        'loct': 6,  # предложный падеж
        'voct': 7,  # звательный падеж
        'gen1': 8,  # первый родительный падеж
        'gen2': 9,  # второй родительный (частичный) падеж
        'acc2': 11,  # второй винительный падеж
        'loc1': 12,  # первый предложный падеж
        'loc2': 13  # второй предложный (местный) падеж
    }

    aspects = {
        'perf': 1,  # совершенный вид
        'impf': 2  # несовершенный вид
    }

    transitivity = {
        'tran': 1,  # переходный
        'intr': 2  # непереходный
    }

    persons = {
        '1per': 1,  # 1 лицо
        '2per': 2,  # 2 лицо
        '3per': 3  # 3 лицо
    }

    tenses = {
        'pres': 1,  # настоящее время
        'past': 2,  # прошедшее время
        'futr': 3  # будущее время
    }

    moods = {
        'indc': 1,  # изъявительное наклонение
        'impr': 2  # повелительное наклонение
    }

    voices = {
        'actv': 1,  # действительный залог
        'pssv': 2  # страдательный залог
    }

    involvement = {
        'incl': 1,  # говорящий включён в действие
        'excl': 2  # говорящий не включён в действие
    }

    # convert OpencorporaTag to vector<12>
    def tag_to_vector(self, tag):
        vector = [0] * self.TAG_VECTOR_LEN  # amount tag params

        tmp = tag.POS
        if tmp is not None:
            vector[0] = self.pos[tmp]

        tmp = tag.animacy
        if tmp is not None:
            vector[1] = self.animacy[tmp]

        tmp = tag.gender
        if tmp is not None:
            vector[2] = self.genders[tmp]

        tmp = tag.number
        if tmp is not None:
            vector[3] = self.numbers[tmp]

        tmp = tag.case
        if tmp is not None:
            vector[4] = self.cases[tmp]

        tmp = tag.aspect
        if tmp is not None:
            vector[5] = self.aspects[tmp]

        tmp = tag.transitivity
        if tmp is not None:
            vector[6] = self.transitivity[tmp]

        tmp = tag.person
        if tmp is not None:
            vector[7] = self.persons[tmp]

        tmp = tag.tense
        if tmp is not None:
            vector[8] = self.tenses[tmp]

        tmp = tag.mood
        if tmp is not None:
            vector[9] = self.moods[tmp]

        tmp = tag.voice
        if tmp is not None:
            vector[10] = self.voices[tmp]

        tmp = tag.involvement
        if tmp is not None:
            vector[11] = self.involvement[tmp]

        return vector

    def sent_to_tag_vector(self, sent):
        sent_vectors = []
        for word in sent.split(' '):
            sent_vectors.append(self.tag_to_vector(self.morph.parse(word)[0].tag))

        return sent_vectors

    def sents_to_tag_vectors(self, sents):
        sents_vectors = []
        for sent in sents:
            sents_vectors.append(self.sent_to_tag_vector(sent))

        return sents_vectors

    def question_prob(self, sent: str):
        vects_tmp = self.sent_to_tag_vector(sent)
        vects_pad = pad_sequences([vects_tmp], maxlen=self.MAXLEN)
        return self.model.predict(vects_pad)
