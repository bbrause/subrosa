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
from sklearn.preprocessing import minmax_scale

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

# Log in to database

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

# Read Speechtempo and Sentiment vectors

speechtempo_percent = pd.read_sql("select * from speechtempo_percent", conn, index_col="ID")
sentiment_percent = pd.read_sql("select * from sentiment_percent", conn, index_col="ID")

# Read docs of tokens, pos-tags and pure srts

docs_tokens = []

for file in os.listdir("pickles/docs_tokens/"):
  docs_tokens += pickle.load(open("pickles/docs_tokens/" + file, "rb"))

docs_pos_tags = []

for file in os.listdir("pickles/docs_pos_tags/"):
  docs_pos_tags += pickle.load(open("pickles/docs_pos_tags/" + file, "rb"))

srts_cleaned = []

for file in os.listdir("pickles/srts_cleaned/"):
  srts_cleaned += pickle.load(open("pickles/srts_cleaned/" + file, "rb"))

# Statistical calculations

def calc_standardized_typetoken(tokens, n):
    tokens = [''.join([c for c in token if c.isalpha()]) for token in tokens]
    chunks = [tokens[i:i+n] for i in range(0, len(tokens), n)]
    if len(chunks) > 1:
        chunks = chunks[:-1]
    typetokens = [(len(set(tokens)) / len(tokens)) for tokens in chunks]
    return sum(typetokens) / len(chunks)
    
def calc_standardized_entropy(tokens, n):
    tokens = [''.join([c for c in token if c.isalpha()]) for token in tokens]
    chunks = [tokens[i:i+n] for i in range(0, len(tokens), n)]
    if len(chunks) > 1:
        chunks = chunks[:-1]
    entropies = []
    for chunk in chunks:
      sum_ = 0
      for token in set(chunk):
        p = chunk.count(token) / len(chunk)
        sum_ += (p * np.log(p)) / np.log(len(chunk))
      entropies.append(-sum_)
    return sum(entropies) / len(chunks)
  
def calc_entropy(tokens):
    tokens = [''.join([c for c in token if c.isalpha()]) for token in tokens]
    sum_ = 0
    for token in set(tokens):
      p = tokens.count(token) / len(tokens)
      sum_ += (p * np.log(p))
    return -sum_
  
def calc_word_lengths(tokens):
    word_lengths = [len([c for c in token if c.isalpha()]) for token in tokens]
    short_word_ratio = len([w for w in word_lengths if w <= 3]) / len(word_lengths)
    mid_word_ratio = len([w for w in word_lengths if w > 3 and w <= 5]) / len(word_lengths)
    long_word_ratio = len([w for w in word_lengths if w > 5]) / len(word_lengths)
    return np.mean(word_lengths), short_word_ratio, mid_word_ratio, long_word_ratio
  
def calc_sentence_lengths(pos_tags):
    sentence_lengths = []
    len_sentence = 0
    for tag in pos_tags:
      if tag == "#":
        if len_sentence < 25:
          sentence_lengths.append(len_sentence)
        len_sentence = 0
      else:
        len_sentence += 1
    short_sent_ratio = len([s for s in sentence_lengths if s < 5]) / len(sentence_lengths)
    mid_sent_ratio = len([s for s in sentence_lengths if s >= 5 and s <= 7]) / len(sentence_lengths)
    long_sent_ratio = len([s for s in sentence_lengths if s > 7]) / len(sentence_lengths)
    return np.mean(sentence_lengths), short_sent_ratio, mid_sent_ratio, long_sent_ratio

# Create dataframe

stylometric_features = pd.DataFrame(0, index=ids["id"], columns=["sttr", "entropy", "mean_word_length", 
                                                                "short_word_ratio", "mid_word_ratio", "long_word_ratio", 
                                                                "mean_sentence_length", "short_sentence_ratio", "mid_sentence_ratio", "long_sentence_ratio", 
                                                                "mean_sentiment", "mean_words_per_second", "mean_silence_duration"])

stylometric_features["sttr"] = [calc_standardized_typetoken(doc,1000) for doc in docs_tokens]
stylometric_features["entropy"] = [calc_entropy(doc) for doc in docs_tokens]
sentence_data = [calc_sentence_lengths(doc) for doc in docs_pos_tags]
stylometric_features["mean_sentence_length"] = [doc[0] for doc in sentence_data]
stylometric_features["short_sentence_ratio"] = [doc[1] for doc in sentence_data]
stylometric_features["mid_sentence_ratio"] = [doc[2] for doc in sentence_data]
stylometric_features["long_sentence_ratio"] = [doc[3] for doc in sentence_data]
word_data = [calc_word_lengths(doc) for doc in docs_tokens]
stylometric_features["mean_word_length"] = [doc[0] for doc in word_data]
stylometric_features["short_word_ratio"] = [doc[1] for doc in word_data]
stylometric_features["mid_word_ratio"] = [doc[2] for doc in word_data]
stylometric_features["long_word_ratio"] = [doc[3] for doc in word_data]

# Determine silence stats from subtitle dataframes

mean_silence_duration = []
silence_ratio = []

for i,doc in enumerate(srts_cleaned):
  silence_durations = [0]
  silence_start = 0
  silence_end = 0
  for entry in doc[:-2]:
    if len(entry[3]) > 0:
      silence_end = entry[1].total_seconds()
      if silence_end - silence_start > 0.01:
        silence_durations.append(silence_end - silence_start)
      silence_start = entry[2].total_seconds()
  if min(1, sum(silence_durations[1:]) / doc[-1][2].total_seconds()) > 0.9:
    silence_durations = [d for d in silence_durations if d < np.median(silence_durations) + 2*np.std(silence_durations)]

  mean_silence_duration.append(np.mean(silence_durations[1:]))
  silence_ratio.append(min(1, sum(silence_durations[1:]) / doc[-1][2].total_seconds()))

stylometric_features["mean_silence_duration"] = mean_silence_duration
stylometric_features["silence_ratio"] = silence_ratio

# Determine mean values of sentiment and speech tempo (first sorting is necessary because these vectors come from database
# and are differently sorted than our metadata here)

stylometric_features = stylometric_features.sort_values(by="id")

stylometric_features["mean_sentiment"] = [np.mean(doc) for doc in sentiment_percent["SENTIMENT"]]
stylometric_features["mean_words_per_second"] = [np.mean(doc) for doc in speechtempo_percent["SPEECHTEMPO"]]

# Store to database

stylometric_features.to_sql("stylometric_features", conn, index=True)

# Minmax-scale each feature individually

stylometric_features_scaled = stylometric_features

for column in stylometric_features_scaled.columns:
  min_ = min(stylometric_features_scaled[column])
  max_ = max(stylometric_features_scaled[column])
  stylometric_features_scaled[column] = [(x - min_)/(max_ - min_) for x in stylometric_features_scaled[column]]

# Determine mean value of l2-normalization factor among vectors

sums = []
for i, row in stylometric_features_scaled.iterrows():
  sum_ = sum([x*x for x in row.values])
  sum_ = np.sqrt(sum_)
  sums.append(sum_)
  
stylometric_features_norm_factor = np.mean(sums)

# Normalize by this factor

stylometric_features_scaled_normalized = stylometric_features_scaled
for i, row in stylometric_features_scaled_normalized.iterrows():
  stylometric_features_scaled_normalized.loc[row.name] = [(x/stylometric_features_norm_factor) for x in row.values]

# Store

stylometric_features_scaled.to_sql("stylometric_features_sn", conn, index=True)






