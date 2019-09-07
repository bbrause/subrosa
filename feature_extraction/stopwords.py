import pickle
import os
import sqlite3
import numpy as np
import pandas as pd
from nltk import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

def adapt_array(arr):
    return arr.tobytes()

def convert_array(text):
    return np.frombuffer(text)
  
sqlite3.register_adapter(np.array, adapt_array)    
sqlite3.register_converter("array", convert_array)

stopwords_edited = ['you',
 'i',
 'the',
 'to',
 "'s",
 'a',
 'it',
 'that',
 "n't",
 'and',
 'do',
 'of',
 'is',
 'what',
 'we',
 'in',
 'me',
 'this',
 'on',
 'he',
 'my',
 'your',
 'no',
 'for',
 'have',
 'are',
 "'m",
 "'re",
 'not',
 'be',
 'was',
 'all',
 'here',
 'with',
 'there',
 'just',
 'they',
 'but',
 'so',
 "'ll",
 'can',
 'did',
 'him',
 'now',
 'she',
 'if',
 'about',
 'at',
 'get',
 'got',
 'how',
 'will',
 'let',
 'her',
 "'ve",
 'well',
 'who',
 'yes',
 'why',
 'from',
 'as',
 'where',
 'his',
 'going',
 'us',
 'them',
 'would',
 'when',
 'an',
 'could',
 'were',
 'or',
 'been',
 'some',
 'our',
 'then',
 'had',
 "'d",
 'please',
 'something',
 'too',
 'really',
 'never',
 'has',
 'by',
 'does',
 'very',
 'should',
 'am',
 'doing',
 'any',
 'because',
 'which',
 'only']


def dummy_fun(doc):
  return doc
  
def preprocessor(doc):
  out =[]
  for w in doc:
    w = w.strip(string.punctuation)
    w = w.strip(" ")
    if len(w) > 0:
      if "'" in w:
        w = word_tokenize(w)
      if type(w) == list:
        out.extend(w)
      else:
        out.append(w)
  return out

ids = pd.read_csv("imdb_sub_ids.tsv", sep="\t")
ids = ids.drop(ids.columns[0], axis = 1)

docs_tokens = []

for file in os.listdir("pickles/docs_tokens/"):
  docs_tokens += pickle.load(open("pickles/docs_tokens/" + file, "rb"))
  
vect = TfidfVectorizer(analyzer='word',
                tokenizer=dummy_fun,
                preprocessor=preprocessor,
                token_pattern=None,
                use_idf=False,
                vocabulary = stopwords_edited,
                ngram_range=(1,1)
                )

tf_stopwords = vect.fit_transform(docs_tokens)

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

stopwords_ids = pd.DataFrame(vect.get_feature_names(), columns=["word"])
stopwords_ids["id"] = stopwords_ids.index
stopwords_ids.set_index("word")
stopwords_ids.to_sql("stopwords_id", conn, index=True)

pd.DataFrame(vect.idf_, columns=["idf"]).to_sql("pos_trigrams_idf", conn, index=True)


cur.execute("create table stopwords_tf (ID integer primary key, STOPWORDS array)")

cur.execute("begin")
for i in range(len(docs_tokens)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into stopwords_tf (ID, STOPWORDS) values (?, ?)", (imdb_id, tf_stopwords[i].toarray()))
cur.execute("commit")