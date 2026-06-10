import os
import tempfile

from flask import (Blueprint, abort, current_app, redirect,
                   render_template, request, send_file, url_for)

from app.core.database import (
    create_project,
    get_all_projects,
    get_all_templates,
    get_photos_by_project,
    get_project_by_id,
    get_template_components,
    register_complete_template,
)

bp = Blueprint('web', __name__)


@bp.route('/')
def dashboard():
    projects = get_all_projects()
    templates = get_all_templates()
    return render_template('dashboard.html',
                           projects=[dict(p) for p in projects],
                           templates=[dict(t) for t in templates])


@bp.route('/projects/new', methods=['POST'])
def new_project():
    name = request.form.get('project_name', '').strip()
    customer = request.form.get('customer_name', '').strip()
    template_id = request.form.get('template_id') or None
    if not name:
        return redirect(url_for('web.dashboard'))
    project_id = create_project(name, customer or None, template_id)
    return redirect(url_for('web.project_detail', project_id=project_id))


@bp.route('/projects/<int:project_id>')
def project_detail(project_id):
    project = get_project_by_id(project_id)
    if not project:
        abort(404)
    photos = get_photos_by_project(project_id)
    templates = get_all_templates()
    return render_template('project.html',
                           project=dict(project),
                           photos=[dict(p) for p in photos],
                           templates=[dict(t) for t in templates])


@bp.route('/projects/<int:project_id>/layout')
def layout_editor(project_id):
    project = get_project_by_id(project_id)
    if not project:
        abort(404)
    photos = get_photos_by_project(project_id)
    inner_component = None
    if project['template_id']:
        components = get_template_components(project['template_id'])
        inner_component = next(
            (dict(c) for c in components if c['component_type'] == 'inner'), None
        )
    return render_template('layout.html',
                           project=dict(project),
                           photos=[dict(p) for p in photos],
                           inner_component=inner_component)


@bp.route('/templates')
def templates_page():
    templates = get_all_templates()
    result = []
    for t in templates:
        components = get_template_components(t['id'])
        cover = next((dict(c) for c in components if c['component_type'] == 'cover'), None)
        result.append({'template': dict(t), 'cover': cover})
    return render_template('templates_page.html', templates=result)


@bp.route('/templates/new', methods=['POST'])
def new_template():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    cover = request.files.get('cover')
    inner = request.files.get('inner')
    if name and category and cover and inner:
        with tempfile.TemporaryDirectory() as tmp:
            cover_path = os.path.join(tmp, cover.filename)
            inner_path = os.path.join(tmp, inner.filename)
            cover.save(cover_path)
            inner.save(inner_path)
            register_complete_template(name, category, cover_path, inner_path)
    return redirect(url_for('web.templates_page'))


@bp.route('/media/<path:filepath>')
def media(filepath):
    root = os.path.normpath(os.path.join(current_app.root_path, '..'))
    abs_path = os.path.normpath(os.path.join(root, filepath))
    allowed = [
        os.path.join(root, 'data'),
        os.path.join(root, 'app', 'static', 'outputs'),
    ]
    if not any(abs_path.startswith(p) for p in allowed):
        abort(403)
    if not os.path.exists(abs_path):
        abort(404)
    return send_file(abs_path)
