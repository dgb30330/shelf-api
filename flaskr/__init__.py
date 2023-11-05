import os

from flask import Flask

from flask_mysqldb import MySQL


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    app.config['MYSQL_USER'] = "root"
    app.config['MYSQL_PASSWORD'] = "KingDog57!"
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_PORT'] = 3306
    app.config['MYSQL_DATABASE'] = 'shelf'

    mysql = MySQL(app)

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

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        cur = mysql.connection.cursor()
        cur.execute("select * from shelf.users;")
        rv = cur.fetchall()
        return str(rv)

    return app