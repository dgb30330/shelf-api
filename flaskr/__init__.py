import os

from flask import Flask

from flask import request

from flask_mysqldb import MySQL
from flask_cors import CORS

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

    cors = CORS(app, resources={r"/*": {"origins": "*"}})

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
    
    @app.route('/test', methods = ['PUT'])
    def test():
        return request.data

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
                return Flask.response_class(response=["No User Found"],status=401)
            if thisUser.checkPassword(passIdTuple):
                thisUser.setId(passIdTuple[0][1])
                #return thisUser.createLoginUpdate()
                cur.execute(thisUser.createLoginUpdate())
                mysql.connection.commit()
                return flaskr.helpers.encode(thisUser.getToken())
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
            return flaskr.helpers.simpleUpdate(user_id,request,mysql,thisUser)
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
    #return search results - list needed resources below (number to return? set by limit property in object)
    #should search strings of multiple words be searched per word?? maybe!  
    def search(resource,string):
        searchObject = None
        if resource == 'record':
            searchObject = flaskr.models.Record()    
        if resource == 'artist':
            searchObject = flaskr.models.Alias()
        if resource == 'shelf':
            searchObject = flaskr.models.Shelf()
        if resource == 'blog':
            searchObject = flaskr.models.Blog()
        try:
            cur = mysql.connection.cursor()
            #return searchObject.createSearchQuery(string)
            cur.execute(searchObject.createSearchQuery(string,otherMinimum=True))
            rawResults = cur.fetchall()
            cur.close()
            return searchObject.manyJoinedDatabaseReturns(rawResults)
        except Exception as e:
            return searchObject.createSearchQuery(string,otherMinimum=True)
        
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
            if options == 'home':
                manyOwned.setCondition((manyOwned.homeKey,True,'1'))
            if options == 'edit':
                manyOwned.setCondition((manyOwned.editKey,True,'1'))
            cur.execute(manyOwned.createJoinQuery(flaskr.models.Shelf(),('user_id',True,user_id)))
            #this may need to be a join to get lite shelf info
            rv = cur.fetchall()
            return manyOwned.manyJoinedDatabaseReturns(rv)
        
    @app.route('/owned/<owned_id>',methods = ['PUT'])
    def owned(owned_id):
        thisShelfOwned = flaskr.models.Owned()
        return flaskr.helpers.simpleUpdate(owned_id,request,mysql,thisShelfOwned)

 
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
                return Flask.response_class(response="Unauthorized!",status=401) #TODO reuse this
        elif request.method == 'PUT':
            thisShelf = flaskr.models.Shelf()
            return flaskr.helpers.simpleUpdate(shelf_id,request,mysql,thisShelf)
        else:
            shelfToGet = flaskr.models.Shelf()
            shelfToGet.setId(shelf_id)
            try:
                cur = mysql.connection.cursor()
                #return shelfToGet.createSelectByIdQuery()
                cur.execute(shelfToGet.createSelectByIdQuery())
                rv = cur.fetchall()
                shelfToGet.prepDatabaseReturn(rv)
                creator = flaskr.models.User()
                creator.setId(shelfToGet.deliverableData[shelfToGet.creator_idKey])
                cur.execute(creator.createSelectByIdQuery(minimal=True))
                creator_rv = cur.fetchall()
                shelfToGet.insertForeignObject(creator.tableName,creator.prepDatabaseReturn(creator_rv,minimal=True))
                return shelfToGet.prepDatabaseReturn(rv)
                #TODO determine if this is where light record item is incorporated
            except Exception as e:
                return str(e)

    @app.route('/shelf/r/u/<record_id>/<user_id>')
    #minimal return for preview  
    def shelf_r_u(record_id,user_id):
        shelvesToGet = flaskr.models.Shelf()
        try:
            cur = mysql.connection.cursor()
            cur.execute(shelvesToGet.createGetByRecordAndUserQuery(record_id,user_id))
            rv = cur.fetchall()
            #return str(rv)
            return shelvesToGet.manyDatabaseReturns(rv)
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
            thisRecord = flaskr.models.Record()
            return flaskr.helpers.simpleUpdate(record_id,request,mysql,thisRecord)
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

    @app.route('/records/<options>/<foreign_id>')
    #to handle individual records in detail  
    def records(options,foreign_id):
        manyRecords = flaskr.models.Record()
        cur = mysql.connection.cursor()
        if options == 'artist':
            cur.execute(manyRecords.createCollabJoinByArtistId(foreign_id))
            rv = cur.fetchall()
            cur.close()
            return manyRecords.manyJoinedDatabaseReturns(rv)
        if options == 'shelf':
            #return manyRecords.createShelvedJoinByShelfId(foreign_id)
            cur.execute(manyRecords.createShelvedJoinByShelfId(foreign_id))
            rv = cur.fetchall()
            cur.close()
            return manyRecords.manyJoinedDatabaseReturns(rv) 
        else:
            return str(False)
        
    @app.route('/shelved/<shelved_id>',methods = ['POST','PUT'])
    def shelved(shelved_id):
        #expected body {'shelf_id':'x','record_id':'x','shelved':'YYYY-MM-DD HH:MM:SS.XX'}
        if request.method == 'POST':
            #TODO check duplication and throw errow
            newShelvedRecord = flaskr.models.Shelved()
            return flaskr.helpers.simpleInsert(request,mysql,newShelvedRecord)
        elif request.method == 'PUT':
            thisShelvedRecord = flaskr.models.Shelved()
            return flaskr.helpers.simpleUpdate(shelved_id,request,mysql,thisShelvedRecord)
        else:
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
            #UGH
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
                aliasData = cur.fetchall()
                aliasId = str(aliasData[0][0])
                newArtist.setPrimaryAlias(aliasId)
                newAlias.setId(aliasId)
                cur.execute(newArtist.createInsertQuery())
                mysql.connection.commit()
                cur.execute(newArtist.createGetIdByPrimaryAlias())
                artistData = cur.fetchall()
                artistId = str(artistData[0][0])
                newAlias.setArtistIdToUpdate(artistId)
                cur.execute(newAlias.createUpdateQuery())
                mysql.connection.commit()
                return str(True)
            except Exception as e:
                    return str(e)
        elif request.method == 'PUT':
            thisArtist = flaskr.models.Artist()
            return flaskr.helpers.simpleUpdate(artist_id,request,mysql,thisArtist)
        else:
            thisArtist = flaskr.models.Artist()
            thisArtist.setId(artist_id)
            cur = mysql.connection.cursor()
            #return thisArtist.createJoinQuery(flaskr.models.Alias(),otherMinimum=True)
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
            thisAlias = flaskr.models.Alias()
            return flaskr.helpers.simpleUpdate(alias_id,request,mysql,thisAlias)
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
            if options == 'home':
                manyFollows.setCondition((manyFollows.homeKey,True,'1'))
            cur.execute(manyFollows.createJoinQuery(flaskr.models.Blog(),('user_id',True,user_id)))
            rv = cur.fetchall()
            #return str(rv)
            return manyFollows.manyJoinedDatabaseReturns(rv)
        
    @app.route('/follow/<follow_id>',methods = ['PUT'])
    def follow(follow_id):
        thisBlogFollow = flaskr.models.Follow()
        return flaskr.helpers.simpleUpdate(follow_id,request,mysql,thisBlogFollow)

    @app.route('/blog/<options>/<blog_id>', methods = ['GET','POST','PUT'])
    #to handle individual blogs in detail  
    def blog(options,blog_id):
        #expected body {'name':'xxx'}
        if request.method == 'POST':
            return flaskr.helpers.simpleInsert(request,mysql,flaskr.models.Blog())
        elif request.method == 'PUT':
            thisBlog = flaskr.models.Blog()
            return flaskr.helpers.simpleUpdate(blog_id,request,mysql,thisBlog)
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
            thisPost = flaskr.models.Post()
            return flaskr.helpers.simpleUpdate(post_id,request,mysql,thisPost)
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
        
        return flaskr.helpers.getRecordHtml(flaskr.helpers.simpleDatabaseGet(record_id,mysql,thisRecord))

    





    return app