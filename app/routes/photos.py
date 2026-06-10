import json
import os

from flask import Blueprint, current_app, jsonify, request

from app.core.database import (
    add_photo,
    delete_photo,
    get_photo_by_id,
    get_photos_by_project,
    get_project_by_id,
    update_photo,
)

bp = Blueprint('photos', __name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}


def _photo_upload_dir(project_id):
    root = os.path.join(current_app.root_path, '..')
    path = os.path.join(root, 'data', 'customer_photos', str(project_id))
    os.makedirs(path, exist_ok=True)
    return path


@bp.route('/api/projects/<int:project_id>/photos', methods=['GET'])
def list_photos(project_id):
    if not get_project_by_id(project_id):
        return jsonify({'error': 'Progetto non trovato'}), 404
    photos = get_photos_by_project(project_id)
    return jsonify([dict(p) for p in photos])


@bp.route('/api/projects/<int:project_id>/photos', methods=['POST'])
def upload_photos(project_id):
    if not get_project_by_id(project_id):
        return jsonify({'error': 'Progetto non trovato'}), 404

    files = request.files.getlist('photos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Nessun file ricevuto (campo: photos)'}), 400

    upload_dir = _photo_upload_dir(project_id)
    created = []

    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': f"Formato non supportato: {f.filename}"}), 415

        dest = os.path.join(upload_dir, f.filename)
        f.save(dest)
        rel_path = os.path.join('data', 'customer_photos', str(project_id), f.filename)

        photo_id = add_photo(project_id, rel_path, sort_order=f.filename)
        if not photo_id:
            return jsonify({'error': f"Errore DB durante il salvataggio di {f.filename}"}), 500

        created.append(dict(get_photo_by_id(photo_id)))

    return jsonify(created), 201


@bp.route('/api/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({'error': 'Foto non trovata'}), 404
    return jsonify(dict(photo))


@bp.route('/api/photos/<int:photo_id>', methods=['PUT'])
def update(photo_id):
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({'error': 'Foto non trovata'}), 404

    data = request.get_json(silent=True) or {}

    position_data = data.get('position_data')
    if position_data is not None and not isinstance(position_data, dict):
        return jsonify({'error': 'position_data deve essere un oggetto JSON {x, y, w, h}'}), 400

    if not update_photo(
        photo_id=photo_id,
        page_number=data.get('page_number', photo['page_number']),
        position_data=json.dumps(position_data) if position_data else photo['position_data'],
        optimized_path=data.get('optimized_path', photo['optimized_path']),
    ):
        return jsonify({'error': "Errore durante l'aggiornamento"}), 500

    return jsonify(dict(get_photo_by_id(photo_id)))


@bp.route('/api/photos/<int:photo_id>', methods=['DELETE'])
def remove(photo_id):
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({'error': 'Foto non trovata'}), 404

    root = os.path.join(current_app.root_path, '..')
    abs_path = os.path.join(root, photo['original_path'])
    if os.path.exists(abs_path):
        os.remove(abs_path)

    delete_photo(photo_id)
    return '', 204
