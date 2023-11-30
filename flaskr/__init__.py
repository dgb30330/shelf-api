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

    masterSecurityBypass = True #for token needs - True for free dev mode

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
            #return thisUser.createSelectByIdQuery(minimal=True)
            cur.execute(thisUser.createSelectByIdQuery())
            rv = cur.fetchall()
            #return str(rv)
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
        #expected body {'shelf_id':'x','user_id':'x','added':'YYYY-MM-DD HH:MM:SS.XX'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Owned())
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
                    cur.close()
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
                #return shelfToGet.createSelectByIdQuery()
                cur.execute(shelfToGet.createSelectByIdQuery())
                rv = cur.fetchall()
                return shelfToGet.prepDatabaseReturn(rv)
                #TODO determine if this is where light record item is incorporated
            except Exception as e:
                return str(e)
        

    @app.route('/shelf_lite/<shelf_id>')
    #minimal return for preview  
    def shelf_lite(shelf_id):
        shelfToGet = flaskr.models.Shelf()
        shelfToGet.setId(shelf_id)
        try:
            cur = mysql.connection.cursor()
            cur.execute(shelfToGet.createSelectByIdQuery(minimal=True))
            rv = cur.fetchall()
            return shelfToGet.prepDatabaseReturn(rv,minimal=True)
        except Exception as e:
            return str(e)

    @app.route('/record/<record_id>', methods = ['GET','POST','PUT'])
    #to handle individual records in detail  
    def record(record_id):
        #expected body {'title':'xxx','artist_id':'x','alias_id':'x'}
        if request.method == 'POST':
            #if artist/alias is new, must be called before this operation
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Record())

        elif request.method == 'PUT':
            pass
        else:
            thisRecord = flaskr.models.Record()
            thisRecord.setId(record_id)
            cur = mysql.connection.cursor()
            cur.execute(thisRecord.createJoinQuery(flaskr.models.Alias(),otherMinimum=True))
            #TODO if parent_record_id is not null - retrieve and return parent - correct?
            rv = cur.fetchall()
            thisRecord.prepJoinedDatabaseReturn(rv)
            links = flaskr.models.Link()
            cur.execute(links.createSelectByConditionQuery((links.record_idKey,True,record_id)))
            links_rv = cur.fetchall()
            thisRecord.insertForeignObject(links.tableName,links.manyDatabaseReturns(links_rv))
            resources = flaskr.models.Resource()
            cur.execute(resources.createSelectByConditionQuery((resources.record_idKey,True,record_id)))
            resources_rv = cur.fetchall()
            thisRecord.insertForeignObject(resources.tableName,resources.manyDatabaseReturns(resources_rv))
            return thisRecord.prepJoinedDatabaseReturn(rv)


    @app.route('/record_lite/<record_id>')
    #minimal return for preview  
    def record_lite(record_id):
        pass

    @app.route('/link/<record_id>', methods = ['GET','POST','PUT'])
    #to handle streamin links by record  
    def link(record_id):
        #expected body {'url':'xxx','record_id':'x','platform_id':'x'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Link(),insertVote=True)
        elif request.method == 'PUT':
            pass
        else:
            pass

    @app.route('/resource/<record_id>', methods = ['GET','POST','PUT'])
    #to handle resource links by record  
    def resource(record_id):
        #expected body {'url':'xxx','record_id':'x','variety_code':'x'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Resource(),insertVote=True)
        elif request.method == 'PUT':
            pass
        else:
            pass

    @app.route('/artist/<artist_id>', methods = ['GET','POST','PUT'])
    #to handle individual artists in detail  
    def artist(artist_id):
        if request.method == 'POST':
            #how do handle ALIAS on create?
            newArtist = flaskr.models.Artist()
            newAlias = flaskr.models.Alias()
            newAlias.populateFromRequest(request.data)
            newAlias.setNewArtistHold()
            newVote = flaskr.models.Vote()
            newAlias.setVoteId(newVote.generateId())
            try:
                cur = mysql.connection.cursor()
                cur.execute(newVote.createInsertQuery())
                cur.execute(newAlias.createInsertQuery())
                mysql.connection.commit()
                cur.execute(newAlias.createGetIdByNameVoteQuery())
                rv = cur.fetchall()
                newArtist.setPrimaryAlias(str(rv[0][0]))
                cur.execute(newArtist.createInsertQuery())
                mysql.connection.commit()
                return str(True)
            except Exception as e:
                    return str(e)

        elif request.method == 'PUT':
            pass
        else:
            thisArtist = flaskr.models.Artist()
            thisArtist.setId(artist_id)
            cur = mysql.connection.cursor()
            cur.execute(thisArtist.createJoinQuery(flaskr.models.Alias(),otherMinimum=True))
            rv = cur.fetchall()
            return thisArtist.prepJoinedDatabaseReturn(rv)

    @app.route('/artist_lite/<artist_id>')
    #minimal return for preview  
    def artist_lite(artist_id):
        pass

    @app.route('/alias/<alias_id>', methods = ['GET','POST','PUT'])
    #to get all blogs of a user and modify 'follow' table determining shelf association
    #needed options definitions - 'all' 'home'  
    def alias(alias_id):
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Alias(),insertVote=True)
        elif request.method == 'PUT':
            pass
        else:
            aliasToGet = flaskr.models.Alias()
            aliasToGet.setId(alias_id)
            try:
                cur = mysql.connection.cursor()
                cur.execute(aliasToGet.createSelectByIdQuery())
                rv = cur.fetchall()
                return aliasToGet.prepDatabaseReturn(rv)
            except Exception as e:
                return str(e)

    @app.route('/blogs/<options>/<user_id>', methods = ['GET','POST','PUT'])
    #to get all blogs of a user and modify 'follow' table determining shelf association
    #needed options definitions - 'all' 'home'  
    def blogs(options,user_id):
        #expected body {'blog_id':'x','user_id':'x'}
        if request.method == 'POST':
            newBlogFollow = flaskr.models.Follow()
            return flaskr.helpers.simpleInsert(request,mysql,newBlogFollow)
        elif request.method == 'PUT':
            pass
        else:
            #options could dictate minimal or maximal response
            manyFollows = flaskr.models.Follow()
            cur = mysql.connection.cursor()
            #return manyFollows.createJoinQuery(flaskr.models.Blog(),('user_id',True,user_id))
            cur.execute(manyFollows.createJoinQuery(flaskr.models.Blog(),('user_id',True,user_id)))
            rv = cur.fetchall()
            #return str(rv)
            return manyFollows.manyJoinedDatabaseReturns(rv)

    @app.route('/blog/<options>/<blog_id>', methods = ['GET','POST','PUT'])
    #to handle individual blogs in detail  
    def blog(options,blog_id):
        #expected body {'name':'xxx'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Blog())
        elif request.method == 'PUT':
            pass
        else:
            thisBlog = flaskr.models.Blog()
            thisBlog.setId(blog_id)
            cur = mysql.connection.cursor()
            cur.execute(thisBlog.createSelectByIdQuery())
            rv = cur.fetchall()
            return thisBlog.prepDatabaseReturn(rv)

    @app.route('/blog_lite/<blog_id>')
    #minimal return for preview  
    def blog_lite(blog_id):
        thisBlog = flaskr.models.Blog()
        thisBlog.setId(blog_id)
        cur = mysql.connection.cursor()
        cur.execute(thisBlog.createSelectByIdQuery())
        rv = cur.fetchall()
        return thisBlog.prepDatabaseReturn(rv,minimal=True)

    @app.route('/posts/<options>/<blog_id>')
    #minimal return for preview  
    def posts(options,blog_id):
        manyPosts = flaskr.models.Post()
        cur = mysql.connection.cursor()
        cur.execute(manyPosts.createJoinQuery(flaskr.models.User(),('blog_id',True,blog_id),otherMinimum=True))
        rv = cur.fetchall()
        return manyPosts.manyJoinedDatabaseReturns(rv)

    @app.route('/post/<post_id>', methods = ['GET','POST','PUT'])
    #to handle individual blogs in detail  
    def post(post_id):
        #expected body {'user_id':'x','blog_id':'x','text':'xxx','posted':'YYYY-MM-DD HH:MM:SS.XX','vote_id':'xxx'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Post(),insertVote=True)
        elif request.method == 'PUT':
            pass
        else:
            thisPost = flaskr.models.Post()
            thisPost.setId(post_id)
            cur = mysql.connection.cursor()
            cur.execute(thisPost.createJoinQuery(flaskr.models.User(),otherMinimum=True))
            rv = cur.fetchall()
            return thisPost.prepJoinedDatabaseReturn(rv)
        
    @app.route('/ssr/<record_id>')
    #minimal return for preview  
    def ssr(record_id):
        thisRecord = flaskr.models.Record()
        thisRecord.prepDatabaseReturn(flaskr.helpers.simpleDatabaseGet(record_id,mysql,thisRecord))
        return flaskr.helpers.getRecordHtml(thisRecord)

    





    return app