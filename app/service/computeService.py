from collections import defaultdict
import math

def newUserTastes(user_genres, favoriteMovieData):
    genre_count = defaultdict(int)
    director_count = defaultdict(int)
    actor_count = defaultdict(int)
    
    # print(f"data: {favoriteMovieData}") 
    era_counter = {
    'classic': 0,
    'modern': 0
    }

    genre_score = {}
    director_score = {}
    actor_score = {}
    era_score = {}
    normalized_rating_sum = 0.0
    normalized_popularity_sum = 0.0

    for genre_id in user_genres:
        genre_count[genre_id] += 1

    for movie in favoriteMovieData:
        
        year = movie['release_year']
        # print(f"release_year: {year}, type: {type(year)}") 
        if not year:
            continue
        year = int(year)
        if year < 2000:
            era_counter['classic'] += 1
        else:
            era_counter['modern'] += 1

        for d_id in movie.get('director_ids', []):
            director_count[d_id] += 1

        for a_id in movie.get('actor_ids', []):
            actor_count[a_id] += 1

        for genre_id in movie.get('genre_ids', []):
            genre_count[genre_id] += 1

        normalized = movie.get('normalized_data', {})
        normalized_rating_sum += float(normalized.get('n_rating', 0) or 0)
        normalized_popularity_sum += float(normalized.get('n_popularity', 0) or 0)

    total_genre = sum(genre_count.values()) or 0
    total_director = sum(director_count.values()) or 0
    total_actor = sum(actor_count.values()) or 0
    movie_count = len(favoriteMovieData) or 0

    for g, count in genre_count.items():
        genre_score[g] = round(count / total_genre,2)

    for d, count in director_count.items():
        director_score[d] = round(count / total_director,2)

    for a, count in actor_count.items():
        actor_score[a] = round(count / total_actor,2)
        
    for era,count in era_counter.items():
        era_score[era] = round(count / movie_count,2)
        
    preferred_normalized_rating = round(normalized_rating_sum / movie_count,2)
    preferred_normalized_popularity = round(normalized_popularity_sum / movie_count,2)
    
    return {
        'preferred_genres': genre_score,
        'preferred_directors': director_score,
        'preferred_actors': actor_score,
        'preferred_era':era_score,
        'preferred_normalized_rating': preferred_normalized_rating,
        'preferred_normalized_popularity': preferred_normalized_popularity,
    }
    
def gaussian_score(preferred, actual, sigma):
    return round(math.exp(-((actual - preferred) ** 2) / (2 * sigma ** 2)), 2)

def final_score(genre_score, director_score, actor_score, era_score, rating_score, popularity_score):
    WEIGHTS = {
            'genre'      : 0.45,
            'director'   : 0.15,
            'actor'      : 0.15,
            'era'        : 0.10,
            'rating'     : 0.05,
            'popularity' : 0.10,
    }
        
    return round(
        WEIGHTS['genre']      * genre_score      +
        WEIGHTS['director']   * director_score   +
        WEIGHTS['actor']      * actor_score      +
        WEIGHTS['era']        * era_score        +
        WEIGHTS['rating']     * rating_score     +
        WEIGHTS['popularity'] * popularity_score,
        2
    )

