from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import io
import logging
import json
from extension import r

def get_all_similar_movies():
    
    discover_cache = r.get('movie_normalized_data')
    if not discover_cache:
        logging.error("Redis key 'movie_normalized_data' tidak ditemukan")
        return []

    try:
        discover_cache_str = discover_cache.decode('utf-8') if isinstance(discover_cache, bytes) else discover_cache
        raw_movie_data = pd.read_json(io.StringIO(discover_cache_str), orient='split')
        raw_movie_data.set_index('tmdb_movie_id', inplace=True)
        raw_movie_data['vector'] = raw_movie_data['vector'].apply(
        lambda x: json.loads(x) if isinstance(x, str) else x
    )
    except Exception as e:
        logging.error(f"Gagal parse Redis cache: {e}")
        return []
    popularity_dict = raw_movie_data['n_popularity'].to_dict()
    rating_dict = raw_movie_data['n_rating'].to_dict()
    movie_ids = raw_movie_data.index.tolist()
    matrix = np.array(raw_movie_data['vector'].tolist())
    
    all_results = {}

    for i, target_movie_id in enumerate(movie_ids):
        target_vec = matrix[i]
        
        other_ids = movie_ids[:i] + movie_ids[i+1:]
        other_matrix = np.delete(matrix, i, axis=0)
        
        # Hitung cosine similarity sekaligus
        similarities = cosine_similarity(
            other_matrix,
            target_vec.reshape(1, -1)
        ).flatten()
        
        recommendations = []
        
        for j, sim_score in enumerate(similarities):
            
            # Filter terlalu tidak mirip
            if sim_score < 0.3:
                continue
            
            other_movie_id = other_ids[j]
            rating_val = rating_dict[other_movie_id]
            popularity_val = popularity_dict[other_movie_id]
            
            # SAW scoring sama persis dengan fungsi lama
            final_score = (
                (sim_score * 0.80)
                + (rating_val * 0.15)
                + (popularity_val * 0.05)
            )
            
            recommendations.append({
                'id': other_movie_id,
                'final_score': round(float(final_score), 4)
            })
        
        # Sort by final_score, ambil top 10
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        similar_ids = [rec['id'] for rec in recommendations[:10]]
        r.set(f'movie_similar_{target_movie_id}', json.dumps(similar_ids))
    print("✅ Cache movie_similar selesai dibuat")
    return True
        
def get_similar_movies(target_movie, movies):

    target_vector = np.array(
        target_movie['movie_genre_vector']
    ).reshape(1, -1)

    recommendations = []

    for movie in movies:

        # SKIP jika movie yang sama
        if movie['id'] == target_movie['id']:
            continue

        movie_vector = np.array(
            movie['vector']
        ).reshape(1, -1)

        # HITUNG COSINE SIMILARITY
        similarity_score = cosine_similarity(
            target_vector,
            movie_vector
        )[0][0]

        # FILTER movie yang terlalu tidak mirip
        if similarity_score < 0.3:
            continue

        # NORMALISASI RATING
        normalized_rating = movie['rating']

        # NORMALISASI POPULARITY
        normalized_popularity = movie['popularity']

        # FINAL SCORE (Hybrid SAW Ranking)
        final_score = (
            (similarity_score * 0.80)
            +
            (normalized_rating * 0.15)
            +
            (normalized_popularity * 0.05)
        )

        recommendations.append({
            'id': movie['id'],
            'final_score': round(float(final_score), 4)
        })

    # SORT DESC
    recommendations = sorted(
        recommendations,
        key=lambda x: x['final_score'],
        reverse=True
    )

    # TOP 10
    top_movies = recommendations[:10]

    #print("Similar Movies:")
    #for movie in top_movies:
    #    print(f"  - {movie['id']}: {movie['final_score']}")

    # RETURN ID ONLY
    return [movie['id'] for movie in top_movies]