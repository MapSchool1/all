from flask import Flask, jsonify, request
from sqlalchemy import inspect, text

from config import config
from app.extensions import db, migrate, jwt, cors, limiter


def create_app(config_name='desarrollo'):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']},
                                  r'/auth/*': {'origins': app.config['CORS_ORIGINS']}},
                  supports_credentials=True)
    limiter.init_app(app)

    from app import models  # noqa: F401  — registra modelos con SQLAlchemy

    _register_jwt_callbacks(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_health(app)
    _register_template_helpers(app)

    return app


def _register_health(app):
    from flask import send_from_directory
    import os

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'img'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/health')
    def health():
        db_ok = True
        try:
            db.session.execute(text('SELECT 1'))
        except Exception:
            db_ok = False
        return jsonify({
            'status': 'ok' if db_ok else 'degraded',
            'db': 'ok' if db_ok else 'error',
            'version': app.config.get('APP_VERSION', '0.0.0'),
        })


def _register_blueprints(app):
    from app.api.auth import bp as auth_bp
    from app.api.users import bp as users_bp
    from app.api.academic import bp as academic_bp
    from app.api.campus import bp as campus_bp
    from app.api.horarios import bp as horarios_bp
    from app.api.inscripciones import bp as inscripciones_bp
    from app.api.tramites import bp as tramites_bp
    from app.api.notifications import bp as notifications_bp
    from app.api.stats import bp as stats_bp
    from app.api.mapa import bp as mapa_bp
    from app.api.search import bp as search_bp
    from app.api.audit import bp as audit_bp
    from app.api.anuncios import bp as anuncios_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(academic_bp, url_prefix='/api/v1')
    app.register_blueprint(campus_bp, url_prefix='/api/v1')
    app.register_blueprint(horarios_bp, url_prefix='/api/v1/horarios')
    app.register_blueprint(inscripciones_bp, url_prefix='/api/v1/inscripciones')
    app.register_blueprint(tramites_bp, url_prefix='/api/v1/tramites')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notificaciones')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')
    app.register_blueprint(mapa_bp, url_prefix='/api/v1/mapa')
    app.register_blueprint(search_bp, url_prefix='/api/v1/buscar')
    app.register_blueprint(audit_bp, url_prefix='/api/v1/audit')
    app.register_blueprint(anuncios_bp, url_prefix='/api/v1/anuncios')

    from app.web.public import bp as web_public_bp
    from app.web.auth_views import bp as web_auth_bp
    from app.web.student import bp as web_student_bp
    from app.web.admin_views import bp as web_admin_bp
    from app.web.profesor_views import bp as web_profesor_bp
    from app.web.components import bp as web_components_bp

    app.register_blueprint(web_public_bp)
    app.register_blueprint(web_auth_bp, url_prefix='/auth')
    app.register_blueprint(web_student_bp)
    app.register_blueprint(web_admin_bp, url_prefix='/admin')
    app.register_blueprint(web_profesor_bp, url_prefix='/profesor')
    if app.debug:
        app.register_blueprint(web_components_bp, url_prefix='/components')


def _register_jwt_callbacks(app):
    from app.models import RefreshToken, User

    @jwt.token_in_blocklist_loader
    def check_blocklist(_jwt_header, jwt_payload):
        if jwt_payload.get('type') != 'refresh':
            return False
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        token = RefreshToken.query.filter_by(token_jti=jti).first()
        return token is None or token.revoked

    @jwt.user_lookup_loader
    def user_loader(_jwt_header, jwt_payload):
        identity = jwt_payload.get('sub')
        try:
            uid = int(identity)
        except (TypeError, ValueError):
            return None
        return User.query.get(uid)

    @jwt.unauthorized_loader
    def unauth(reason):
        return jsonify({'error': 'No autenticado', 'code': 'UNAUTHORIZED',
                        'detalle': reason}), 401

    @jwt.invalid_token_loader
    def invalid(reason):
        return jsonify({'error': 'Token inválido', 'code': 'INVALID_TOKEN',
                        'detalle': reason}), 401

    @jwt.expired_token_loader
    def expired(_h, _p):
        return jsonify({'error': 'Token expirado', 'code': 'TOKEN_EXPIRED'}), 401

    @jwt.revoked_token_loader
    def revoked(_h, _p):
        return jsonify({'error': 'Token revocado', 'code': 'TOKEN_REVOKED'}), 401


def _register_error_handlers(app):
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({'error': 'Recurso no encontrado',
                            'code': 'NOT_FOUND'}), 404
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(_e):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({'error': 'Permiso denegado',
                            'code': 'FORBIDDEN'}), 403
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(HTTPException)
    def http_exc(e):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({'error': e.description,
                            'code': e.name.upper().replace(' ', '_')}), e.code
        return e

    @app.errorhandler(Exception)
    def server_error(e):
        db.session.rollback()
        app.logger.exception('Error no manejado: %s', e)
        if app.debug:
            raise e
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({'error': 'Error interno del servidor',
                            'code': 'INTERNAL_ERROR'}), 500
        from flask import render_template
        return render_template('errors/500.html'), 500


def _register_security_headers(app):
    @app.after_request
    def headers(resp):
        resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
        resp.headers.setdefault('X-Frame-Options', 'DENY')
        resp.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return resp


def _register_template_helpers(app):
    from flask import session
    from app.models import User

    @app.context_processor
    def inject_globals():
        user = None
        uid = session.get('user_id')
        if uid:
            user = User.query.get(uid)
            if user and user.is_deleted:
                user = None
        return {
            'app_name': 'Matute Guide',
            'app_version': app.config.get('APP_VERSION'),
            'current_user': user,
        }
