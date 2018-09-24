import os
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'proto.sqlite'),
        ALLOWED_EXTENSIONS=set(['nc']),
        UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #HTTP Error Handlers
    @app.errorhandler(404)
    def file_not_found(e):
        return render_template('404.html')

    @app.errorhandler(500)
    def file_not_found(e):
        return render_template('500.html')

    #Register Blueprints
    from . import views
    app.register_blueprint(views.bp)

    return app