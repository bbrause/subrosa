# SUB ROSA v0.1
# 2019
#
# author:  Jan Luhmann
# license: GNU General Public License v3.0

import numpy as np
from film import Film
from sklearn.metrics import pairwise_distances

def build_vector_matrix(db, batch_size=100, offset=0):
    # For a batch of films, builds a vector matrix from all feature models.
    # @return: list of tuples of vectors
    vector_matrix = None
    
    for feature_set in ["lemmatizedtokens_vectors", "pos_trigrams_vectors", "stopwords_vectors",
                       "speechtempo_percent_ssn", "sentiment_percent_ssn", "stylometric_features_sn"]:
        data = db.get_vectors_batch(feature_set, batch_size, offset)
        if data is None:
            return None
        
        if vector_matrix is None:
            vector_matrix = data
        else:
            for i, film in enumerate(data):
                if film[0] == vector_matrix[i][0]:
                    vector_matrix[i] = vector_matrix[i] + (film[1],)
    
    return vector_matrix
    

def calculate_distance_matrix(main_film_vector, vector_matrix, weights, metric="euclidean"):
    # For a given main Film vector and a given vector matrix (vectors of multiple films),
    # calculate distances according to given feature weights and metric.
    # @return: list of tuples (film_id, distance to main film)

    if len(main_film_vector) > 6:
        main_film_vector = main_film_vector[1:]
    
    main_film_vector = np.concatenate([weights[i] * main_film_vector[i] for i in range(0, 6)])
    
    film_ids = [film[0] for film in vector_matrix]
    
    vector_matrix = [np.concatenate([weights[i] * film[i+1] for i in range(0, 6)]) for film in vector_matrix]
    
    return list(zip(film_ids, pairwise_distances([main_film_vector], vector_matrix, metric=metric).flatten()))
    
    
def get_similar_films(db, main_film_id, weights=[1,1,1,1,1,1]):
    # Given a Film ID and feature weights, calculate distances of this film to all films in the database
    # using a batch_size of 100 films at a time
    # @return: Film instance of main film, list of Film instances of 100 nearest neighbours

    num_films = 100
    
    main_film = Film(main_film_id)
    vectors = main_film.build_vectors(db)
    if vectors is None:
        return None
    else:
        main_film.set_vectors(vectors)
    main_film.set_metadata(db)
    
    similar_films = []
    
    batch_size = 100
    offset = 0
    while True:
        vector_matrix = build_vector_matrix(db, batch_size, offset)
        if vector_matrix is None:
            break
        
        distance_matrix = calculate_distance_matrix(main_film.vectors, vector_matrix, weights)
        distance_matrix = [film for film in distance_matrix if int(film[0]) != int(main_film_id)]
        distance_matrix = [(distance_matrix[i] + (vector_matrix[i][1:],)) for i in range(0,len(distance_matrix)) 
                               if distance_matrix[i][0] == vector_matrix[i][0]]
        distance_matrix = sorted(distance_matrix, key=lambda x:x[1])
        
        similar_films += distance_matrix[:num_films]
        
        offset += batch_size
        
    similar_films = sorted(similar_films, key=lambda x:x[1])
    similar_films = similar_films[:num_films]
    
    similar_films_instances = []
    
    for film_id, distance, vectors in similar_films:
        similar_film = Film(film_id)
        similar_film.set_distance(main_film_id, distance)
        similar_film.set_metadata(db)
        similar_film.set_vectors(vectors)
        print(similar_film.title)
        similar_films_instances.append(similar_film)
    
    vector_matrix = [(film.id,) + film.vectors for film in similar_films_instances]
    for film in vector_matrix:
        distance_matrix = calculate_distance_matrix(film, vector_matrix, weights)
        for i, (film_id, dist) in enumerate(distance_matrix):
            if similar_films_instances[i].id != film_id:
                print("error!")
            similar_films_instances[i].set_distance(film[0], dist)
        
    return main_film, similar_films_instances
    
    
def update_film_distances(current_films, weights=[1,1,1,1,1,1]):
    # Given list of current Film instances and feature weights,
    # recalculate distances among them.
    # @return: updates list of Film instances
    vector_matrix = [(film.id,) + film.vectors for film in current_films]
        
    for film in vector_matrix:
        distance_matrix = calculate_distance_matrix(film, vector_matrix, weights)
        for i, (film_id, dist) in enumerate(distance_matrix):
            if current_films[i].id != film_id:
                print("error!")
            current_films[i].set_distance(film[0], dist)
        
    return current_films


def get_film(db, main_film_id):
    # Get Film instance for given ID from database
    # @return: Film instance
    main_film = Film(main_film_id)
    vectors = main_film.build_vectors(db)
    if vectors is None:
        return None
    main_film.set_vectors(vectors)
    main_film.set_metadata(db)
        
    return main_film