def newUserRecommendation(userGenres, userTastes, movies):
    genre_weight    = defaultdict(float)
    director_weight = defaultdict(float)
    actor_weight    = defaultdict(float)
    era_weight    = defaultdict(float)

    movie_genre_score      = defaultdict(float)
    movie_director_score   = defaultdict(float)
    movie_actor_score      = defaultdict(float)
    movie_final_scores     = defaultdict(float)

    preferredActors     = userTastes.get('preferred_actors', {})
    preferredDirectors  = userTastes.get('preferred_directors', {})
    preferredEra        = userTastes.get('preferred_era', {})
    preferredRating     = userTastes.get('preferred_normalized_rating', 0)
    preferredPopularity = userTastes.get('preferred_normalized_popularity', 0)

    # print(f"preferredActors: {preferredActors}")
    # print(f"preferredDirectors: {preferredDirectors}")
    # print(f"preferredEra: {preferredEra}")
    # print(f"preferredRating: {preferredRating}")
    # print(f"preferredPopularity: {preferredPopularity}")

    for era_key, weight in preferredEra.items():
        era_weight[era_key] = weight

    for director_id, weight in preferredDirectors.items():
        director_weight[int(director_id)] = weight

    for actor_id, weight in preferredActors.items():
        actor_weight[int(actor_id)] = weight

    for ug in userGenres:
        genre_id = ug.get('genre_id')
        genre_weight[int(genre_id)] = ug.get('weight', 0)

    # print(f"genre_weight: {dict(genre_weight)}")
    # print(f"director_weight: {dict(director_weight)}")
    # print(f"actor_weight: {dict(actor_weight)}")
    # print(f"actor_weight: {dict(era_weight)}")

    
    
    for m in movies:
        movie_id     = m.get('movie_id')
        release_year = m.get('release_year')
        normalized   = m.get('normalizedData') or {}
        # Genre score
        movie_genres = m.get('genre_ids', [])
        # print(f"movie genre: {movie_genres}")
        
        if not movie_genres:
            movie_genre_score[movie_id] = 0
        else:
            genre_total = sum(genre_weight[int(mg)] for mg in movie_genres)
            movie_genre_score[movie_id] = round(genre_total / len(movie_genres), 2)
        # print(f"+movie genre weight: {genre_total}")

        # Director score
        movie_directors = m.get('director_ids') or []
        # print(f"movie director: {movie_directors}")
        if not movie_directors:
            movie_director_score[movie_id] = 0
        else:
            director_total = sum(director_weight[d] for d in movie_directors)
            movie_director_score[movie_id] = round(director_total / len(movie_directors), 2)
        # print(f"+movie director weight: {director_total}")

        # Actor score
        movie_actors = m.get('actor_ids') or []
        # print(f"movie actor: {movie_actors}")
        if not movie_actors:
            movie_actor_score[movie_id] = 0
        else:
            actor_total = sum(actor_weight[a] for a in movie_actors)
            movie_actor_score[movie_id] = round(actor_total / len(movie_actors), 2)
        # print(f"+movie director weight: {actor_total}")

        # Rating & popularity score
        movie_rating_score     = gaussian_score(preferredRating, normalized.get('n_rating', 0),0.2)
        movie_popularity_score = gaussian_score(preferredPopularity, normalized.get('n_popularity', 0),0.2)
        # print(f"+movie rating score: {movie_rating_score}")
        # print(f"+movie popularity score: {movie_popularity_score}")

        # Era score
        if release_year:
            movie_era       = 'modern' if int(release_year) >= 2000 else 'classic'
            movie_era_score = era_weight.get(movie_era, 0)
        else:
            movie_era_score = 0
        # print(f"+movie era score: {movie_era_score}")
        # Final score
        movie_final_scores[movie_id] = final_score(
            movie_genre_score[movie_id],
            movie_director_score[movie_id],
            movie_actor_score[movie_id],
            movie_era_score,
            movie_rating_score,
            movie_popularity_score
        )
        # print(f"+movie final  score: {movie_final_scores[movie_id]}")

    recommendation_ids = sorted(
        movie_final_scores,
        key=lambda x: movie_final_scores[x],
        reverse=True
    )[:40]
    for id in recommendation_ids:
        score = movie_final_scores[id]
        #print(f'hasil rekomendasi: {id} score : {score}')
    return recommendation_ids

def exponentialMovingAverage(currentValue, array ):
    if not array:
        return currentValue
    alpha = 0.1
    avgNewValue = round(sum(array)/len(array),2)
    value = round(((1-alpha) * currentValue) + (alpha*avgNewValue),2)
    return value

