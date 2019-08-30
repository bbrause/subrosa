# SUB ROSA v0.1
# 2019
#
# author:  Jan Luhmann
# license: GNU General Public License v3.0

import numpy as np
import webbrowser
from threading import Timer

from database import Database
from film import Film
from methods import *

from flask import Flask, request, jsonify, render_template
app = Flask(__name__)

def jsonify_films():
    # Attributes of instances of class "Film" contained in current_films are transferred to list "nodes"
    # and calculated distances between their feature vectors are transferred to list "links".
    # Distance values are normalized using zscores.
    # @return: JSON of dict containing "nodes" and "links"

    global current_films
    global weights
    nodes = []
    links = []
    all_ids = [f.id for f in current_films]
    for film in current_films:
        nodes.append({ "title": film.title,
                       "id": film.id,
                       "genre": film.main_genre,
                       "genres": film.genres,
                       "year": film.year,
                       "num_votes": film.num_votes })
        for linked_film_id, dist in film.distances.items():
                if linked_film_id in all_ids:
                    links.append({ "source": film.id,
                            "target": linked_film_id,
                            "distance": dist})

    if len(links) > 0:
        distances = [l["distance"] for l in links]
        dist_mean = np.mean(distances)
        dist_std = max(0.001,np.std(distances))
        for i in range(len(links)):
            links[i]["distance"] = (max(-2.5, min(10, (links[i]["distance"] - dist_mean)/dist_std)) / 5) + 0.5
    return jsonify({"nodes": nodes, "links": links})


def calculate_weights(weights_str):
    # Converts String of weights to float values and normalizes these values by their max value.
    # @return:  list of weights

    weights = weights_str.split("_")
    weights = [float(w) for w in weights]
    max_ = max(weights)
    weights = [w/max_ for w in weights]
    return weights


@app.route('/')
def start():
    return render_template('index.html')


@app.route('/get_search_data/', methods=['POST'])
def get_search_data():
    # Gets all movie titles, release year and their IDs from the database for autocomplete search.
    # @return: JSON of search data

    results = db.get_search_data()
    return jsonify({"results": results})


def append_to_current_films(films):
    # Appends an instance of Film to current_films, prevents doubles.

    global current_films
    for film in films:
        if film.id not in [f.id for f in current_films]:
            current_films.append(film)


@app.route('/add_film/<film_id>', methods=['POST'])
def add_film(film_id):
    # Processes the user request to add a new film to the canvas.
    # @return: updated graph data

    global current_films
    global weights
    for film_ in current_films:
        if film_.id == int(film_id):
            return 'Exists'
    film = get_film(db, film_id)
    if film is None:
        return 'None'
    append_to_current_films([film])
    return update_weights(weights)


@app.route('/add_similar_films/<film_id>/<number>/<weights>', methods=['POST'])
def add_similar_films(film_id, number, weights):
    # Processes the user request to add a number of similar films 
    # to a selected film by selected weights.
    # @return: updated graph data

    global current_films
    weights = calculate_weights(weights)
    number = int(number)
    result = get_similar_films(db, film_id, weights)
    if result is None:
        return 'None'
    else:
        film, similar_films = result
    similar_films = similar_films[:number]
    append_to_current_films([film] + similar_films)
    return update_weights(weights)


@app.route('/update_weights/<weights>', methods=['POST'])
def update_weights(weights):
    # Updates graph data based on given weights.
    # return: JSON of updated graph data

    global current_films
    if isinstance(weights, str):
        weights = calculate_weights(weights)
    update_film_distances(current_films, weights)
    return jsonify_films()

@app.route('/clear')
def clear():
    # Clears current_films
    # @return: String

    global current_films
    current_films = []
    return "success"

