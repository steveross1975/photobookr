import os
import shutil
import tempfile

from flask import Blueprint, current_app, jsonify, request

from app.core.database import (
    delete_template,
    get_all_templates,
    get_template_by_id,
    register_complete_template,
    update_template_complete,
)

bp = Blueprint('templates', __name__, url_prefix='/api/templates')


@bp.route('', methods=['GET'])
def list_templates():
    templates = get_all_templates()
    return jsonify([dict(t) for t in templates])


@bp.route('/<int:template_id>', methods=['GET'])
def get_template(template_id):
    template = get_template_by_id(template_id)
    if not template:
        return jsonify({'error': 'Template non trovato'}), 404
    return jsonify(dict(template))


@bp.route('', methods=['POST'])
def create_template():
    name = request.form.get('name')
    category = request.form.get('category')
    cover_file = request.files.get('cover')
    inner_file = request.files.get('inner')

    if not all([name, category, cover_file, inner_file]):
        return jsonify({'error': 'Campi richiesti: name, category, cover, inner'}), 400

    with tempfile.TemporaryDirectory() as tmp:
        cover_path = os.path.join(tmp, cover_file.filename)
        inner_path = os.path.join(tmp, inner_file.filename)
        cover_file.save(cover_path)
        inner_file.save(inner_path)
        template_id = register_complete_template(name, category, cover_path, inner_path)

    if not template_id:
        return jsonify({'error': 'Errore durante la creazione del template'}), 500

    return jsonify(dict(get_template_by_id(template_id))), 201


@bp.route('/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    if not get_template_by_id(template_id):
        return jsonify({'error': 'Template non trovato'}), 404

    name = request.form.get('name')
    category = request.form.get('category')
    if not all([name, category]):
        return jsonify({'error': 'Campi richiesti: name, category'}), 400

    cover_path = inner_path = None
    dest_dir = os.path.join(current_app.root_path, '..', 'data', 'templates_master')
    clean_name = name.replace(' ', '_').lower()

    for field, comp_type in [('cover', 'cover'), ('inner', 'inner')]:
        f = request.files.get(field)
        if f:
            ext = os.path.splitext(f.filename)[1]
            dest = os.path.join(dest_dir, f"{clean_name}_{comp_type}{ext}")
            f.save(dest)
            rel_path = os.path.join('data', 'templates_master', f"{clean_name}_{comp_type}{ext}")
            if comp_type == 'cover':
                cover_path = rel_path
            else:
                inner_path = rel_path

    if not update_template_complete(template_id, name, category, cover_path, inner_path):
        return jsonify({'error': "Errore durante l'aggiornamento"}), 500

    return jsonify(dict(get_template_by_id(template_id)))


@bp.route('/<int:template_id>', methods=['DELETE'])
def remove_template(template_id):
    if not get_template_by_id(template_id):
        return jsonify({'error': 'Template non trovato'}), 404
    delete_template(template_id)
    return '', 204
