#!/usr/bin/env python
# coding: utf-8

import csv

import nltk
import numpy as np
import pymorphy2
from keras.preprocessing.sequence import pad_sequences
from nltk.tokenize.toktok import ToktokTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')

from typing import List

morph = pymorphy2.MorphAnalyzer(lang='ru')

filter_fn = lambda x: x.isalpha() and not x.isspace() 


# ============== Common preprocessing functions ==============


def tokenize(text : str, normalize : bool = True) -> List[str]:
    """ Tokenize text to words with normalization. Remove punktuation."""
    text.replace('\n', ' ')
    words = nltk.word_tokenize(text)
    word_tokens = []
    if normalize:
        for word in words:
            word_tokens.append(morph.parse(word)[0].normal_form)
    else:
        for word in words:
            word_tokens.append(word)
    res = list(filter(filter_fn, word_tokens))
    
    return res

def normalize_sent(sent: str) -> str:
    """ Normalize words in text. Remove punktuation."""
    sent.replace('\n', ' ')
    words = nltk.word_tokenize(sent)
    word_tokens = []
    for word in words:
        word_tokens.append(morph.parse(word)[0].normal_form)
    res = list(filter(filter_fn, word_tokens))
    
    return ' '.join(res)


def text_to_seq(text : str, vectorizer : TfidfVectorizer) -> List[int]:
    """Convert text to sequence of word id's. ID from TfidfVectorizer"""
    seq = []
    words = text.split(' ')
    for word in words:
        try:
            seq.append(vectorizer.vocabulary_[word] + 1) # 0 - empty char
            
        except KeyError:
            pass
    return seq

def texts_to_seqs(texts : List[str], vectorizer : TfidfVectorizer) -> List[List[int]]:
    """Convert texts to sequence of word id's. ID from TfidfVectorizer"""
    seqs = []
    for text in texts:
        seqs.append(text_to_seq(text, vectorizer))
    
    return seqs


y_train = labels_to_y(label_list)
print(y_train[:10])

x_normalize = list(map(normalize_sent, text_list))
print(x_normalize[:10])

maxlen = 50
max_words = 10000

vectorizer = TfidfVectorizer(max_features=max_words)
vectorizer.fit(x_normalize)
print(len(vectorizer.vocabulary_))

# encode words to numbers
x_seq = texts_to_seqs(x_normalize, vectorizer)
print(len(x_seq))
print(x_seq[:10])

def labels_to_y(label_list : List[str]) -> List[List[int]]:
    """Transform every medical review label to vector
    
    Example: 
    ' Ужасно'    -> [1, 0, 0]
    ' Плохо'     -> [1, 0, 0]
    ' Нормально' -> [0, 1, 0]
    ' Хорошо'    -> [0, 0, 1]
    ' Отлично'   -> [0, 0, 1]
    """
    num_labels = []
    for label in label_list:
        labels_vect = [0]*3 # amount classes
        labels_vect[labels_dict[label]] = 1
        num_labels.append(labels_vect)

    return num_labels 

# ============== medical review dataset preprocessing functions ==============
    
def transform_to_target_format(input_path: str, output_path: str = 'output.csv') -> str:
    """Transform medical review dataset to target format (in .csv)"""
    labels_dict = {
        ' Ужасно' : 'negative',
        ' Плохо' : 'negative',
        ' Нормально' : 'neutral',
        ' Хорошо' : 'positive',
        ' Отлично' : 'positive'
    }

    with open(input_path, "r") as input_file:
        reader = csv.DictReader(input_file, delimiter=',')
        with open(output_path, "w") as output_file:
            field_names = ['text','sentiment']  # TODO: get field_names from reader
            writer = csv.DictWriter(output_file, fieldnames=field_names, delimiter=',')
            writer.writeheader()

            for record in reader:
                writer.writerow(record.update({'sentiment': labels_dict[record['sentiment']]}))

