# SUB ROSA v0.1
# 2019
#
# author:  Jan Luhmann
# license: GNU General Public License v3.0

import pickle
import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Register adapter for storing numpy arrays in SQLite database

def adapt_array(arr):
    return arr.tobytes()

def convert_array(text):
    return np.frombuffer(text)
  
sqlite3.register_adapter(np.array, adapt_array)    
sqlite3.register_converter("array", convert_array)

# Read metadata

ids = pd.read_csv("imdb_sub_ids.tsv", sep="\t")
ids = ids.drop(ids.columns[0], axis = 1)

# Read docs of lemmatized tokens

docs_lemmatized = []

for file in os.listdir("pickles/docs_lemmatized/"):
  docs_lemmatized += pickle.load(open("pickles/docs_lemmatized/" + file, "rb"))
  
# Generate BOW vectors

def dummy_fun(doc):
  return doc

vect = TfidfVectorizer(analyzer='word',
                tokenizer=dummy_fun,
                preprocessor=dummy_fun,
                token_pattern=None,
                sublinear_tf=True,
                use_idf=True,
                min_df = 0.025,
                max_df = 0.95,
                ngram_range=(1,1)
                )

tfidf_lemmatized = vect.fit_transform(docs_lemmatized)

# Log into database

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

# Store indices of terms in database (for later detail view of top terms of documents)

tokens_id = pd.DataFrame(vect.get_feature_names(), columns=["word"])
tokens_id["id"] = tokens_id.index
tokens_id.set_index("word")
tokens_id.to_sql("lemmatizedtokens_id", conn, index=True)

# Store IDF values of terms

pd.DataFrame(vect.idf_, columns=["idf"]).to_sql("lemmatizedtokens_idf", conn, index=True)

# Store BOW vectors

cur.execute("create table lemmatizedtokens_tfidf (ID integer primary key, TOKENS array)")

cur.execute("begin")
for i in range(len(docs_lemmatized)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into lemmatizedtokens_tfidf (ID, TOKENS) values (?, ?)", (imdb_id, tfidf_lemmatized[i].toarray()[0]))
cur.execute("commit")