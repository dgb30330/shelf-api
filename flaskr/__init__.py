import os

from flask import Flask

from flask import request

from flask_mysqldb import MySQL

import flaskr.helpers
import flaskr.models


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
        cur.execute("select * from shelf.user;")
        rv = cur.fetchall()
        return str(rv)
    
    @app.route('/login', methods = ['POST'])
    #will need only validate pwd and change last login
    def login():
        pass

    @app.route('/search/<resource>/<string>')
    #return search results - list needed resources below (number to return?)  
    def search(resource,string):
        return "searching for " + string + " in " + resource
        #record, alias, blog, users if permis, shelves if public

    @app.route('/user/<user_id>', methods = ['GET','POST','PUT'])
    #user info includes id display name and privacy pref
    def user(user_id):
        if request.method == 'POST':
            return "user post"
        elif request.method == 'PUT':
            return "user PUT"
        else:
            cur = mysql.connection.cursor()
            cur.execute("select * from shelf.user where id = "+user_id+";")
            rv = cur.fetchall()
            return str(rv)
        

    #Homepage (what is here! shelves/artists/blogs by size and position)
    #using - shelves endpoint with options ('/shelves/<options>/<user_id>')
    #might need additional table for non shelf homepages
    #@app.route('/home/<user_id>', methods = ['GET','POST','PUT'])

    
    @app.route('/shelves/<options>/<user_id>', methods = ['GET','POST','PUT'])
    #to get all shelves of a user and modify 'owned' table determining shelf association
    #needed options definitions - 'all' 'home'  
    def shelves(options,user_id):
        pass
 
    @app.route('/shelf/<shelf_id>', methods = ['GET','POST','PUT'])
    #to handle individual shelves in detail  
    def shelf(shelf_id):
        if request.method == 'POST':
            newShelf = flaskr.models.Shelf(True)
            newShelf.populateFromRequest(request.data)
            #return newShelf.createInsertQuery()
            try:
                cur = mysql.connection.cursor()
                cur.execute(newShelf.createInsertQuery())
                mysql.connection.commit()
                return str(True)
                #rv = cur.fetchall()
            except Exception as e:
                return str(e)
        elif request.method == 'PUT':
            dataDict = flaskr.helpers.dictFromRaw(request.data)
            return 'edit shelf id ' + shelf_id + ' new name: ' + dataDict["name"]
        else:
            shelfToGet = flaskr.models.Shelf(False)
            shelfToGet.id = shelf_id
            try:
                cur = mysql.connection.cursor()
                cur.execute(shelfToGet.createGetAllByIdQuery())
                rv = cur.fetchall()
                return shelfToGet.prepDatabaseReturn(rv)
            except Exception as e:
                return str(e)
        

    @app.route('/shelf_lite/<shelf_id>')
    #minimal return for preview  
    def shelf_lite(shelf_id):
        pass

    @app.route('/blogs/<options>/<user_id>', methods = ['GET','POST','PUT'])
    #to get all blogs of a user and modify 'follow' table determining shelf association
    #needed options definitions - 'all' 'home'  
    def blogs(options,user_id):
        pass

    @app.route('/blog/<blog_id>/<post_count>', methods = ['GET','POST','PUT'])
    #to handle individual blogs in detail  
    def blog(blog_id,post_count):
        pass

    @app.route('/blog_lite/<blog_id>')
    #minimal return for preview  
    def blog_lite(blog_id):
        pass

    @app.route('/posts/<options>/<blog_id>/<post_count>')
    #minimal return for preview  
    def posts(options,blog_id,post_count):
        pass

    @app.route('/post', methods = ['GET','POST','PUT'])
    #to handle individual blogs in detail  
    def post():
        pass

    @app.route('/record/<record_id>', methods = ['GET','POST','PUT'])
    #to handle individual records in detail  
    def record(record_id):
        pass

    @app.route('/record_lite/<record_id>')
    #minimal return for preview  
    def record_lite(record_id):
        pass

    @app.route('/links/<record_id>', methods = ['GET','POST','PUT'])
    #to handle streamin links by record  
    def links(record_id):
        pass

    @app.route('/resources/<record_id>', methods = ['GET','POST','PUT'])
    #to handle resource links by record  
    def resources(record_id):
        pass

    @app.route('/artist/<artist_id>', methods = ['GET','POST','PUT'])
    #to handle individual artists in detail  
    def artist(artist_id):
        pass

    @app.route('/artist_lite/<artist_id>')
    #minimal return for preview  
    def artist_lite(artist_id):
        pass



    





    return app