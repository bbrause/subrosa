import sqlite3
import numpy as np
from database_helper import sparse_to_dense

class Database:
    
    feature_set_dict = {
            "lemmatizedtokens_vectors" : 0, "pos_trigrams_vectors" : 1, "stopwords_vectors" : 2,
            "speechtempo_percent_ssn" : 3, "sentiment_percent_ssn" : 4, "stylometric_features_sn" : 5 
    }
    
    def __init__(self):
        # Initialize numpy array adapter and converter
        def adapt_array(arr):
            return arr.tobytes()

        def convert_array(text):
            return np.frombuffer(text)
        
        sqlite3.register_adapter(np.array, adapt_array)    
        sqlite3.register_converter("array", convert_array)


    def get_db(self):
        # Try to connect to database
        # @return: connection, cursor (if successful)
        try:
            conn = sqlite3.connect("database_dense.db", detect_types=sqlite3.PARSE_DECLTYPES)
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            print(e)


    def get_search_data(self):
        # Gets all search data for autocomplete search box from Metadata table
        # @return: results as list of dicts
        conn, cursor = self.get_db()

        cursor.execute("SELECT ID, TITLE, YEAR FROM metadata ORDER BY id")
        data = cursor.fetchall()

        results = []

        for film in data:
            id = film[0]
            title = film[1]
            year = film[2]

            results.append({"label": title + " (" + str(year) + ")",
                            "value": id})
        
        conn.close()

        return results

            
    def get_vectors_batch(self, feature_set, batch_size = 100, offset = 0):
        # For a given feature model, gets a batch of vectors with a given offset.
        # @ return: list of tuples (film_id, film_vector)
        conn, cursor = self.get_db()

        cursor.execute("SELECT * FROM " + feature_set + " ORDER BY id LIMIT " + str(batch_size) + " OFFSET " + str(offset))
        data = cursor.fetchall()

        if len(data) == 0:
            return None
        
        feature_set = self.feature_set_dict[feature_set]
        output_data = []
        
        for film in data:
            film_id = film[0]
            
            if len(film) == 2:
                film_vector = film[1]
            else:
                film_vector = np.array(film[1:])

            #if feature_set in [0,1]:
                #film_vector = sparse_to_dense(film_vector)

            output_data.append((film_id, film_vector))
            
        conn.close()

        return output_data
    
    
    def get_vector(self, feature_set, film_id):
        # For a given feature model and given Film ID, gets that specific vector.
        # @return: tuple of (film_id, film_vector), if successful
        conn, cursor = self.get_db()

        feature_set_id = self.feature_set_dict[feature_set]
        
        cursor.execute("SELECT * FROM " + feature_set + " WHERE id=" + str(film_id))
        data = cursor.fetchall()

        if len(data) != 1:
            return None
        
        #if feature_set_id in [0,1]:
        #    data = [(film_id, sparse_to_dense(vector)) for film_id, vector in data][0]
        if feature_set_id == 5:
            data = [(film_data[0], np.array(film_data[1:])) for film_data in data][0]
        else:
            data = data[0]
        
        conn.close()
            
        return data
                
        
    def get_metadata_batch(self, film_ids):
        # For a given list of Film IDs, gets their metadata.
        # @return: list of tuples of metadata, if successful
        conn, cursor = self.get_db()

        cursor.execute("SELECT * FROM metadata WHERE id IN " + str(tuple(film_ids)))
        data = cursor.fetchall()

        conn.close()

        if len(data) == len(film_ids):
            return data
        else:
            return None
    
    
    def get_metadata(self, film_id):
        # Gets metadata of film of given ID.
        # @return: tuple of metadata, if successful
        conn, cursor = self.get_db()

        cursor.execute("SELECT * FROM metadata WHERE id=" + str(film_id))
        data = cursor.fetchall()

        conn.close()

        if len(data) == 1:
            return data[0]
        else:
            return None
        
        
    def get_detail_data(self, film_id):
        # Gets all data for detail views, for a film of given ID
        # @return: list of data
        conn, cursor = self.get_db()

        cursor.execute("SELECT * FROM stylometric_features WHERE id=" + str(film_id))
        data = cursor.fetchall()
        if len(data) == 1:
            data = data[0]
            stylometric_features = data[1:]
        else:
            return None
        
        cursor.execute("SELECT * FROM speechtempo_percent WHERE id=" + str(film_id))
        data = cursor.fetchall()
        if len(data) == 1:
            data = data[0]
            speechtempo_percent = data[1]
        else:
            return None
        
        cursor.execute("SELECT * FROM speechtempo_minute WHERE id=" + str(film_id))
        data = cursor.fetchall()
        if len(data) == 1:
            data = data[0]
            speechtempo_minute = data[1]
        else:
            return None
        
        cursor.execute("SELECT * FROM sentiment_percent WHERE id=" + str(film_id))
        data = cursor.fetchall()
        if len(data) == 1:
            data = data[0]
            sentiment_percent = data[1]
        else:
            return None
        
        cursor.execute("SELECT * FROM sentiment_minute WHERE id=" + str(film_id))
        data = cursor.fetchall()
        if len(data) == 1:
            data = data[0]
            sentiment_minute = data[1]
        else:
            return None

        conn.close()
        
        return [stylometric_features, speechtempo_percent, speechtempo_minute, sentiment_percent, sentiment_minute]

    
    def get_terms(self, feature_set, tokens):
        # Gets all terms of given feature_set corresponding to token indices of given list "tokens" 
        # @return: list of tuples (token rank, term, token weight)
        conn, cursor = self.get_db()

        token_indices = [i for (i, x) in tokens]

        cursor.execute("SELECT ID, WORD FROM " + feature_set + " WHERE ID IN " + str(tuple(token_indices)))
        data = cursor.fetchall()
        if len(data) != len(tokens):
            return None
        
        tokens = [(j, word, tokens[i][1]) for (i, (j, word)) in enumerate(data)]

        conn.close()

        return tokens

