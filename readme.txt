Python 3.11.5 build

to run test server
-from home dir: .venv\Scripts\activate
-from venv to start: flask --app flaskr run --debug
on new machine
-to set up venv from home dir: py -3 -m venv .venv
-activate as above
-to install from venv: pip install Flask

db library: https://pypi.org/project/Flask-MySQLdb/
install: pip install Flask-MySQLdb

jwt library: https://pyjwt.readthedocs.io/en/stable/
install: pip install pyjwt

flask_cors library: https://flask-cors.readthedocs.io/en/latest/
install: pip install -U flask-cors
(possibly unnecessary in prod)