from flask import Blueprint, request, jsonify
from app.service.edasService import calculate_edas_bestbygenre, calculate_edas_alltime

edas_bp = Blueprint('edas', __name__, url_prefix='/edas')


@edas_bp.route('/bestbygenre', methods=['POST'])
def bestbygenre():
    data       = request.get_json()
    movies     = data.get('movies', [])
    genre_name = data.get('genre_name', '')

    if not data or 'movies' not in data:
        return jsonify({'error': 'movies field is required'}), 400

    movies = data['movies']

    if not movies:
        return jsonify({'ranked_id': []}), 200

    ranked_ids = calculate_edas_bestbygenre(movies, genre_name)
    return jsonify({'ranked_id': ranked_ids})

@edas_bp.route('/alltime', methods=['POST'])
def alltime():
    data = request.get_json()

    if not data or 'movies' not in data:
        return jsonify({'error': 'movies field is required'}), 400

    movies = data['movies']

    if not movies:
        return jsonify({'ranked_id': []}), 200

    ranked_ids = calculate_edas_alltime(movies)
    return jsonify({'ranked_id': ranked_ids})