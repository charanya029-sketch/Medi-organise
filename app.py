import os
from flask import Flask, render_template
from config import Config
from models import db
from routes import main_bp, patients_bp, reports_bp, api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "preprocessed"), exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Template filters for status and provenance styling
    @app.template_filter("status_badge")
    def status_badge(status):
        s = (status or "").upper()
        if s == "LOW":
            return "badge-status badge-low"
        elif s == "NORMAL":
            return "badge-status badge-normal"
        elif s == "HIGH":
            return "badge-status badge-high"
        elif "VERIF" in s:
            return "badge-status badge-verify"
        else:
            return "badge-status badge-neutral"

    @app.template_filter("source_badge")
    def source_badge(source):
        src = (source or "").upper()
        if "USER_CORRECTED" in src:
            return "badge-provenance badge-user-corrected"
        elif "USER_VERIFIED" in src:
            return "badge-provenance badge-user-verified"
        elif "USER_PROVIDED" in src:
            return "badge-provenance badge-user"
        elif "EXTRACTED" in src or "REPORT" in src:
            return "badge-provenance badge-extracted"
        elif "AI" in src or "GENERATED" in src:
            return "badge-provenance badge-ai"
        return "badge-provenance badge-neutral"

    # Friendly error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("base.html", custom_error="The requested resource or page was not found."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("base.html", custom_error="An unexpected internal error occurred. Your medical records remain safely preserved."), 500

    @app.errorhandler(413)
    def file_too_large(error):
        return render_template("base.html", custom_error="The uploaded file exceeds the 16MB file size limit. Please upload a smaller document."), 413

    with app.app_context():
        db.create_all()

    return app
    app = create_app()

if __name__ == "__main__":
   
    app.run(host="127.0.0.1", port=5000, debug=True)
