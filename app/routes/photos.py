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
from app.core.pipeline import enhance_photo

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

    # position_data: None = mantieni, null esplicito = rimuovi, dict = aggiorna
    if 'position_data' in data:
        position_data = data['position_data']
        if position_data is not None and not isinstance(position_data, dict):
            return jsonify({'error': 'position_data deve essere un oggetto JSON {x, y, w, h}'}), 400
        serialized_pos = json.dumps(position_data) if position_data else None
    else:
        serialized_pos = photo['position_data']

    if not update_photo(
        photo_id=photo_id,
        page_number=data.get('page_number', photo['page_number']),
        position_data=serialized_pos,
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


def _enhance_one(photo, root):
    """Esegue la pipeline su una singola foto e aggiorna il DB. Ritorna (foto aggiornata, errore)."""
    original_abs = os.path.normpath(os.path.join(root, photo['original_path']))
    if not os.path.exists(original_abs):
        return None, f"File non trovato: {photo['original_path']}"

    folder = os.path.dirname(original_abs)
    filename = os.path.basename(original_abs)
    optimized_abs = os.path.join(folder, 'optimized', filename)

    enhance_photo(original_abs, optimized_abs)

    rel_path = os.path.join(
        'data', 'customer_photos', str(photo['project_id']), 'optimized', filename
    )
    update_photo(
        photo_id=photo['id'],
        page_number=photo['page_number'],
        position_data=photo['position_data'],
        optimized_path=rel_path,
    )
    return dict(get_photo_by_id(photo['id'])), None


@bp.route('/api/photos/<int:photo_id>/enhance', methods=['POST'])
def enhance_single(photo_id):
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({'error': 'Foto non trovata'}), 404

    root = os.path.normpath(os.path.join(current_app.root_path, '..'))
    result, err = _enhance_one(photo, root)
    if err:
        return jsonify({'error': err}), 404

    return jsonify(result)


@bp.route('/api/projects/<int:project_id>/enhance', methods=['POST'])
def enhance_project(project_id):
    if not get_project_by_id(project_id):
        return jsonify({'error': 'Progetto non trovato'}), 404

    photos = get_photos_by_project(project_id)
    if not photos:
        return jsonify({'error': 'Nessuna foto nel progetto'}), 404

    root = os.path.normpath(os.path.join(current_app.root_path, '..'))
    results, errors = [], []

    for photo in photos:
        result, err = _enhance_one(photo, root)
        if err:
            errors.append({'photo_id': photo['id'], 'error': err})
        else:
            results.append(result)

    return jsonify({'enhanced': results, 'errors': errors})
