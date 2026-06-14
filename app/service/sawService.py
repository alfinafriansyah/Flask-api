import json
from pathlib import Path
from extension import r
import pandas as pd
import io
import logging

def calculate_saw(movies):
    # logic SAW di sini
    ranked_ids = []
    return ranked_ids

def calculate_coocurrence(user_input, movie_data, matrix):
    results = []
    total_user_genres = sum(user_input)

    # Convert list to dict if needed (matrix from JSON is a list)
    if isinstance(matrix, list):
        matrix = {str(item.get('genre_id', idx)): item for idx, item in enumerate(matrix)}

    for movie_id, row in movie_data.iterrows():
        raw_vector = row['vector']
        actual_vector = json.loads(raw_vector) if isinstance(raw_vector, str) else raw_vector

        match = [
            idx
            for idx, (u, m)
            in enumerate(zip(user_input, actual_vector))
            if u == 1 and m == 1
        ]

        if not match:
            results.append({
                'id': movie_id,
                'score': 0
            })
            continue

        match_set = set(match)
        other_genres = [
            idx
            for idx, val in enumerate(actual_vector)
            if val == 1 and idx not in match_set
        ]

        direct_score = round(len(match) / total_user_genres,2)

        # Menghitung relation score dengan aman dari Key JSON String
        relation_scores = []
        for m in match:
            genre_row = matrix.get(str(m + 1))
            if genre_row:
                cooc_vector = genre_row.get('cooccurrence_vector', [])
                for o in other_genres:
                    if 0 <= o < len(cooc_vector):
                        relation_scores.append(cooc_vector[o])

        relation_score = (
            round(sum(relation_scores) / len(relation_scores),1)
            if relation_scores else 0
        )

        final_score = round((
            0.7 * direct_score +
            0.3 * relation_score
        ),2)

        results.append({
            'id': movie_id,
            'score': final_score
        })

    return results


# PAKAI YANG INI SAJA (FUNGSI YANG DOUBLE DI BAWAHNYA SUDAH DIHAPUS)
def calculate_saw_discover_test(user_input, movie_ids):

    current_file = Path(__file__).resolve()
    root_path = current_file.parent.parent.parent
    file_path = root_path / "genre_cooccurrence.json"

    with open(file_path, "r", encoding="utf-8") as file:
        matrix = json.load(file)

    discover_cache = r.get('movie_normalized_data')
    if not discover_cache:
        logging.error("Redis key 'movie_normalized_data' tidak ditemukan")
        return []

    try:
        discover_cache_str = discover_cache.decode('utf-8') if isinstance(discover_cache, bytes) else discover_cache
        # Gunakan io.StringIO agar dibaca sebagai string buffer data, bukan path file
        raw_movie_data = pd.read_json(io.StringIO(discover_cache_str), orient='split')
        raw_movie_data.set_index('tmdb_movie_id', inplace=True)
    except Exception as e:
        logging.error(f"Gagal parse Redis cache: {e}")
        return []
    
    # 1. Menyelaraskan tipe data ID dari Laravel ke Integer
    movie_ids_int = [int(x) for x in movie_ids]
    
    # 2. Irisan index yang setara
    valid_movie = raw_movie_data.index.intersection(movie_ids_int)
    movie_data = raw_movie_data.loc[valid_movie].copy()
    
    if not movie_data.empty and isinstance(movie_data['vector'].iloc[0], str):
        movie_data['vector'] = movie_data['vector'].apply(json.loads)
    
    genre_coocurrence = calculate_coocurrence(user_input, movie_data, matrix)
    cooc_lookup = {item['id']: item['score'] for item in genre_coocurrence}
    
    weights = {'rating': 0.2, 'popularity': 0.2, 'genre': 0.6}

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    scored = []
    for movie_id, row in movie_data.iterrows():
        popularity_val = row['n_popularity'] if 'n_popularity' in row.index else row.get('n_popularity', 0)
        rating_val = row['n_rating'] if 'n_rating' in row.index else row.get('n_rating', 0)
        score = round(
            (
                safe_float(popularity_val) * weights['popularity'] +
                safe_float(rating_val) * weights['rating'] +
                safe_float(cooc_lookup.get(movie_id, 0)) * weights['genre']
            ), 
            2 # <--- Menentukan jumlah digit desimal (2 angka di belakang koma)
        )
        scored.append({'id': movie_id, 'score': score})
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    # 2. Batasi hanya mengambil 100 item teratas menggunakan slicing [:100]
    top_100_scored = scored[:100]
    #print(f"cooc score: {cooc_lookup}")
    #print(f"Movie ID & score: {top_100_scored}")
    # 3. Kembalikan array berisi ID film saja
    return [m['id'] for m in top_100_scored]

def calculate_saw_discover(movies):
    
    weights = {
        'rating':      0.5,
        'popularity':  0.3,
        'rating_count': 0.2,
    }

    if not movies:
        return []

    max_rating       = max(float(m['rating']) for m in movies) or 1
    max_popularity   = max(float(m['popularity']) for m in movies) or 1
    max_rating_count = max(float(m['rating_count']) for m in movies) or 1

    scored = []
    for m in movies:
        score = (
            (float(m['rating']) / max_rating) * weights['rating'] +
            (float(m['popularity']) / max_popularity) * weights['popularity'] +
            (float(m['rating_count']) / max_rating_count) * weights['rating_count']
        )
        scored.append({'id': m['id'], 'score': score})
    scored.sort(key=lambda x: x['score'], reverse=True)
    return [m['id'] for m in scored]