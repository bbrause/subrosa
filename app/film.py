# SUB ROSA v0.1
# 2019
#
# author:  Jan Luhmann
# license: GNU General Public License v3.0

import numpy as np
from database import Database

class Film:
    # Each instance of this class represents a film containing its metadata, vectors and distances
    # to other films.

    def __init__(self, film_id):
        # Inititalize with ID and empty dict of distances
        self.id = int(film_id)
        self.distances = {}
        
    def set_metadata(self, *args):
        # Set its metadata with data from database.
        db = None
        metadata = None
        
        for arg in args:
            if isinstance(arg, Database) and db is None:
                db = arg
            elif isinstance(arg, tuple) and metadata is None:
                metadata = arg
        
        if metadata is None and db is not None:
            metadata = db.get_metadata(self.id)
        
        if int(metadata[0]) != int(self.id):
            print("Cannot set metadata because film ID does not match!")
            return
        
        self.title = metadata[1]
        self.year = metadata[2]
        self.genres = [g.strip(" ,") for g in metadata[3].split(" ")]
        self.runtime = metadata[4]
        self.num_votes = metadata[5]
        self.rating = metadata[6]
        self.sub_id = metadata[7]
        self.main_genre = metadata[8]
        
        
    def build_vectors(self, db):
        # Get all its vectors from database
        # @return: tuple of vectors
        vectors = None

        for feature_set in ["lemmatizedtokens_vectors", "pos_trigrams_vectors",
                            "stopwords_vectors", "speechtempo_percent_ssn", "sentiment_percent_ssn", "stylometric_features_sn"]:
            data = db.get_vector(feature_set, self.id)
            if vectors is None:
                vectors = data
            else:
                if data[0] == vectors[0]:
                    vectors = vectors + (data[1],)

        if vectors is None:
            return None

        return vectors[1:]

    def set_vectors(self, vectors):
        # Given vectors, set them as attribute of instance.
        self.vectors = vectors
        
    def set_detail_data(self, db):
        # Set all data for detail view
        self.top_tokens = self.set_top_tokens(db)
        self.top_postags = self.set_top_postags(db)
        self.top_stopwords = self.set_top_stopwords(db)

        data = db.get_detail_data(self.id)
        
        self.sttr = data[0][0]
        self.entropy = data[0][1]
        self.mean_word_length = data[0][2]
        self.short_word_ratio, self.mid_word_ratio, self.long_word_ratio = data[0][3:6]
        self.mean_sentence_length = data[0][6]
        self.short_sentence_ratio, self.mid_sentence_ratio, self.long_sentence_ratio = data[0][7:10]
        self.mean_sentiment = data[0][10]
        self.mean_words_per_second = data[0][11]
        self.mean_silence_duration = data[0][12]
        self.silence_ratio = data[0][13]
        
        self.speechtempo_percent = data[1]
        self.speechtempo_minute = data[2]
        self.sentiment_percent = data[3]
        self.sentiment_minute = data[4]
        
    def set_distance(self, film_id, distance):
        # Given another ID of film and distance,
        # save this to distance dict in attributes.
        if film_id == self.id:
            return None
        self.distances[film_id] = distance

    def set_top_tokens(self, db):
        # For Bag-of-Words model, get most significant terms to attribute
        # @return: list of tuples (token rank, term, token weight value)
        tokens_vector = self.vectors[0]
        top_tokens = [(i, x) for (i, x) in enumerate(tokens_vector) if x > 0]
        top_tokens_words = db.get_terms("lemmatizedtokens_id", top_tokens)

        self.tokens_score_mean = None
        self.tokens_score_std = None

        return top_tokens_words

    def set_top_postags(self, db):
        # Same as set_top_tokens, but for POS Tag Trigrams model.
        postags_vector = self.vectors[1]
        top_postags = [(i, x) for (i, x) in enumerate(postags_vector) if x > 0]
        top_postags = db.get_terms("pos_trigrams_id", top_postags)

        return top_postags

    def set_top_stopwords(self, db):
        # Same as set_top_tokens, but for Stopwords Distribution model.
        stopwords_vector = self.vectors[2]
        top_stopwords = [(i, x) for (i, x) in enumerate(stopwords_vector) if x > 0]
        top_stopwords = db.get_terms("stopwords_id", top_stopwords)

        return top_stopwords

