# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 15:21:41 2019

@author: Ryan
"""

from __future__ import division
import urllib
from bs4 import BeautifulSoup

import pickle
import re
import csv
import os
import sys
import nltk, string
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import nltk

import numpy as np

from nltk.stem import WordNetLemmatizer

os.chdir("C:\\Users\\Ryan\\Documents\\Projects\\Fact-Feel-FlaskApp")

import re
import string
from collections import Counter, defaultdict
from string import punctuation


class Dictionary():
    sentence_punctuation = {'.', '?', '!', '\n'}
    _TYPE_BASIC = 'basic'
    _TYPE_PRE = 'pre'
    _TYPE_POST = 'post'

    def __init__(self, filename, use_long_category_names=True, internal_category_list=None): ##################################
        """@param internal_category_list: Should be None or '2001' or '2007' """
        self._stems = dict()  # this is a prefix tree for the stems, the leaves are sets of categories
        self._lookup = defaultdict(dict)  # word->type->????->{categories}
        #type can be one of "basic", "pre", "post".
        #basic leads to a set of categories,
        #pre and post lead to a list of tuples of (conditions, if_true categories, if_false categories)
        self._ignored = set()  # caches words that are searched for but not found, this favors processing over memory

        self._setup_category_lookup(internal_category_list, use_long_category_names)
        try:
            self.load_dictionary_file(filename, internal_category_list)
        except:
            sys.stderr.writelines(["Failed to load dictionary file: "+filename+"\n",
                                   "Is the dictionary file correct?\n",
                                   "Does a % precede the category list?\n",
                                   "If there is no category list, did you set internal_category_list='2007' ?\n",
                                   "Hope this helps...\n"])
            raise

    _dictionary_line_re = re.compile(r'^(?P<word>\S+)\s+(?P<categories>.+)$')
    _dictionary_line_categories_re = re.compile(r'(\d+|\<(\w+(\s+\w+)*)\>(\d+)(\/(\d+))?|\(\s*(\d+(\s+\d+)*)\s*\)(\d+)(\/(\d+))?)')
    def load_dictionary_file(self, filename, internal_category_list=None):
        category_mode = False
        for line in open(filename):
            line = line.strip()

            if line=='' or line.startswith('#'):
                continue
            if line.startswith('%'):
                category_mode = not category_mode
                continue

            if category_mode:
                if internal_category_list is None:
                    number, category_name = line.split()
                    category_name = self._translate_category_name(category_name)
                    self._category_lookup[int(number)]=category_name
                continue

            match = Dictionary._dictionary_line_re.match(line)
            word = match.group('word')
            is_stem = word.endswith('*')
            if is_stem:
                word = word[:-1]
            for category_group in Dictionary._dictionary_line_categories_re.findall(match.group('categories')):
                category = category_group[0]
                if category == '00':
                    continue
                elif category.isdigit():
                    if is_stem:
                        self._add_stemmed(word, self._category_lookup[int(category)])
                    else:
                        if Dictionary._TYPE_BASIC not in self._lookup[word]:
                            self._lookup[word][Dictionary._TYPE_BASIC]=set()
                        self._lookup[word][Dictionary._TYPE_BASIC].add(self._category_lookup[int(category)])

                elif '(' in category or '<' in category:  # convoluted special cases lead to much of the complexity in this program
                    junk, post, junk, if_post, junk, if_not_post, pre, junk, if_pre, junk, if_not_pre = category_group
                    if pre != '':
                        entry_type = Dictionary._TYPE_PRE
                        conditions = sorted([self._category_lookup[int(number)] for number in pre.split()])
                        if_true = self._category_lookup[int(if_pre)]
                        if if_not_pre != '':
                            if_not_true = self._category_lookup[int(if_not_pre)]
                    elif post != '':
                        entry_type = Dictionary._TYPE_POST
                        conditions = sorted(post.lower().split())
                        if_true = self._category_lookup[int(if_post)]
                        if if_not_post != '':
                            if_not_true = self._category_lookup[int(if_not_post)]

                    if entry_type not in self._lookup[word]:
                        self._lookup[word][entry_type]=list()

                    for other_conditions, other_if_set, other_if_not_set in self._lookup[word][entry_type]:
                        if str(other_conditions)==str(conditions):  # a little costly on load means less on use
                            other_if_set.add(if_true)
                            other_if_not_set.add(if_not_true)
                            break
                    else:  # for else means the for ended naturally
                        self._lookup[word][entry_type].append( (conditions, {if_true}, {if_not_true}) )

    def _translate_category_name(self, category_name):
        if category_name.lower() in self._category_name_lookup:
            return self._category_name_lookup[category_name.lower()]
        return category_name

    def _add_stemmed(self, word, category):
        current_node = self._stems
        for char in word[:-1]:
            if char not in current_node:
                current_node[char] = dict()
            current_node = current_node[char]
        if word[-1] not in current_node:
            current_node[word[-1]] = set()
        current_node = current_node[word[-1]]

        current_node.add(category)

    _pure_punctuation_re = re.compile('^['+re.escape(string.punctuation)+']+$')
    _punctuation_of_interest = {'?':'Question Marks', '!':'Exclamation Marks', '"':'Quote Marks',
                                ',':'Comma',':':'Colon',';':'Semicolon','-':'Dash','\'':'Apostrophe',
                                '(':'Parenthesis', ')':'Parenthesis', '{':'Parenthesis', '}':'Parenthesis', '[':'Parenthesis', ']':'Parenthesis' }
    def score_word(self, word, previous_word=None, next_word=None):
        scores = Counter()
        if word is None:
            return scores

        if '\n' in word:
            scores['Newlines'] += 1

        word = word.strip().lower()

        if len(word) == 0:
            pass
        elif word[0].isdigit():
            scores['Word Count'] += 1
            scores['Numerals'] += 1
        elif Dictionary._pure_punctuation_re.match(word):
            scores['All Punctuation'] += 1
            for char in word:
                if char in Dictionary._punctuation_of_interest:
                    scores[Dictionary._punctuation_of_interest[char]] += 1
                else:
                    scores['Other Punctuation'] += 1
        else:
            scores['Word Count'] += 1
            if len(word) > 6:
                scores['Six Letter Words'] += 1
            if word not in self._ignored:
                if word in self._lookup:
                    for entry_type in self._lookup[word]:
                        if entry_type==Dictionary._TYPE_BASIC:
                            scores.update(self._lookup[word][entry_type])
                        else:
                            for conditions, if_set, if_not_set in self._lookup[word][entry_type]:
                                if ((entry_type==Dictionary._TYPE_PRE and not set(self.score_word(word=previous_word, next_word=word).keys()).isdisjoint(set(conditions))) or
                                        (entry_type==Dictionary._TYPE_POST and next_word is not None and next_word.lower() in conditions)):
                                    scores.update(if_set)
                                else:
                                    scores.update(if_not_set)
                else:
                    current_node = self._stems
                    for char in word:
                        if char in current_node:
                            current_node = current_node[char]
                            if isinstance(current_node, set):
                                if Dictionary._TYPE_BASIC not in self._lookup[word]:
                                    self._lookup[word][Dictionary._TYPE_BASIC]=set()
                                self._lookup[word][Dictionary._TYPE_BASIC].update(current_node) #add to main lookup for time efficiency
                                scores.update(self._lookup[word][Dictionary._TYPE_BASIC])
                                break
                        else:
                            self._ignored.add(word) #dead end
                            break
                    else:
                        self._ignored.add(word) #not found but didn't hit a dead end

                if word not in self._ignored: #Note this is "still not in"
                    scores['Dictionary Words'] += 1
        return scores

    def _setup_category_lookup(self, internal_category_list, use_long_category_names):
        self._category_name_lookup = dict()
        if use_long_category_names:
            for long_name, LIWC2007_number, LIWC2007_short, LIWC2001_number, LIWC2001_short in Dictionary._liwc_categories:
                if LIWC2001_short is not None:
                    self._category_name_lookup[LIWC2001_short]=long_name
                if LIWC2007_short is not None:
                    self._category_name_lookup[LIWC2007_short]=long_name

        self._category_lookup = dict()
        if internal_category_list is not None:
            for long_name, LIWC2007_number, LIWC2007_short, LIWC2001_number, LIWC2001_short in Dictionary._liwc_categories:
                if internal_category_list == '2001' and LIWC2001_number is not None:
                    self._category_lookup[LIWC2001_number]=self._translate_category_name(LIWC2001_short)
                if internal_category_list == '2007' and LIWC2007_number is not None:
                    self._category_lookup[LIWC2007_number]=self._translate_category_name(LIWC2007_short)

    #In case it is needed:
    #(long_name, LIWC2007_number, LIWC2007_short, LIWC2001_number, LIWC2001_short)
    _liwc_categories = [
        ('Total Function Words', 1, 'funct', None, None),
        ('Total Pronouns', 2, 'pronoun', 1, 'pronoun'),
        ('Personal Pronouns', 3, 'ppron', None, None),
        ('First Person Singular', 4, 'i', 2, 'i'),
        ('First Person Plural', 5, 'we', 3, 'we'),
        ('Second Person', 6, 'you', 5, 'you'),
        ('Third Person Singular', 7, 'shehe', None, None),
        ('Third Person Plural', 8, 'they', None, None),
        ('Impersonal Pronouns', 9, 'ipron', None, None),
        ('Articles', 10, 'article', 9, 'article'),
        ('Common Verbs', 11, 'verb', None, None),
        ('Auxiliary Verbs', 12, 'auxverb', None, None),
        ('Past Tense', 13, 'past', 38, 'past'),
        ('Present Tense', 14, 'present', 39, 'present'),
        ('Future Tense', 15, 'future', 40, 'future'),
        ('Adverbs', 16, 'adverb', None, None),
        ('Prepositions', 17, 'preps', 10, 'preps'),
        ('Conjunctions', 18, 'conj', None, None),
        ('Negations', 19, 'negate', 7, 'negate'),
        ('Quantifiers', 20, 'quant', None, None),
        ('Number', 21, 'number', 11, 'number'),
        ('Swear Words', 22, 'swear', 66, 'swear'),
        ('Social Processes', 121, 'social', 31, 'social'),
        ('Family', 122, 'family', 35, 'family'),
        ('Friends', 123, 'friend', 34, 'friends'),
        ('Humans', 124, 'humans', 36, 'humans'),
        ('Affective Processes', 125, 'affect', 12, 'affect'),
        ('Positive Emotion', 126, 'posemo', 13, 'posemo'),
        ('Negative Emotion', 127, 'negemo', 16, 'negemo'),
        ('Anxiety', 128, 'anx', 17, 'anx'),
        ('Anger', 129, 'anger', 18, 'anger'),
        ('Sadness', 130, 'sad', 19, 'sad'),
        ('Cognitive Processes', 131, 'cogmech', 20, 'cogmech'),
        ('Insight', 132, 'insight', 22, 'insight'),
        ('Causation', 133, 'cause', 21, 'cause'),
        ('Discrepancy', 134, 'discrep', 23, 'discrep'),
        ('Tentative', 135, 'tentat', 25, 'tentat'),
        ('Certainty', 136, 'certain', 26, 'certain'),
        ('Inhibition', 137, 'inhib', 24, 'inhib'),
        ('Inclusive', 138, 'incl', 44, 'incl'),
        ('Exclusive', 139, 'excl', 45, 'excl'),
        ('Perceptual Processes', 140, 'percept', 27, 'senses'),
        ('See', 141, 'see', 28, 'see'),
        ('Hear', 142, 'hear', 29, 'hear'),
        ('Feel', 143, 'feel', 30, 'feel'),
        ('Biological Processes', 146, 'bio', None, None),
        ('Body', 147, 'body', 61, 'body'),
        ('Health', 148, 'health', None, None),
        ('Sexual', 149, 'sexual', 62, 'sexual'),
        ('Ingestion', 150, 'ingest', 63, 'eating'),
        ('Relativity', 250, 'relativ', None, None),
        ('Motion', 251, 'motion', 46, 'motion'),
        ('Space', 252, 'space', 41, 'space'),
        ('Time', 253, 'time', 37, 'time'),
        ('Work', 354, 'work', 49, 'job'),
        ('Achievement', 355, 'achieve', 50, 'achieve'),
        ('Leisure', 356, 'leisure', 51, 'leisure'),
        ('Home', 357, 'home', 52, 'home'),
        ('Money', 358, 'money', 56, 'money'),
        ('Religion', 359, 'relig', 58, 'relig'),
        ('Death', 360, 'death', 59, 'death'),
        ('Assent', 462, 'assent', 8, 'assent'),
        ('Nonfluencies', 463, 'nonfl', 67, 'nonfl'),
        ('Fillers', 464, 'filler', 68, 'fillers'),
        ('Total first person', None, None, 4, 'self'),
        ('Total third person', None, None, 6, 'other'),
        ('Positive feelings', None, None, 14, 'posfeel'),
        ('Optimism and energy', None, None, 15, 'optim'),
        ('Communication', None, None, 32, 'comm'),
        ('Other references to people', None, None, 33, 'othref'),
        ('Up', None, None, 42, 'up'),
        ('Down', None, None, 43, 'down'),
        ('Occupation', None, None, 47, 'occup'),
        ('School', None, None, 48, 'school'),
        ('Sports', None, None, 53, 'sports'),
        ('TV', None, None, 54, 'tv'),
        ('Music', None, None, 55, 'music'),
        ('Metaphysical issues', None, None, 57, 'metaph'),
        ('Physical states and functions', None, None, 60, 'physcal'),
        ('Sleeping', None, None, 64, 'sleep'),
        ('Grooming', None, None, 65, 'groom')]


feat_list_model_order = None
with open(os.path.join("feature_extraction","feature_order.pkl"),"rb") as f_p:
    feat_list_model_order = pickle.load(f_p)

#feat_list_model_order = [
#        "Word Count",
#        "Words Per Sentence",
#        "Six Letter Words",
#        "Dictionary Words",
#        "Numerals",
#        "Total Function Words",
#        "Total Pronouns",
#        "Personal Pronouns",
#        "First Person Singular",
#        "First Person Plural",
#        "Second Person",
#        "Third Person Singular",
#        "Third Person Plural",
#        "Impersonal Pronouns",
#        "Articles",
#        "Common Verbs",
#        "Auxiliary Verbs",
#        "Past Tense",
#        "Present Tense",
#        "Future Tense",
#        "Adverbs",
#        "Prepositions",
#        "Conjunctions",
#        "Negations",
#        "Quantifiers",
#        "Number",
#        "Swear Words",
#        "Social Processes",
#        "Family",
#        "Friends",
#        "Humans",
#        "Affective Processes",
#        'Positive Emotion', 
#        'Negative Emotion', 
#        'Anxiety', 
#        'Anger', 
#        'Sadness', 
#        'Cognitive Processes', 
#        'Insight',
#        'Causation', 
#        'Discrepancy', 
#        'Tentative', 
#        'Certainty', 
#        'Inhibition', 
#        'Inclusive', 
#        'Exclusive', 
#        'Perceptual Processes', 
#        'See', 
#        'Hear', 
#        'Feel', 
#        'Biological Processes', 
#        'Body', 
#        'Health', 
#        'Sexual',
#        'Ingestion',
#        'Relativity', 
#        'Motion', 
#        'Space', 
#        'Time', 
#        'Work',
#        'Achievement', 
#        'Leisure', 
#        'Home', 
#        'Money', 
#        'Religion', 
#        'Death', 
#        'Assent', 
#        'Nonfluencies', 
#        'Fillers', 
#        "Period",
#        "Comma",
#        "Colon",
#        "Semi Colon",
#        "Question Mark",
#        "Exclamation Mark",
#        "Dash",
#        "Quote",
#        "Apostrophe",
#        "Parenthesis",
#        "Other Punctuation",
#        "All Punctuation",
#        "CC",
#        "CD",
#        "DT",
#        "EX",
#        "FW",
#        "IN",
#        "JJ",
#        "JJR",
#        "JJS",
#        "LS",
#        "MD",
#        "NN",
#        "NNS",
#        "NNP",
#        "NNPS",
#        "PDT",
#        "POS",
#        "PRP",
#        "PRP$",
#        "RB",
#        "RBR",
#        "RBS",
#        "RP",
#        "SYM",
#        "TO",
#        "UH",
#        "VB",
#        "VBD",
#        "VBG",
#        "VBN",
#        "VBP",
#        "VBZ",
#        "WDT",
#        "WP",
#        "WP$",
#        "WRB",
#        "anticipation_emo",
#        "joy_emo",
#        "negative_emo",
#        "sadness_emo",
#        "disgust_emo",
#        "positive_emo",
#        "anger_emo",
#        "surprise_emo",
#        "fear_emo",
#        "trust_emo",
#        "Strong-subjective",
#        "Weak-subjective"
#        ]

POS = None
with open(os.path.join("feature_extraction","POS_dict.pkl"),"rb") as f_p:
    POS = pickle.load(f_p)

#POS = {"JJ":"adj",
#       "JJR":"adj",
#       "JJS":"adj",
#       "NN":"noun",
#       "NNS":"noun",
#       "NNP":"noun",
#       "NNPS":"noun",
#       "PRP":"noun",
#       "PRP$":"noun",
#       "RB":"adverb",
#       "RBR":"adverb",
#       "RB$":"adverb",
#       "VB":"verb",
#       "VBD":"verb",
#       "VBG":"verb",
#       "VBN":"verb",
#       "VBP":"verb",
#       "VBZ":"verb"
#        }

punct_feats = None
with open(os.path.join("feature_extraction","punct_feats.pkl"),"rb") as f_p:
    punct_feats = pickle.load(f_p)

#punct_feats = {
#        "Period" : ".",
#        "Comma": ",",
#        "Colon": ":",
#        "Semi Colon": ";",
#        "Question Mark": "?",
#        "Exclamation Mark": "!",
#        "Dash": "-",
#        "Quote": '"',
#        "Apostrophe": "'",
#        "Parenthesis": "()",
#        "Other Punctuation": '#$%&*+/<=>@[\\]^_`{|}~',
#        "All Punctuation": ""
#        }

strong_pos_adjectives = ["incredible", "wellwritten", "great", "excellent",
                         "successful", "outstanding", "impressive", "best", "highest",
                         "outstanding", "featured", "greatest", "awesome",
                         "fantastic", "nice", "beautiful", "good"]   

cause_verbs = ["make", "have", "get", "let", "help", "collaborate", "advise",
               "advocate", "anticipate", "ask", "command", "expect",
               "desire", "demand", "insist", "hope", "necessitate", "need",
               "postulate","propose", "recommend", "request", "require",
               "suggest", "urge", "want", "wish"]  

you_mod = ["you can", "you could", "you shall", "you may", "you might", 
           "you must", "you should", "you will", "you would",
           "you'd", "can you", "could you", "shall you", "may you", 
           "might you", "must you", "should you", "will you", "would you"]

negative_jargon = ["spam","revert","reverted", "block", "blocked",
                   "vandalism","vandalise","vandalised", "vandalized",
                   "vandalize", "violate", "violated", "nonfree", "copyright",
                   "remove", "disputed", "dispute", "noneutral", "fair use"] 

smile = ["smile", "smiles", "smiling", "balloon", "balloons"]  

greetings = ["hi", "hey", "ha", "hello" , "cheers", 
             "regards", "new year", "merry christmas", 
             "see you", "good day", "nice day"]

congrats = ["congrats", "congratulation", "congratulations"]

acknowledge = ["thank you for","thanks for"]

#Parts of speech labels
pos_tags = ["CC","CD","DT","EX","FW","IN","JJ","JJR","JJS","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
#Emotion lexicon labels
emo_cats = ['anticipation_emo', 'joy_emo', 'negative_emo', 'sadness_emo', 'disgust_emo', 'positive_emo', 'anger_emo', 'surprise_emo', 'fear_emo', 'trust_emo']
 
subj_cats = ["weak-negative","strong-negative","weak-positive","strong-positive"]


_liwc_categories = None
with open(os.path.join("feature_extraction","liwc_categories.pkl"),"rb") as f_p:
    _liwc_categories = pickle.load(f_p)

#_liwc_categories = [
#    'Unique Words',
#    'Dictionary Words',
#    'Other Punctuation',
#    'Numerals',
#    'Six Letter Words',
#    'Word Count',
#    'Sentences',
#    'Words Per Sentence',
#    'Total Function Words',
#    'Total Pronouns',
#    'Personal Pronouns',
#    'First Person Singular', 
#    'First Person Plural', 
#    'Second Person',
#    'Third Person Singular', 
#    'Third Person Plural', 
#    'Impersonal Pronouns', 
#    'Articles',
#    'Common Verbs', 
#    'Auxiliary Verbs', 
#    'Past Tense', 
#    'Present Tense', 
#    'Future Tense', 
#    'Adverbs', 
#    'Prepositions', 
#    'Conjunctions', 
#    'Negations', 
#    'Quantifiers', 
#    'Number', 
#    'Swear Words', 
#    'Social Processes', 
#    'Family', 
#    'Friends', 
#    'Humans', 
#    'Affective Processes',
#    'Positive Emotion', 
#    'Negative Emotion', 
#    'Anxiety', 
#    'Anger', 
#    'Sadness', 
#    'Cognitive Processes', 
#    'Insight',
#    'Causation', 
#    'Discrepancy', 
#    'Tentative', 
#    'Certainty', 
#    'Inhibition', 
#    'Inclusive', 
#    'Exclusive', 
#    'Perceptual Processes', 
#    'See', 
#    'Hear', 
#    'Feel', 
#    'Biological Processes', 
#    'Body', 
#    'Health', 
#    'Sexual',
#    'Ingestion',
#    'Relativity', 
#    'Motion', 
#    'Space', 
#    'Time', 
#    'Work',
#    'Achievement', 
#    'Leisure', 
#    'Home', 
#    'Money', 
#    'Religion', 
#    'Death', 
#    'Assent', 
#    'Nonfluencies', 
#    'Fillers', 
#    'Total first person',
#    'Total third person']

#LIWC features

#tests:
#jan 1, 2010 = 2 words
#1 jan, 2010 = 3 words
#Jan 1? so soon! = 1 sentence
#lkhj.iou = 1 word
#lkhj.'iou = 2 words
#lkhj'.iou = 1 word
# 1)2)3)4)5)6)7)8)9 = 2 words...?
# 1]2]3]4]5}6}7}8]9 = 1 word
# 1 2 3 4 5 6 7 8 9 = 1 word
# 1!2@3#4$5%6^7&8*9~0`0'0;0:0[0{0]0}0.0,0-0_0=0+0|0\0>0<0"0 0 0.0 = 1 word
# 1..2 = 1 word
# a..b = 2 words
# a.b = 1 word
# the "cat". the dog. = 1 sentence
# b :) :) c :) = 4 words, two unique
# asdf... = not a sentence
# asdf = not a sentence
# Mr. = sentence

def score_text(text, _dictionary,raw_counts=False, scores=None, unique_words=None):
    """Returns a sparse counter object of word frequencies or counts if raw_counts is specified
        @param scores: If you want to keep a running total, Scores should be
            a Counter of previous counts and raw_counts should be set to True!
        @param unique_words: Again, will be created if None. Should be a set().
            If used, you'll probably want to override the scores['Unique Words'] category.
    """
    assert _dictionary is not None, 'Dictionary not loaded, you need to load a .dic file, perhaps from LIWC...'
    if scores is None: scores = Counter()
    if unique_words is None: unique_words = set()
    _liwc_tokenizer = re.compile(r'(\d[^a-z\(\)]*|[a-z](?:[\'\.]?[a-z])*|(?<=[a-z])[^a-z0-9\s\(\)]+|[\(\)][^a-z]*)',re.UNICODE|re.IGNORECASE)
    
    sentence_terminated = True
    for line in text.strip().split('\n'):
        all_tokens = _liwc_tokenizer.findall(line.strip().lower())
        if not all_tokens:
            continue
        for i in range(len(all_tokens)):
            token = all_tokens[i]
            if len(token)==0: continue

            if token[0].isdigit(): #Numbers
                scores.update(_dictionary.score_word(token))
                sentence_terminated=False
            elif token[0].isalpha(): #Words
                unique_words.add(token)
                previous_token = all_tokens[i-1] if i>0 else ''
                next_token = all_tokens[i+1] if i<len(all_tokens)-1 else ''
                scores.update(_dictionary.score_word(token, previous_token, next_token))
                sentence_terminated=False
            else: #Punctuation and stuff
                scores.update(_dictionary.score_word(token))

            if token in Dictionary.sentence_punctuation and not sentence_terminated:
                scores['Sentences']+=1
                sentence_terminated = True

    if not sentence_terminated:
        scores['Sentences'] += 1

    scores['Unique Words'] = len(unique_words)
    scores['Words Per Sentence'] = scores['Word Count']/scores['Sentences'] if scores['Sentences'] > 0 else 0

    if not raw_counts:
        scores = normalize_scores(scores)

    return scores

def score_file(filename, raw_counts=False, scores=None, unique_words=None):
    return score_text(open(filename).read(), raw_counts=raw_counts, scores=scores, unique_words=unique_words)

def normalize_scores(scores, bound_scores=True):
    """@summary: Converts counts to percentages"""
    new_scores = Counter()
    for category, score in list(scores.items()):
        if category not in {'Word Count', 'Sentences', 'Words Per Sentence', 'Newlines'}:
            if scores['Word Count'] > 0:
                score = 100.0*score/scores['Word Count']
            elif score > 0:
                score = 100.0
            else:
                score = 0.0
            if bound_scores:  # Since certain categories can exceed word count
                score = min(100.0, max(0.0, score))  # Bounds it to [0,100]
        new_scores[category] = score
    return new_scores


class FeatureExtractor():
    
    def __init__(self):
        self._load_lexicons()
        self.glob_word = ""
        
    def _load_lexicons(self):
        self.subj_dic = pickle.load(open(os.path.join("lexicons",'subjective_lexicon_dic_py3.pkl'),'rb'),encoding="latin-1")
        self._dictionary = None
        self.load_dictionary(self.default_dictionary_filename())
        #Load the emotion lexicon dictionary
        p_file = open(os.path.join("lexicons","Emotion-Lexicon-Dictionary_py3.pkl"),"rb")
        self.emo_dic = pickle.load(p_file,encoding="latin-1")
        p_file.close()
        
        #Load the subjective lexicon dictionary
        p_file = open(os.path.join("lexicons","subjective_lexicon_dic_py3.pkl"),"rb")
        self.subj_dic = pickle.load(p_file,encoding="latin-1")
        p_file.close()
        
        stemmer = nltk.stem.porter.PorterStemmer()
        remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
        
        def stem_tokens(tokens):
            return [stemmer.stem(item) for item in tokens]
        
        '''remove punctuation, lowercase, stem'''
        def normalize_cosine(text):
            return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))
        
        self.vectorizer = TfidfVectorizer(tokenizer=normalize_cosine, stop_words='english')

    def default_dictionary_filename(self):
        return os.path.abspath(os.path.join("lexicons","LIWC2007_English100131.dic"))
    
    def load_dictionary(self,filename):
        self._dictionary = Dictionary(filename)

    def cosine_sim(self,text1, text2):
        tfidf = self.vectorizer.fit_transform([text1, text2])
        return ((tfidf * tfidf.T).A)[0,1]

    def find_smilies(self,text):
        smilies = [":)", ":P", ":b", ":-)", 
                   ":-P", ":-b", ";)", ";P", 
                   ";b", ";-)", ";-P", ";-b", 
                   "^_^", "=)", "=]"]
    
        eyes, noses, mouths = r":;8BX=^", r"-~'^_", r")(/\|DP^]"
        pattern1 = "[%s][%s]?[%s]" % tuple(map(re.escape, [eyes, noses, mouths]))
        counts = Counter(re.findall(pattern1,text))
        temp_counts = {}
        for smile in counts:
            if smile in smilies:
                temp_counts[smile] = counts[smile]
        return sum([temp_counts[item] for item in temp_counts])
        
        
    def get_feats(self,text):
        
        feats = {}
        for elem in subj_cats:
            feats[elem] = 0.0   
        feats["strong_pos_adj"] = 0.0
        feats["acknowledge"] = 0.0    
        feats["cause_verbs"] = 0.0
        feats["you_mod"] = 0.0
        feats["please_verb"] = 0.0
        feats["if-you"] = 0.0
        feats["negative_jargon"] = 0.0
        feats["smiley"] = 0.0
        feats["greetings"] = 0.0
        feats["congrats"] = 0.0
        feats["welcome"] = 0.0    
        for feat in _liwc_categories:
            feats[feat] = 0.0
        for feat in pos_tags:
            feats[feat] = 0.0
        for feat in emo_cats:
            feats[feat] = 0.0
        
    		#Use pattern.tag to get POS tags
        tags = nltk.pos_tag(text)
    		#Gather only the tags from the output of pattern.tag
        ptags = [t for w,t in tags]
    		#Dictionary used for hold the counts for each POS tag
        tag_dic = {}
    		#Create Dictionary element for each possible tag
        for t in pos_tags:
            tag_dic[t] = 0.0
    		#Count number of tags found within the text sample
        for t in ptags:
            if t in tag_dic:
                tag_dic[t] += 1
    		#Append each tag frequency to the row
    		#If tag was not present append 0
        for t in pos_tags:
            if len(ptags) == 0:
                feats[t] = 0.0
            else:
                feats[t] = (tag_dic[t] / float(len(ptags)))
        wnl = WordNetLemmatizer()
        subj_parsed = [wnl.lemmatize(i) for i in nltk.word_tokenize(text)]
    #    subj_parsed = parse(text,chunks=False,lemmata=True).split(' ') 
        	#EMOTION LEXICON FEATURE EXTRACTION
    		#Use pattern.parse to get the parsed text
        words = subj_parsed[:]
        results = {}
    		#Dictionary used for hold the counts for each emotional category
        text_cats = {}
    		#Initialize all categories to 0 count
        for cat in emo_cats:
            text_cats[cat] = 0.0
        
        for key in self.emo_dic[list(self.emo_dic.keys())[0]]:
            results[key] = 0.0
    		#Separate the words given from pattern.parse into a list
    #    for word_emo in subj_parsed:
    #        words.append(word_emo.split('/')[0])
    		
        for word in words:
    			#To ensure the word is in the lexicon match the case by making all text lower case
            word = word.lower()
            self.glob_word = word
    			#Count the number of times a category is found
            if word in self.emo_dic:
                for cat in self.emo_dic[word]:
                    text_cats[cat+"_emo"] += float(self.emo_dic[word][cat])
    		#Append the emotion category frequency to the row
        for cat in text_cats:
            text_cats[cat] = text_cats[cat]/len(words)
            feats[cat] = text_cats[cat] 
        #Get Strong positive adjectives feature
        for word_strong in strong_pos_adjectives:
            feats["strong_pos_adj"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_strong), text.lower()))
        #Get Causative/subjunctive verbs
        for word_cause in cause_verbs:
            feats["cause_verbs"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_cause), text.lower()))
        #Get YouMod features
        for word_you in you_mod:
            feats["you_mod"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_you), text.lower()))
        #Get Negative Jargon features
        for word_neg in negative_jargon:
            feats["negative_jargon"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_neg), text.lower()))
        #Get Smiley features
        for word_smile in smile:
            feats["smiley"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_smile), text.lower()))
        feats["smiley"] += self.find_smilies(text)
        #Get Greetings features
        for word_greet in greetings:
            feats["greetings"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_greet), text.lower()))
        #Get congrats features
        for word_congrats in congrats:
            feats["congrats"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_congrats), text.lower()))
        #Get welcome features
        feats["welcome"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape("welcome"), text.lower()))
        #Get Acknowledge features
        for word_ack in acknowledge:
            feats["acknowledge"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word_ack), text.lower()))
        #Get if-you features
        feats["if-you"] += sum(1 for _ in re.finditer(r'\b%s\b' % re.escape("if you"), text.lower()))
        
        for index in range(len(subj_parsed)):
            word = subj_parsed[index]
            if word != '':
                
    #            parts = ptags[index]
                w = word
                pos = ptags[index]
    #            lem = parts[2]
                #Get Subjectivity Features 
                if w.lower() in self.subj_dic:
                    pos_temp = POS.get(pos,"anypos")
                    if pos_temp in self.subj_dic[w.lower()]:
                        subj = self.subj_dic[w.lower()][pos_temp]["type"].replace("subj","")
                        polarity = subj + "-" + self.subj_dic[w.lower()][pos_temp]['priorpolarity']
                        if polarity in subj_cats:
                            feats[polarity] += 1
    #            elif lem in subj_dic:
    #                pos_temp = POS.get(pos,"anypos")
    #                if pos_temp in subj_dic[lem]:
    #                    subj = subj_dic[lem][pos_temp]["type"].replace("subj","")
    #                    polarity = subj + "-" + subj_dic[lem][pos_temp]['priorpolarity']
    #                    if polarity in subj_cats:
    #                        feats[polarity] += 1
                #Get Please features
                if w.lower() == "please":
                    if index != len(subj_parsed)-1:
                        next_word = subj_parsed[index+1]
                        i = 2
                        flag = True
                        while(next_word == '' and flag):
                            if index+i >= len(subj_parsed):
                                flag = False
                                break
                            next_word = subj_parsed[index+i]
                            i += 1
                        if flag:
                            next_parts = ptags[index+1]
                            next_pos = pos_temp = POS.get(next_parts,"anypos")
                            if next_pos == "verb":
                                feats["please_verb"] += 1
        
        liwc_feats = score_text(text,self._dictionary)
        for feat in liwc_feats:
            if feat in feats:
                feats[feat] = liwc_feats[feat]
        for feat in feats:
            if feat not in liwc_feats:
    #            print(feat)
    #            print(type(feats[feat]))
    #            print(liwc_feats['Word Count'])
    ##            print(type(liwc_feats['Word Count']))
    #            if feat == "subj":
    #                for elem in subj_cats:
    #                    feats[feat][elem] = (feats[feat][elem] / liwc_feats['Word Count'])*100.0
    #            else:
                if liwc_feats['Word Count'] == 0:
                    feats[feat] = 0.0
                else:
                    feats[feat] = (feats[feat] / liwc_feats['Word Count'])*100.0
        for feat in punct_feats:
            count = 0
            for char in punct_feats[feat]:
                count += text.count(char)
            feats[feat] = count
        return feats

def order_feats(feats,feat_order):
    new_feats = []
    for feat in feat_order:
        new_feats.append(feats[feat])
    return np.array(new_feats)

if __name__ == "__main__":
    FE_ = FeatureExtractor()
    print("TESTING FEATURE EXTRACTOR")
    print(FE_.get_feats("Hello there! How is your day going? I hope you are having an amazing happy time!"))    
    print("SUCCESS!")
    
    