# pad sequences
x_seq_pad = pad_sequences(x_seq, maxlen=maxlen)
print(np.shape(x_seq_pad))
print(x_seq_pad[:10])


# ================= create models ===============

import matplotlib.pyplot as plt
from keras.callbacks import ModelCheckpoint
from keras.layers import (GRU, LSTM, Dense, Embedding, Flatten, InputLayer,
                          SimpleRNN)
from keras.models import Sequential


embedding_length = 30
optimizer = 'adam'
# loss = 'binary_crossentropy'
loss = 'binary_crossentropy'
metrics = ['accuracy']
output_activation = 'softmax'
input_len = maxlen
print(input_len)
y_train = np.array(y_train)
x_train = np.array(x_seq_pad)
num_classes = len(y_train[0])
print(num_classes)



model = Sequential()
model.add(Embedding(max_words+1, embedding_length, input_length=input_len))
model.add(LSTM(16, recurrent_dropout=0.1))
model.add(Dense(num_classes, activation=output_activation))
model.compile(optimizer=optimizer, 
              loss=loss, 
              metrics=metrics
              )

model.summary()

model_name = 'med_model2'
callback = ModelCheckpoint(model_name+'.h5',
              monitor='acc',
              mode='max',
              save_best_only=True)

history = model.fit(x_train, 
                    y_train, 
                    epochs=10,
                    batch_size=2000,
                    validation_split=0.15,
                    callbacks=[callback])

plt.plot(history.history['acc'], 
         label='Доля верных ответов на обучающем наборе')
