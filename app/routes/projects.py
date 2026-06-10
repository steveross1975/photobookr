from flask import Blueprint, jsonify, request

from app.core.database import (
    create_project,
    delete_project,
    get_all_projects,
    get_project_by_id,
    get_template_by_id,
    update_project,
)

bp = Blueprint('projects', __name__, url_prefix='/api/projects')

VALID_STATUSES = {'draft', 'processing', 'completed'}


@bp.route('', methods=['GET'])
def list_projects():
    projects = get_all_projects()
    return jsonify([dict(p) for p in projects])


@bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = get_project_by_id(project_id)
    if not project:
        return jsonify({'error': 'Progetto non trovato'}), 404
    return jsonify(dict(project))


@bp.route('', methods=['POST'])
def create():
    data = request.get_json(silent=True) or {}
    project_name = data.get('project_name')
    if not project_name:
        return jsonify({'error': 'Campo richiesto: project_name'}), 400

    template_id = data.get('template_id')
    if template_id and not get_template_by_id(template_id):
        return jsonify({'error': 'Template non trovato'}), 404

    project_id = create_project(
        project_name=project_name,
        customer_name=data.get('customer_name'),
        template_id=template_id,
    )
    if not project_id:
        return jsonify({'error': 'Errore durante la creazione del progetto'}), 500

    return jsonify(dict(get_project_by_id(project_id))), 201


@bp.route('/<int:project_id>', methods=['PUT'])
def update(project_id):
    project = get_project_by_id(project_id)
    if not project:
        return jsonify({'error': 'Progetto non trovato'}), 404

    data = request.get_json(silent=True) or {}
    project_name = data.get('project_name', project['project_name'])

    status = data.get('status', project['status'])
    if status not in VALID_STATUSES:
        return jsonify({'error': f"Status non valido. Valori ammessi: {', '.join(VALID_STATUSES)}"}), 400

    template_id = data.get('template_id', project['template_id'])
    if template_id and not get_template_by_id(template_id):
        return jsonify({'error': 'Template non trovato'}), 404

    if not update_project(
        project_id=project_id,
        project_name=project_name,
        customer_name=data.get('customer_name', project['customer_name']),
        template_id=template_id,
        status=status,
    ):
        return jsonify({'error': "Errore durante l'aggiornamento"}), 500

    return jsonify(dict(get_project_by_id(project_id)))


@bp.route('/<int:project_id>', methods=['DELETE'])
def remove(project_id):
    if not get_project_by_id(project_id):
        return jsonify({'error': 'Progetto non trovato'}), 404
    delete_project(project_id)
    return '', 204
