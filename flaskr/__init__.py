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

    masterSecurityBypass = False

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

    @app.route('/health')
    def health():
        msg = "API Reachable - "
        cur = mysql.connection.cursor()
        cur.execute("select id from shelf.user;")
        rv = cur.fetchall()
        if len(rv) > 0:
            msg += "db Working"
        else:
            msg += "ERROR no db return"
        return msg
    
    @app.route('/login', methods = ['PUT'])
    #will need only validate pwd and change last login
    def login():
        #expected body {'displayname':'x','email':'x@x.x','password':'x','last_login':'YYYY-MM-DD HH:MM:SS.XX'} with either displayname or email null
        thisUser = flaskr.models.User()
        thisUser.populateFromRequest(request.data)
        isEmail = thisUser.checkEmailField()
        if isEmail:
            getPasswordQuery = thisUser.createLoginByEmailQuery()
        else:
            getPasswordQuery = thisUser.createLoginByDisplaynameQuery()
        try:
            cur = mysql.connection.cursor()
            cur.execute(getPasswordQuery)
            passIdTuple = cur.fetchall()
            if len(passIdTuple) < 1:
                return Flask.response_class(response="No User Found",status=401)
            if thisUser.checkPassword(passIdTuple):
                thisUser.setId(passIdTuple[0][1])
                cur.execute(thisUser.createLoginUpdate())
                mysql.connection.commit()
                return thisUser.getToken()
            else:
                return Flask.response_class(response="Incorrect Password",status=401)
        except Exception as e:
            return str(e)

    @app.route('/user/<user_id>', methods = ['GET','POST','PUT'])
    #user info includes id display name and privacy pref
    def user(user_id):
        #expected body {'displayname':'x','email':'x@x.x','image':'x','privacy_id':'0','created':'YYYY-MM-DD HH:MM:SS.XX','last_login':'YYYY-MM-DD HH:MM:SS.XX','password':'x'}
        if request.method == 'POST':
            newUser = flaskr.models.User()
            #validation?
            newUser.populateFromRequest(request.data)
            newUser.generateSignature()
            try:
                cur = mysql.connection.cursor()
                cur.execute(newUser.createInsertQuery())
                mysql.connection.commit()
                cur.execute(newUser.createGetAllByEmailQuery())
                rv = cur.fetchall()
                newUser.prepDatabaseReturn(rv)
                return newUser.getToken()
            except Exception as e:
                return str(e)
        elif request.method == 'PUT':
            thisUser = flaskr.models.User()
            thisUser.setId(user_id)
            thisUser.populateFromRequest(request.data)

            
            return "user PUT"
        else:
            thisUser = flaskr.models.User()
            thisUser.setId(user_id)
            cur = mysql.connection.cursor()
            cur.execute(thisUser.createGetAllByIdQuery())
            rv = cur.fetchall()
            thisUser.prepDatabaseReturn(rv)
            return thisUser.getPublicReturn()
        
    @app.route('/search/<resource>/<string>')
    #return search results - list needed resources below (number to return?)  
    def search(resource,string):
        return "searching for " + string + " in " + resource
        #record, alias, blog, users if permis, shelves if public
        

    #Homepage (what is here! shelves/artists/blogs by size and position)
    #using - shelves endpoint with options ('/shelves/<options>/<user_id>')
    #might need additional table for non shelf homepages
    #@app.route('/home/<user_id>', methods = ['GET','POST','PUT'])

    
    @app.route('/shelves/<options>/<user_id>', methods = ['GET','POST','PUT'])
    #to get all shelves of a user and modify 'owned' table determining shelf association
    #needed options definitions - 'all' 'home'  
    def shelves(options,user_id):
        if request.method == 'POST':
            newOwnedShelf = flaskr.models.Owned()
            newOwnedShelf.populateFromRequest(request.data)
            try:
                cur = mysql.connection.cursor()
                cur.execute(newOwnedShelf.createInsertQuery())
                mysql.connection.commit()
                return str(True)
            except Exception as e:
                return str(e)
        elif request.method == 'PUT':
            pass
        else:
            #options could dictate minimal or maximal response
            manyOwned = flaskr.models.Owned()
            cur = mysql.connection.cursor()
            #return manyOwned.createMinimalJoinQuery(flaskr.models.Shelf(),('user_id',True,user_id))
            cur.execute(manyOwned.createJoinQuery(flaskr.models.Shelf(),('user_id',True,user_id)))
            #this may need to be a join to get lite shelf info
            rv = cur.fetchall()
            return manyOwned.manyJoinedDatabaseReturns(rv)
            
 
    @app.route('/shelf/<shelf_id>', methods = ['GET','POST','PUT'])
    #to handle individual shelves in detail  
    def shelf(shelf_id):
        #expected body {'name':'x','creator_id':'x','privacy_id':'x','description':'x'}
        if request.method == 'POST':
            if(masterSecurityBypass or flaskr.helpers.tokenValidation(request,mysql)):
                newShelf = flaskr.models.Shelf()
                newShelf.populateFromRequest(request.data)
                #return newShelf.createInsertQuery()
                try:
                    cur = mysql.connection.cursor()
                    cur.execute(newShelf.createInsertQuery())
                    mysql.connection.commit()
                    return str(True)
                    #TODO create owned for creator here
                except Exception as e:
                    return str(e)
            else:
                return Flask.response_class(response="Unauthorized!",status=401)
        elif request.method == 'PUT':
            dataDict = flaskr.helpers.dictFromRaw(request.data)
            return 'edit shelf id ' + shelf_id + ' new name: ' + dataDict["name"]
        else:
            shelfToGet = flaskr.models.Shelf()
            shelfToGet.setId(shelf_id)
            try:
                cur = mysql.connection.cursor()
                #return shelfToGet.createGetAllByIdQuery()
                cur.execute(shelfToGet.createGetAllByIdQuery())
                rv = cur.fetchall()
                return shelfToGet.prepDatabaseReturn(rv)
                #TODO determine if this is where light record item is incorporated
            except Exception as e:
                return str(e)
        

    @app.route('/shelf_lite/<shelf_id>')
    #minimal return for preview  
    def shelf_lite(shelf_id):
        pass
        #likely need name ims description

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

    



    





    return app