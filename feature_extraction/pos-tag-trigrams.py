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

def ngram_preprocessor(doc):
  doc = [tag for tag in doc if tag not in string.punctuation + "''" + "``" + "HYPH" or tag == "#"] 
  out = []
  for i in range(len(doc)-3):
    if doc[i+1] != "#":
      out.append(' '.join(doc[i:i+3]))
  return out 

ids = pd.read_csv("imdb_sub_ids.tsv", sep="\t")
ids = ids.drop(ids.columns[0], axis = 1)

docs_pos_tags = []

for file in os.listdir("pickles/docs_pos_tags/"):
  docs_pos_tags += pickle.load(open("pickles/docs_pos_tags/" + file, "rb"))
  
vect = TfidfVectorizer(analyzer='word',
                tokenizer=dummy_fun,
                preprocessor=ngram_preprocessor,
                token_pattern=None,
                sublinear_tf=False,
                use_idf=True,
                min_df = 0.9,
                ngram_range=(1,1)
                )

tfidf_pos_tags = vect.fit_transform(docs_pos_tags)

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

trigrams_id = pd.DataFrame(vect.get_feature_names(), columns=["word"])
trigrams_id["id"] = tokens_id.index
trigrams_id.set_index("word")
trigrams_id.to_sql("pos_trigrams_id", conn, index=True)

pd.DataFrame(vect.idf_, columns=["idf"]).to_sql("pos_trigrams_idf", conn, index=True)


cur.execute("create table pos_trigrams_tfidf (ID integer primary key, POSTRIGRAMS array)")

cur.execute("begin")
for i in range(len(docs_pos_tags)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into pos_trigrams_tfidf (ID, POSTRIGRAMS) values (?, ?)", (imdb_id, tfidf_pos_tags[i].toarray()[0]))
cur.execute("commit")