import os

from flask import Blueprint, current_app, jsonify

from app.core.database import (
    get_photos_by_project,
    get_project_by_id,
    get_template_components,
    set_project_output,
)
from app.core.exporter import export_project_pdf

bp = Blueprint('export', __name__)


@bp.route('/api/projects/<int:project_id>/export', methods=['POST'])
def export_pdf(project_id):
    project = get_project_by_id(project_id)
    if not project:
        return jsonify({'error': 'Progetto non trovato'}), 404

    photos = get_photos_by_project(project_id)
    if not photos:
        return jsonify({'error': 'Nessuna foto nel progetto'}), 400

    components = []
    if project['template_id']:
        components = get_template_components(project['template_id'])

    root = os.path.normpath(os.path.join(current_app.root_path, '..'))
    safe_name = project['project_name'].replace(' ', '_')
    output_dir = os.path.join(root, 'app', 'static', 'outputs', str(project_id))
    output_path = os.path.join(output_dir, f"{safe_name}.pdf")

    total_pages = export_project_pdf(project, photos, components, output_path, root)

    rel_output = os.path.join('app', 'static', 'outputs', str(project_id))
    set_project_output(project_id, rel_output, total_pages)

    return jsonify({
        'pdf_path': os.path.relpath(output_path, root),
        'total_pages': total_pages,
    })
