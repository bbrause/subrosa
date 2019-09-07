import pickle
import os
import sqlite3
import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def adapt_array(arr):
    return arr.tobytes()

def convert_array(text):
    return np.frombuffer(text)
  
sqlite3.register_adapter(np.array, adapt_array)    
sqlite3.register_converter("array", convert_array)

ids = pd.read_csv("imdb_sub_ids.tsv", sep="\t")
ids = ids.drop(ids.columns[0], axis = 1)

srts_cleaned = []

for file in os.listdir("pickles/srts_cleaned/"):
  srts_cleaned += pickle.load(open("pickles/srts_cleaned/" + file, "rb"))

sentiment = SentimentIntensityAnalyzer()

import time
from datetime import timedelta
import numpy as np

speechtempo_minute = []
sentiment_minute = []
speechtempo_percent = []
sentiment_percent = []

def interpolate(runtime, minutes):
  srt_segments_num_words = (int(runtime/minutes) + 1) * [0]
  srt_segments_sentiment = (int(runtime/minutes) + 1) * [0.0]
  line_counter = (int(runtime/minutes) + 1) * [0]

  for j, srt_row in srt.iterrows():
    start_min = int(srt_row["start"] / (minutes*60))
    end_min = int(srt_row["end"] / (minutes*60)) + 1
  
    for m in range(start_min, end_min):
      if srt_segments_num_words[m] <= minutes*300:
        srt_segments_num_words[m] += srt_row["n_words"] / (end_min - start_min)
        srt_segments_sentiment[m] += srt_row["sentiment"]
        line_counter[m] += 1
      else:
        print("over 300 words!")
  
  srt_segments_sentiment = [x/max(1,line_counter[i]) for i, x in enumerate(srt_segments_sentiment)]
  srt_segments_words_per_seconds = [x/(minutes*60) for x in srt_segments_num_words]
    
  return srt_segments_words_per_seconds, srt_segments_sentiment

t0 = time.time()

for i, row in ids.iterrows():
  if (i % 100) == 0:
    print(time.time() - t0)
    t0 = time.time()

  imdb_id = row["id"]
  srt = srts_cleaned[i]

  runtime = int(row["runtime"])
  
  if srt[-1][2].total_seconds() > runtime * 60:
    runtime = int(srt[-1][2].total_seconds() / 60) + 1

  srt = pd.DataFrame(srt, columns=["index", "start", "end", "text"])

  srt["start"] = srt["start"].apply(lambda x: x.total_seconds())
  srt["end"] = srt["end"].apply(lambda x: x.total_seconds())
  srt["num_words"] = srt["text"].apply(lambda x: min(30,len(x.split(" "))))
  srt["sentiment"] = srt["text"].apply(lambda x: sentiment.polarity_scores(x)["compound"])

  x, y = interpolate(runtime, 1)
  speechtempo_minute.append(x)
  sentiment_minute.append(y)
  x, y = interpolate(runtime, (runtime/100))
  speechtempo_percent.append(x[:100])
  sentiment_percent.append(y[:100])
  
  print(".", end="", flush=True)


conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

cur.execute("create table speechtempo_minute (ID integer primary key, SPEECHTEMPO array, LEN_ARRAY integer)")
cur.execute("begin")
for i in range(len(speechtempo_minute)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into speechtempo_minute (ID, SPEECHTEMPO, LEN_ARRAY) values (?, ?, ?)", (imdb_id, np.array(speechtempo_minute[i]), len(speechtempo_minute[i])))
cur.execute("commit")

cur.execute("create table speechtempo_percent (ID integer primary key, SPEECHTEMPO array)")
cur.execute("begin")
for i in range(len(speechtempo_percent)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into speechtempo_percent (ID, SPEECHTEMPO) values (?, ?)", (imdb_id, np.array(speechtempo_percent[i])))
cur.execute("commit")

cur.execute("create table sentiment_minute (ID integer primary key, SENTIMENT array, LEN_ARRAY integer)")
cur.execute("begin")
for i in range(len(sentiment_minute)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into sentiment_minute (ID, SENTIMENT, LEN_ARRAY) values (?, ?, ?)", (imdb_id, np.array(sentiment_minute[i]), len(sentiment_minute[i])))
cur.execute("commit")

cur.execute("create table sentiment_percent (ID integer primary key, SENTIMENT array)")
cur.execute("begin")
for i in range(len(sentiment_minute)):
    imdb_id = int(ids["id"].values[i])
    cur.execute("insert into sentiment_percent (ID, SENTIMENT) values (?, ?)", (imdb_id, np.array(sentiment_percent[i])))
cur.execute("commit")


speechtempo_percent = pd.read_sql("select * from speechtempo_percent", conn, index_col="ID")
sentiment_percent = pd.read_sql("select * from sentiment_percent", conn, index_col="ID")

speechtempo_percent_smoothed = speechtempo_percent
for i, row in speechtempo_percent_smoothed.iterrows():
  speechtempo_percent_smoothed.loc[row.name]["SPEECHTEMPO"] = [sum(row["SPEECHTEMPO"][i-2:i+3])/5 for i in range(2,len(row["SPEECHTEMPO"])-3,1)]

sentiment_percent_smoothed = sentiment_percent
for i, row in sentiment_percent_smoothed.iterrows():
  sentiment_percent_smoothed.loc[row.name]["SENTIMENT"] = [sum(row["SENTIMENT"][i-2:i+3])/5 for i in range(2,len(row["SENTIMENT"])-3,1)]


sums = []
for i, row in speechtempo_percent_smoothed.iterrows():
  sum_ = sum([x*x for x in row["SPEECHTEMPO"]])
  sum_ = np.sqrt(sum_)
  sums.append(sum_)
  
speechtempo_norm_factor = np.mean(sums)

sums = []
for i, row in sentiment_percent_smoothed.iterrows():
  sum_ = sum([x*x for x in row["SENTIMENT"]])
  sum_ = np.sqrt(sum_)
  sums.append(sum_)
  
sentiment_norm_factor = np.mean(sums)

speechtempo_percent_smoothed_normalized = speechtempo_percent_smoothed
for i, row in speechtempo_percent_smoothed_normalized.iterrows():
  speechtempo_percent_smoothed_normalized.loc[row.name]["SPEECHTEMPO"] = [(x/speechtempo_norm_factor) for x in row["SPEECHTEMPO"]]

sentiment_percent_smoothed_normalized = sentiment_percent_smoothed
for i, row in sentiment_percent_smoothed_normalized.iterrows():
  sentiment_percent_smoothed_normalized.loc[row.name]["SENTIMENT"] = [(x/sentiment_norm_factor) for x in row["SENTIMENT"]]

cur.execute("create table speechtempo_percent_ssn (ID integer primary key, SPEECHTEMPO array)")
cur.execute("begin")
for i, row in speechtempo_percent_smoothed_normalized.iterrows():
    cur.execute("insert into speechtempo_percent_ssn (ID, SPEECHTEMPO) values (?, ?)", (i, np.array(row["SPEECHTEMPO"])))
cur.execute("commit")

cur.execute("create table sentiment_percent_ssn (ID integer primary key, SENTIMENT array)")
cur.execute("begin")
for i, row in sentiment_percent_smoothed_normalized.iterrows():
    cur.execute("insert into sentiment_percent_ssn (ID, SENTIMENT) values (?, ?)", (i, np.array(row["SENTIMENT"])))
cur.execute("commit")




