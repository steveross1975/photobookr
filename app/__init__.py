from flask import Flask
from dotenv import load_dotenv
from app.core.database import init_db

load_dotenv()


def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    init_db()

    from app.routes.templates import bp as templates_bp
    from app.routes.projects import bp as projects_bp
    from app.routes.photos import bp as photos_bp
    app.register_blueprint(templates_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(photos_bp)

    @app.route('/')
    def dashboard():
        return "Dashboard Fotolibro AI: Sistema Pronto."

    return app