@app.route('/get_detail_data/<film_id>', methods=['POST'])
def get_detail_data(film_id):
    # Processes the request to fetch detail data of a Film.
    # Calculates top terms of Bag-of-Words, POS Tag Trigrams and Stopwords models.
    # @return: JSON of detail data

    global current_films
    global weights
    film = [f for f in current_films if int(f.id) == int(film_id)][0]
    if film == None:
        return 'None'

    if not hasattr(film, 'sttr'):
        film.set_detail_data(db)
    
    top_tokens = sorted([(word, score) for (i, word, score) in sorted(film.top_tokens, key=lambda x:x[2], reverse=True)[:200]], key=lambda x:x[0])
    score_mean = np.mean([score for (word, score) in top_tokens])
    film.tokens_score_mean = score_mean
    score_std = np.std([score for (word, score) in top_tokens])
    film.tokens_score_std = score_std
    top_tokens = [(word, (score - score_mean)/score_std) for (word, score) in top_tokens]
    
    top_postags = sorted([(term, round(score, 2)) for (i, term, score) in film.top_postags], key=lambda x:x[1], reverse=True)[:10]
    top_stopwords = sorted([(term, round(score, 2)) for (i, term, score) in film.top_stopwords], key=lambda x:x[1], reverse=True)[:10]

    output = {
        "top_tokens": top_tokens, 
        "top_postags": top_postags,
        "top_stopwords": top_stopwords,
        "stylometric_features": {
            "sttr" : film.sttr,
            "entropy": film.entropy,
            "mean_word_length": film.mean_word_length,
            "short_word_ratio": film.short_word_ratio,
            "mid_word_ratio": film.mid_word_ratio,
            "long_word_ratio": film.long_word_ratio,
            "mean_sentence_length": film.mean_sentence_length,
            "short_sentence_ratio": film.short_sentence_ratio,
            "mid_sentence_ratio": film.mid_sentence_ratio,
            "long_sentence_ratio": film.long_sentence_ratio,
            "mean_sentiment": film.mean_sentiment,
            "mean_words_per_second": film.mean_words_per_second,
            "mean_silence_duration": film.mean_silence_duration,
            "silence_ratio": film.silence_ratio
        },
        "sentiment":    {"percent": { "1": list(film.sentiment_percent),
                                    "2": list([np.mean(film.sentiment_percent[i:i+2]) for i in range(0, len(film.sentiment_percent), 2)]),
                                    "5": list([np.mean(film.sentiment_percent[i:i+5]) for i in range(0, len(film.sentiment_percent), 5)])
                        }, 
                        "minute": { "1": list(film.sentiment_minute),
                                    "2": list([np.mean(film.sentiment_minute[i:i+2]) for i in range(0, len(film.sentiment_minute), 2)]),
                                    "5": list([np.mean(film.sentiment_minute[i:i+5]) for i in range(0, len(film.sentiment_minute), 5)])
                        }
        },
        "speechtempo":  {"percent": { "1": list(film.speechtempo_percent),
                                    "2": list([np.mean(film.speechtempo_percent[i:i+2]) for i in range(0, len(film.speechtempo_percent), 2)]),
                                    "5": list([np.mean(film.speechtempo_percent[i:i+5]) for i in range(0, len(film.speechtempo_percent), 5)])
                        }, 
                        "minute": { "1": list(film.speechtempo_minute),
                                    "2": list([np.mean(film.speechtempo_minute[i:i+2]) for i in range(0, len(film.speechtempo_minute), 2)]),
                                    "5": list([np.mean(film.speechtempo_minute[i:i+5]) for i in range(0, len(film.speechtempo_minute), 5)])
                        }
        }
    }

    return jsonify(output)

@app.route('/get_compare_data/<film_left_id>/<film_right_id>', methods=['POST'])
def get_compare_data(film_left_id, film_right_id):
    # Calculates intersection of terms of Bag-of-Words model.
    # @return: JSON of top terms.

    film_left = None
    film_right = None

    found = 0

    for film in current_films:
        if found == 2:
            break
        if film.id == int(film_left_id):
            film_left = film
            found += 1
        elif film.id ==int(film_right_id):
            film_right = film
            found += 1
    
    if found < 2:
        return 'None'

    common_tokens = []
    film_right_token_indices = [i for (i, word, score) in film_right.top_tokens]

    for token in film_left.top_tokens:
        token_right_index = [i for i, token_index in enumerate(film_right_token_indices) if token_index == token[0]]
        if len(token_right_index) == 1:
            token_right_score = film_right.top_tokens[token_right_index[0]][2]
            common_tokens.append((token[1], token[2] + token_right_score))

    common_tokens = sorted([(word, score) for (word, score) in sorted(common_tokens, key=lambda x:x[1], reverse=True)[:200]], key=lambda x:x[0])
    score_mean = 0.9 * (film_left.tokens_score_mean + film_right.tokens_score_mean)
    score_std = 0.9 * (film_left.tokens_score_std + film_right.tokens_score_std)
    common_tokens = [(word, (score - score_mean)/score_std) for (word, score) in common_tokens]

    output = {
        "tokens" : common_tokens,
    }

    return jsonify(output)


if __name__ == '__main__':
    db = Database()
    current_films = []
    weights = [1,1,1,1,1,1]

    Timer(1.25, lambda: webbrowser.open("http://0.0.0.0:5000")).start()
    app.run(host="0.0.0.0", debug=False)
