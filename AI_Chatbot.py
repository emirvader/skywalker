class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR
    
import random
import json
import pickle
import numpy as np

import nltk
from nltk.stem import WordNetLemmatizer

from tensorflow.keras.models import load_model

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Initialising the Model 1/2")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-large")
print("Initialising the Model 2/2")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-large")
print("Initialising done!")

lemmatizer = WordNetLemmatizer()

targets = json.loads(open('traintarget.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
import_model = load_model('chat_model.h5')

def clear_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def examine_words(sentence):
    sentence_words = clear_sentence(sentence)
    examine = [0]*len(words)
    for sen in sentence_words:
        for s, se in enumerate(words):
            if se == sen:
                examine[s] = 1
    return np.array(examine)

def predict_class(sentence):
    exa_words = examine_words(sentence)
    res = import_model.predict(np.array([exa_words]))[0]
    threshold = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > threshold]
    
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent':classes[r[0]], 'probability':str(r[1])})
    return return_list

def get_response(targets_list, targets_json):
    tag = targets_list[0]['intent']
    list_of_targets = targets_json['target']
    # tag2 = str(targets_list)
    for i in list_of_targets:
        if i['tag']==tag:
            result = random.choice(i['response'])
            break
        else:
            new_user_input_ids = tokenizer.encode(tag + tokenizer.eos_token, return_tensors='pt')
            bot_input_ids = torch.cat([new_user_input_ids], dim=-1)
            chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)
            result = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
            break
    return result

print("Test Bot:")

while True:
    message = input("")
    if message == "exit":
        print("Exit Chatbot")
        break
    ints = predict_class(message)
    res = get_response(ints, targets)
    print(res)
    