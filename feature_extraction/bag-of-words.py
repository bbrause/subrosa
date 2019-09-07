import pickle
import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def adapt_array(arr):
    return arr.tobytes()

def convert_array(text):
    return np.frombuffer(text)
  
sqlite3.register_adapter(np.array, adapt_array)    
sqlite3.register_converter("array", convert_array)

def dummy_fun(doc):
  return doc

ids = pd.read_csv("imdb_sub_ids.tsv", sep="\t")
ids = ids.drop(ids.columns[0], axis = 1)

docs_lemmatized = []

for file in os.listdir("pickles/docs_lemmatized/"):
  docs_lemmatized += pickle.load(open("pickles/docs_lemmatized/" + file, "rb"))
  
vect = TfidfVectorizer(analyzer='word',
                tokenizer=dummy_fun,
                preprocessor=dummy_fun,
                token_pattern=None,
                sublinear_tf=True,
                use_idf=True,
                min_df = 0.025,
                max_df = 0.95,
                ngram_range=(1,1),
                #norm=None
                )

tfidf_lemmatized = vect.fit_transform(docs_lemmatized)

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

tokens_id = pd.DataFrame(vect.get_feature_names(), columns=["word"])
tokens_id["id"] = tokens_id.index
tokens_id.set_index("word")
tokens_id.to_sql("lemmatizedtokens_id", conn, index=True)

pd.DataFrame(vect.idf_, columns=["idf"]).to_sql("lemmatizedtokens_idf", conn, index=True)


cur.execute("create table lemmatizedtokens_tfidf (ID integer primary key, TOKENS array)")

cur.execute("begin")
for i in range(len(docs_lemmatized)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into lemmatizedtokens_tfidf (ID, TOKENS) values (?, ?)", (imdb_id, tfidf_lemmatized[i].toarray()[0]))
cur.execute("commit")