def recomputeTastes(userGenres,userTastes,userLog,movies):
    activity_score = {
        'click' : 0.1,
        'watch_trailer' : 0.2,
        'watchlist' : 0.25,
        'favorite' : 0.35,
        'search' : 0.1,
    }
    old_weight = 0.6
    current_genre_score = defaultdict(float)
    movie_log_score = defaultdict(float)
    final_actor_score = defaultdict(float)
    final_director_score = defaultdict(float)
    final_era_score = defaultdict(float)
    final_genre_score = defaultdict(float)
    new_rating_score = []
    new_popularity_score = []
    
    ##userTaste
    current_director_score   = defaultdict(float, {int(k): v *old_weight for k, v in (userTastes.get('preferred_directors') or {}).items()})
    current_actor_score      = defaultdict(float, {int(k): v *old_weight  for k, v in (userTastes.get('preferred_actors') or {}).items()})
    current_era_score = defaultdict(float, {
            k: v * old_weight 
            for k, v in (userTastes.get('preferred_era') or {}).items()
        })
    current_popularity_score = userTastes.get('preferred_normalized_popularity', 0)
    current_rating_score     = userTastes.get('preferred_normalized_rating', 0)
    
    ##userGenre
    for ug in userGenres:
        genre_id = ug.get('genre_id')
        weight = ug.get('weight')
        current_genre_score[int(genre_id)] = weight
    for m in movies:
        movie_id = m.get('tmdb_movie_id')
        movie_log_score[movie_id] = sum(
            activity_score.get(l.get('type'), 0)
            for l in userLog
            if l.get('tmdb_movie_id') == movie_id
            )
        movie_genres = m.get('genre_ids')
        movie_directors = m.get('director_ids')
        movie_actors = m.get('actor_ids')
        normalized_data = m.get('normalized_data')
        movie_popularity = normalized_data.get('n_popularity')
        movie_rating = normalized_data.get('n_rating')
        movie_actors = m.get('actor_ids')
        movie_actors = m.get('actor_ids')
        release_year = m.get('release_year')
        movie_era = 'modern' if release_year and int(release_year) >= 2000 else 'classic'
        for mg in movie_genres:
            current_genre_score[int(mg)] += movie_log_score[movie_id]
        for md in movie_directors:
            current_director_score[int(md)] += movie_log_score[movie_id]
        for ma in movie_actors:
            current_actor_score[int(ma)] += movie_log_score[movie_id]
        current_era_score[str(movie_era)] += movie_log_score[movie_id]
        new_popularity_score.append(movie_popularity)
        new_rating_score.append(movie_rating)
        
    genre_total_score = sum(current_genre_score.values())
    for key, val in current_genre_score.items():
        final_genre_score[key] = round(val/genre_total_score,2)
    actor_total_score = sum(current_actor_score.values())
    for key, val in current_actor_score.items():
        final_actor_score[key] = round(val/actor_total_score,2)
    director_total_score = sum(current_director_score.values())
    for key, val in current_director_score.items():
        final_director_score[key] = round(val/director_total_score,2)
    era_total_score = sum(current_era_score.values())
    for key, val in current_era_score.items():
        final_era_score[key] = round(val/era_total_score,2)
    final_popularity_score = exponentialMovingAverage(current_popularity_score,new_popularity_score)
    final_rating_score = exponentialMovingAverage(current_rating_score,new_rating_score)
    return {
        'preferred_genres': final_genre_score,
        'preferred_directors': final_director_score,
        'preferred_actors': final_actor_score,
        'preferred_era':final_era_score,
        'preferred_normalized_rating': final_rating_score,
        'preferred_normalized_popularity': final_popularity_score,
    }


def calculate_intersect_genres(movies_data):
    """
    Menghitung film mana saja yang memiliki irisan genre kuat (outlier diabaikan).
    Sesuai PM Request: Cek pairwise (satu per satu), jika kedua film (2-2nya) memiliki 
    irisan genre > 0.5 (50%), maka ID film tersebut dikumpulkan.
    """
    if not movies_data:
        return []

    # Jika user cuma ngirim 1 film, langsung return id-nya
    if len(movies_data) == 1:
        first = movies_data[0]
        mid = first.get('id') or first.get('movie_id') or first.get('tmdb_movie_id')
        return [mid] if mid else [] # <-- Ubah jadi array id saja

    valid_movie_ids = set()
    valid_genres = set()

    # Logika "Satu film diambil satu film" (Pairwise Comparison)
    for i in range(len(movies_data)):
        movie_a = movies_data[i]
        genres_a = set(movie_a.get('genre_ids') or [])
        mid_a = movie_a.get('id') or movie_a.get('movie_id') or movie_a.get('tmdb_movie_id')

        for j in range(i + 1, len(movies_data)):
            movie_b = movies_data[j]
            genres_b = set(movie_b.get('genre_ids') or [])
            mid_b = movie_b.get('id') or movie_b.get('movie_id') or movie_b.get('tmdb_movie_id')

            if not genres_a or not genres_b:
                continue

            intersection = genres_a.intersection(genres_b)

            # Menghitung porsi irisan masing-masing 
            sim_a = len(intersection) / len(genres_a)
            sim_b = len(intersection) / len(genres_b)

            # "kalo semisal 2 2 nya lebih dari 0.5, dicocokkan semua / diambil"
            if sim_a >= 0.5 and sim_b >= 0.5:
                if mid_a: valid_movie_ids.add(mid_a)
                if mid_b: valid_movie_ids.add(mid_b)
                valid_genres.update(intersection)

    # Antisipasi kalau ternyata filmnya beda semua (outlier semua tidak ada yg nyambung)
    if not valid_movie_ids:
       return []
    return list(valid_movie_ids)