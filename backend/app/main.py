import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import config
from app.extensions import db, migrate, init_redis

load_dotenv()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
        if config_name not in config:
            config_name = "development"

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    init_redis(app)

    # Import models so Alembic can detect them
    from app.models import Host, MetricSnapshot, Alert, AlertRule, AIInsight, MaintenanceTask  # noqa

    from app.api.health import health_bp
    from app.api.hosts import hosts_bp
    from app.api.ingest import ingest_bp
    from app.api.metrics import metrics_bp
    from app.api.alerts import alerts_bp, rules_bp
    from app.api.insights import insights_bp
    from app.api.maintenance import maintenance_bp

    for bp in (health_bp, hosts_bp, ingest_bp, metrics_bp, alerts_bp, rules_bp, insights_bp, maintenance_bp):
        app.register_blueprint(bp)

    @app.errorhandler(400)
    def bad_request(e):
        from flask import jsonify
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        from flask import jsonify
        return jsonify({"error": "Unauthorized", "message": str(e)}), 401

    @app.errorhandler(404)
    def not_found(e):
        from flask import jsonify
        return jsonify({"error": "Not found", "message": str(e)}), 404

    @app.errorhandler(409)
    def conflict(e):
        from flask import jsonify
        return jsonify({"error": "Conflict", "message": str(e)}), 409

    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

    return app
