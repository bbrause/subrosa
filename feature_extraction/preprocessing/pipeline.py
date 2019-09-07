import pandas as pd
import time
import spacy
import pickle

nlp = spacy.load("en_core_web_md")
sub_ids = pd.read_csv("../imdb_sub_ids.tsv", sep="\t")

docs_tokens = []
docs_lemmatized = []
docs_pos_tags = []
srts_cleaned = []

srts = []

count = 0
chunk_size=100
chunk_count = 0

doc_index = 0

for index, row in sub_ids.iterrows():
    count += 1
    
    srt = parse_srt(gunzip(os.path.join("subtitles",str(row["sub_id"]) + ".gz")))
    srt = clean_srt(srt)
    
    srt = get_continous_text(srt)
    
    srts.append(srt)
    
    if count == chunk_size or index == len(sub_ids)-1:
      t0 = time.time()
      count = 0
      
      for doc in nlp.pipe(srts, batch_size=10000, n_threads=2):
        doc_tokens = []
        doc_lemmatized = []
        doc_pos_tags = []
        
        for t in doc:
          if t.is_sent_start:
            doc_pos_tags.append("#")
          if t.is_alpha and not t.is_punct and not t.is_stop:
            if t.ent_type not in [378,381,386]:
              doc_tokens.append(t.lower)
              doc_lemmatized.append(t.lemma_)
            else:
              doc_lemmatized.append("-NE-")
          doc_pos_tags.append(t.tag_)
        
        docs_tokens.append(doc_tokens)
        docs_lemmatized.append(doc_lemmatized)
        docs_pos_tags.append(doc_pos_tags)
        
        doc_index += 1
        return
        
      pickle.dump(docs_tokens, open("../pickles/docs_tokens/docs_tokens_{:04d}.pkl".format(chunk_count), "wb"))
      pickle.dump(docs_lemmatized, open("../pickles/docs_lemmatized/docs_lemmatized_{:04d}.pkl".format(chunk_count), "wb"))
      pickle.dump(docs_pos_tags, open("../pickles/docs_pos_tags/docs_pos_tags_{:04d}.pkl".format(chunk_count), "wb"))
      pickle.dump(srts_cleaned, open("../pickles/srts_cleaned/srts_cleaned_{:04d}.pkl".format(chunk_count), "wb"))
        
      print(time.time()-t0, end=",", flush=True)
      srts_cleaned = []
      docs_tokens = []
      docs_lemmatized = []
      docs_pos_tags = []
      srts = []
      
      chunk_count += 1
      
  