plt.plot(history.history['val_acc'], 
         label='Доля верных ответов на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.savefig(model_name+'.jpg')
plt.legend()
plt.show()


# In[51]:


def text_to_input(text : str, maxlen : int, vectorizer : TfidfVectorizer) -> List[int]:
    text_norm = normalize_sent(text)
    text_seq = text_to_seq(text_norm, vectorizer)
    text_seq_pad = pad_sequences([text_seq], maxlen=maxlen)
    
    return text_seq_pad    

# predict model
test_text ='Он купил автомобиль, и похавал. нормально' 
# test_text ='отстой ужасно'
test_text ='очень хорошо'
# test_text ='Хватит задавать столько домашки надоело!! и так не справляемся'
test_input = text_to_input(test_text, maxlen, vectorizer)
print(test_input)
model.predict(test_input)
import os

df_train = vectorizer.transform(x_train)


seq_train_array = np.array(seq_train)
print(seq_train_array[:3])
print(np.shape(seq_train_array))

df_train_array = df_train.toarray()
print(df_train_array[:3])
print(np.shape(df_train_array))


label_array = np.array(labels_to_int(label_list))
print(label_array[:3])
print(text_list[:3])
print(len(text_list))


# In[366]:


labels_dict = {
    'neutral' : 0,
    'positive' : 1,
    'negative' : 2,
    'skip' : 3,
    'speech' : 4
}
    
def label_to_int(label : str) -> int:
    return labels_dict[label]

def labels_to_int(labels :List[str]) -> List[List[int]]:
    labels_int = []
    for label in labels:
        labels_vect = [0]*len(labels_dict)
        labels_vect[labels_dict[label]] = 1
        labels_int.append(labels_vect)

    return labels_int


# In[434]:


import csv

label_list = []
text_list = []
file_name = "../rusentiment_random_posts.csv"
with open(file_name, "r") as f:
    reader = csv.DictReader(f, delimiter=',')
    for record in reader:
        label_list.append(record['label'])
        text_list.append(record['text'])
f.close()

label_array = np.array(labels_to_int(label_list))
print(label_array[:3])
print(text_list[:3])
print(len(text_list))


# ### Normalize corpus

# In[435]:


corpus_norm = list(map(normalize_sent, text_list))
print(corpus_norm[:3])


# ### Split to train test

# In[581]:


from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(corpus_norm, label_array, test_size=0.2)


# ### Tf-Idf vectorization

# In[582]:


import numpy as np
from keras.preprocessing.sequence import pad_sequences

maxlen = 50
max_words = 3000

vectorizer = TfidfVectorizer(max_features=max_words)
vectorizer.fit(corpus_norm)
print(len(vectorizer.vocabulary_))

df_train = vectorizer.transform(x_train)
seq_train = texts_to_seqs(x_train, vectorizer)

seq_train = pad_sequences(seq_train, maxlen=maxlen)

seq_train_array = np.array(seq_train)
print(seq_train_array[:3])
print(np.shape(seq_train_array))

df_train_array = df_train.toarray()
print(df_train_array[:3])
print(np.shape(df_train_array))


# ### Concatenate tf-idf with word sequenties (optional)

# In[575]:


x_train = np.concatenate((seq_train_array, df_train_array), axis=1)
print(x_train[:3])
print(np.shape(x_train))
vect_length = np.shape(x_train)[1]


# ## Restrict classes

# In[593]:


import csv

label_list2 = []
text_list2 = []
file_name = "../rusentiment_random_posts.csv"
with open(file_name, "r") as f:
    reader = csv.DictReader(f, delimiter=',')
    for record in reader:
        if record['label'] != 'skip' and record['label'] != 'speech':
            label_list2.append(record['label'])
            text_list2.append(record['text'])
f.close()

label_array2 = np.array(labels_to_int(label_list2))
print(label_array2[:3])
print(text_list2[:3])
print(len(text_list2))

corpus_norm = list(map(normalize_sent, text_list2))
print(corpus_norm[:3])

maxlen = 50
max_words = 3000

vectorizer = TfidfVectorizer(max_features=max_words)
vectorizer.fit(corpus_norm)
print(len(vectorizer.vocabulary_))

seq_train = texts_to_seqs(corpus_norm, vectorizer)

seq_train = pad_sequences(seq_train, maxlen=maxlen)

seq_train_array2 = np.array(seq_train)
print(seq_train_array2[:3])
print(np.shape(seq_train_array))


# In[588]:


labels_dict = {
    'neutral' : 0,
    'positive' : 1,
    'negative' : 2,
}
    
def label_to_int(label : str) -> int:
    return labels_dict[label]

def labels_to_int(labels :List[str]) -> List[List[int]]:
    labels_int = []
    for label in labels:
        labels_vect = [0]*len(labels_dict)
        labels_vect[labels_dict[label]] = 1
        labels_int.append(labels_vect)

    return labels_int


# In[585]:


a = [1,2,3,4,5]
a.pop(3)


# # Compile models

# In[586]:


lr = label_array[:40]
tl = seq_train_array[:40]
print(lr)
print(tl)
for i, label in enumerate(lr):
    if label[3] or label[4]:
        tl.pop(i)
        lr.pop(i)
        
print(lr)
print(tl)
    


# In[4]:


get_ipython().system('pip uninstall -y tensorflow keras ')
get_ipython().system('pip install tensorflow==1.5 keras==2.0')


# ## Model 1
# `Simple NN 128->32->5`

# In[ ]:


model1 = Sequential()
model1.add(InputLayer(input_shape=(vect_length,)))
model1.add(Dense(128, activation='relu', ))
model1.add(Dense(32, activation='relu'))
model1.add(Dense(5, activation='sigmoid'))


# In[380]:


model1.compile(optimizer='adam',
             loss='binary_crossentropy',
             metrics=['accuracy'])

model1.summary()


# In[449]:


model1_weigth = 'model1.h5'
callback1 = ModelCheckpoint(model1_weigth,
              monitor='acc',
              mode='max',
              save_best_only=True)


# In[ ]:


model1_weigth = 'model1.h5'
callback1 = ModelCheckpoint(model1_weigth,
              monitor='acc',
              mode='max',
              save_best_only=True)

 history1 = model1.fit(x_train, 
                       y_train, 
                       epochs=25,
                       batch_size=200,
                       validation_split=0.15,
                       callbacks=[callback1])


# In[424]:


plt.plot(history1.history['acc'], 
         label='Доля верных ответов на обучающем наборе')
plt.plot(history1.history['val_acc'], 
         label='Доля верных ответов на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.legend()
plt.show()


# ## Model 2
# `Simple RNN embedding->RNN(8)->5`

# In[451]:


model2 = Sequential()
model2.add(Embedding(max_words+1, 10, input_length=maxlen))
model2.add(SimpleRNN(8))
model2.add(Dense(5, activation='sigmoid'))


# In[452]:


model2.compile(optimizer='adam', 
              loss='binary_crossentropy', 
              metrics=['accuracy']
              )
model2.summary()


# In[453]:


model2_weigth = 'model2.h5'
callback2 = ModelCheckpoint(model2_weigth,
              monitor='acc',
              mode='max',
              save_best_only=True)


# In[454]:


history2 = model2.fit(seq_train_array, 
                    y_train, 
                    epochs=35,
                    batch_size=128,
                    validation_split=0.1,
                       callbacks=[callback2])


# In[483]:


history2.history['val_acc']


# In[527]:


plt.plot(history2.history['acc'], 
         label='Доля верных ответов на обучающем наборе')
plt.plot(history2.history['val_acc'], 
         label='Доля верных ответов на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')

plt.savefig('model2.jpg')
# plt.legend()
# plt.show()


# In[532]:


plt.clf()


# In[443]:


# save model2
model2_file = 'model2.json'
model2_json = model2.to_json()

with open(model2_file, 'w') as f:
  f.write(model2_json)

model2.save('model2.h5')


# In[468]:


from keras.models import load_model

model22 = load_model('model2.h5')


# In[481]:


print(model2.evaluate(seq_train_array, y_train))


# In[497]:


import os

test_count = 0


# In[533]:

# ===================== utils ======================

def test_models(models, x_train, y_train, epochs, batch_size, validation_split, test_num) -> List[float]:
    """Test models and save best state, plot"""
    results  = []
    print('Start test set #%d ...\n' %test_num)
    
    directory = 'test_' + str(test_num)
    if not os.path.exists(directory):
        print('Create dir "%s" ...\n' %directory)
        os.makedirs(directory)
        
    for i, model in enumerate(models):
        model_name = directory + '/model' + str(i)
        print('Train model %d ...\n' %i)

        callback = ModelCheckpoint(model_name + '.h5',
                                   monitor='acc',
                                   mode='max',
                                   save_best_only=True) 

        history = model.fit(x_train, 
                            y_train, 
                            epochs=epochs,
                            batch_size=batch_size,
                            validation_split=validation_split,
                            callbacks=[callback])

        print('Save model %d \n' %i)
        plt.clf()
        plt.plot(history.history['acc'], 
                 label='Доля верных ответов на обучающем наборе')
        plt.plot(history.history['val_acc'], 
                 label='Доля верных ответов на проверочном наборе')
        plt.xlabel('Эпоха обучения')
        plt.ylabel('Доля верных ответов')

        plt.savefig(model_name + '.jpg')
        print('Save model %d fig\n' %i)

        results.append(history)

    return results
        

embedding_length = 30
optimizer = 'rmsprop'
# loss = 'binary_crossentropy'
loss = 'binary_crossentropy'
metrics = ['accuracy']
output_activation = 'sigmoid'
input_len = maxlen
print(input_len)
y_train = label_array2
x_train = seq_train_array2
num_classes = len(y_train[0])
print(num_classes)

# Dense models
model1 = Sequential()
model1.add(InputLayer(input_shape=(input_len,)))
model1.add(Dense(128, activation='relu', ))
model1.add(Dense(32, activation='relu'))
model1.add(Dense(num_classes, activation=output_activation))
model1.compile(optimizer=optimizer, 
              loss=loss, 
              metrics=metrics
              )
