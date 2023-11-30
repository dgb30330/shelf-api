import json
import jwt
import uuid


secret = "whatever"


class ModelData:
    table = 'shelf.required'
    tableName = 'required'

    idKey = 'id'

    primaryForeignKey = None

    requestBodyData: dict = {}
    deliverableData: dict = {}


    allDatabaseKeys = []
    allDatabaseKeysIsNumeric = []
    requiredFields = []
    minimalDatabaseKeys = []

    joinObject = None
    allJoinedKeys = [] #does not need pre-populated

class Model(ModelData):

    def __init__(self) -> None:
        self.deliverableData = dict.fromkeys(self.allDatabaseKeys)


    def setId(self,incomingId):
        self.deliverableData[self.idKey] = incomingId      

    def dictFromRaw(self, responseData: bytes):
        data = responseData.decode('UTF-8')
        data = data.replace("'",'"')
        newDict = json.loads(data)
        return newDict
    
    def populateFromRequest(self,rawBody: bytes):
        self.requestBodyData = self.dictFromRaw(rawBody)
        for key in self.requestBodyData:
            self.deliverableData[key] = self.requestBodyData[key]
    
    def prepDatabaseReturn(self,databaseData: tuple, minimal=False):
        if minimal:
            keysList = self.minimalDatabaseKeys
        else:
            keysList = self.allDatabaseKeys

        if len(databaseData) == 1:
            databaseData = databaseData[0]

        for i in range(len(keysList)):
            self.deliverableData[keysList[i]] = databaseData[i]
        returnableData = self.deliverableData.copy()
        return returnableData
    
    def manyDatabaseReturns(self,databaseData:tuple):
        allDecoded = []
        for innerTuple in databaseData:
            allDecoded.append(self.prepDatabaseReturn(innerTuple))
        return allDecoded

    def prepJoinedDatabaseReturn(self,databaseData: tuple):
        if len(databaseData) == 1:
            databaseData = databaseData[0]
        subKey = None
        for i in range(len(self.allJoinedKeys)):
            if "." in self.allJoinedKeys[i]:
                tableFieldTup = self.allJoinedKeys[i].split(".")
                if subKey == None:
                    subKey = tableFieldTup[0]
                    self.deliverableData[subKey] = {}
                self.deliverableData[tableFieldTup[0]][tableFieldTup[1]] = databaseData[i]
            else:
                self.deliverableData[self.allJoinedKeys[i]] = databaseData[i]
        returnableData = self.deliverableData.copy()
        return returnableData
    
    def manyJoinedDatabaseReturns(self,databaseData:tuple):
        allDecoded = []
        for innerTuple in databaseData:
            allDecoded.append(self.prepJoinedDatabaseReturn(innerTuple))
        return allDecoded

    def decodeWhereConditionFieldNumericboolValueTuple(self,whereConditionFieldNumericboolValueTuple):
        whereCondition = self.tableName + "." + whereConditionFieldNumericboolValueTuple[0] + " = "
        if whereConditionFieldNumericboolValueTuple[1]:
            whereCondition += whereConditionFieldNumericboolValueTuple[2]
        else:
            whereCondition += "'"+whereConditionFieldNumericboolValueTuple[2]+"'"
        return whereCondition


    def createJoinQuery(self,otherTableObject: ModelData, whereConditionFieldNumericboolValueTuple=None, foreignKey = None, thisMinimum = False, otherMinimum = False) -> str:
        #set conditions
        if foreignKey == None:
            foreignKey = self.primaryForeignKey
        relationCondition = self.tableName + "." + foreignKey + " = " + otherTableObject.tableName + "." + otherTableObject.idKey

        self.joinObject = otherTableObject #WATCH might be unneccessary 
        if whereConditionFieldNumericboolValueTuple != None:
            whereCondition = self.decodeWhereConditionFieldNumericboolValueTuple(whereConditionFieldNumericboolValueTuple)
        else:
            whereCondition = self.tableName + "." + self.idKey + " = " + self.deliverableData[self.idKey]
        
        #operational data
        if thisMinimum:
            thisKeysList = self.minimalDatabaseKeys
        else:
            thisKeysList = self.allDatabaseKeys
        if otherMinimum:
            otherKeysList = otherTableObject.minimalDatabaseKeys
        else:
            otherKeysList = otherTableObject.allDatabaseKeys
        self.allJoinedKeys = []

        #set fields to return
        query = "select "
        for field in thisKeysList:
            self.allJoinedKeys.append(field)
            query += self.tableName + "." + field + ", "
        for field in otherKeysList:
            tableField = otherTableObject.tableName + "." + field
            self.allJoinedKeys.append(tableField)
            query +=  tableField + ", "
        
        query = query[0:-2] + " from " + self.table + " INNER JOIN "+ otherTableObject.table +" where " + whereCondition + " AND "+ relationCondition +";"
        return query 
    
    def createSelectByIdQuery(self,minimal=False,whereConditionFieldNumericboolValueTuple=None) -> str:
        query: str = "select "
        if not minimal:
            query += "* "
        else:
            for field in self.minimalDatabaseKeys:
                query += field + ", "
            query = query[0:-2]
        query += " from " + self.table + " where id = " + str(self.deliverableData[self.idKey])
        if whereConditionFieldNumericboolValueTuple != None: 
            query += " AND " + self.decodeWhereConditionFieldNumericboolValueTuple(whereConditionFieldNumericboolValueTuple)
        query += ";"
        return query
    
    def createSelectByConditionQuery(self,whereConditionFieldNumericboolValueTuple=None,minimal=False) -> str:
        query: str = "select "
        if not minimal:
            query += "* "
        else:
            for field in self.minimalDatabaseKeys:
                query += field + ", "
            query = query[0:-2]
        query += " from " + self.table + " where " + self.decodeWhereConditionFieldNumericboolValueTuple(whereConditionFieldNumericboolValueTuple)
        query += ";"
        return query
    
    def createUpdateByIdQuery(self,fieldNumericTupleList) -> str:
        query: str = "UPDATE " + self.table + " SET "
        for fieldTuple in fieldNumericTupleList:
            isNumeric = fieldTuple[1]
            if self.deliverableData[fieldTuple[0]] != None:
                textValue = self.deliverableData[fieldTuple[0]]
            else:
                textValue = 'null'
                isNumeric = True
            query += fieldTuple[0]+"="
            if isNumeric:
                query += textValue+", "
            else:
                query += "'"+textValue+"', "
        query = query[0:-2] + "WHERE " +self.idKey+"="+str(self.deliverableData[self.idKey])
        return query


    def createInsertQuery(self) -> str:
        query: str = "INSERT INTO " + self.table + " ("
        values: str = ""
        for i in range(len(self.allDatabaseKeys)):
            isNumeric = self.allDatabaseKeysIsNumeric[i]
            if self.deliverableData[self.allDatabaseKeys[i]] != None:
                textValue = self.deliverableData[self.allDatabaseKeys[i]]
            else:
                if self.allDatabaseKeys[i] in self.requiredFields:
                    textValue = 'null'
                    isNumeric = True
                else:
                    continue
            query += "`"+self.allDatabaseKeys[i]+"`, "
            if isNumeric:
                values += textValue+", "
            else:
                values += '"'+textValue+'", '
        query = query[0:-2] + ") VALUES (" + values[0:-2] + ");"
        return query
    
    def insertForeignObject(self,keyString,object):
        self.deliverableData[keyString] = object

    def setVoteId(self,voteId):
        self.deliverableData[self.vote_idKey] = voteId

        
        



class User(Model):
    table = "shelf.user"
    tableName = 'user'

    idKey = "id"
    displaynameKey = 'displayname' #varchar45
    emailKey = 'email' #
    imageKey = 'image'
    privacy_idKey = 'privacy_id'
    createdKey = 'created'
    last_loginKey = 'last_login'
    activeKey = 'active'
    passwordKey = 'password'
    signatureKey = 'signature'

    requiredFields = [displaynameKey,emailKey,imageKey,privacy_idKey,createdKey,last_loginKey,passwordKey,signatureKey]
    allDatabaseKeys = [idKey, displaynameKey, emailKey, imageKey, privacy_idKey, createdKey, last_loginKey, activeKey, passwordKey, signatureKey]
    allDatabaseKeysIsNumeric = [True,False,False,False,True,False,False,True,False,False]
    minimalDatabaseKeys = [idKey, displaynameKey, imageKey]

    def __init__(self) -> None:
        super().__init__()
            

    def checkPassword(self,dbPwdRaw) -> bool:
        isValid = False
        #decrypt dbPwd
        storedPassword = dbPwdRaw[0][0]
        #decrypt incoming pwd?

        if self.deliverableData[self.passwordKey] == storedPassword:
            isValid = True
        return isValid
    
    def checkEmailField(self) -> bool:
        isEmail = True
        if self.deliverableData[self.emailKey] == None:
            isEmail = False
        return isEmail
    
    def generateSignature(self):
        payload = {'arbitrary':self.deliverableData[self.last_loginKey]}
        newSignature = jwt.encode(payload, secret, algorithm="HS256")
        self.deliverableData[self.signatureKey] = newSignature
    
    def createLoginByDisplaynameQuery(self) -> str:
        query: str = "select "+self.passwordKey+", "+self.idKey+" from " + self.table + " where "+self.displaynameKey+" = '" + self.deliverableData[self.displaynameKey] + "';"
        return query
    
    def createLoginByEmailQuery(self) -> str:
        query: str = "select "+self.passwordKey+", "+self.idKey+" from " + self.table + " where "+self.emailKey+" = '" + self.deliverableData[self.emailKey] + "';"
        return query
    
    def createGetAllByEmailQuery(self) -> str:
        query: str = "select * from " + self.table + " where "+self.emailKey+" = '" + self.deliverableData[self.emailKey] + "';"
        return query
    
    def createLoginUpdate(self) -> str:
        self.generateSignature()
        loginNeedTupleList = [(self.last_loginKey,False), (self.signatureKey,False)]
        return self.createUpdateByIdQuery(loginNeedTupleList)
    
    def getToken(self):
        payload = {self.idKey:self.deliverableData[self.idKey],self.signatureKey:self.deliverableData[self.signatureKey]}
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token
    
    def getSignature(self):
        return self.deliverableData[self.signatureKey]
    
    def populateFromToken(self,rawToken):
        token = rawToken[7:]
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        for key in payload:
            self.deliverableData[key] = payload[key]

    def getPublicReturn(self):
        dictForReturn = self.deliverableData
        del dictForReturn[self.passwordKey]
        del dictForReturn[self.signatureKey]
        return dictForReturn
    


class Shelf(Model):
    table = "shelf.shelf"
    tableName = 'shelf'

    idKey = 'id'
    nameKey = "name" 
    creator_idKey = "creator_id"
    privacy_idKey = "privacy_id"
    descriptionKey = "description"
    shuffleKey = "shuffle"

    requiredFields = [nameKey,creator_idKey,privacy_idKey,descriptionKey]
    allDatabaseKeys = [idKey,nameKey,creator_idKey,privacy_idKey,descriptionKey,shuffleKey]
    allDatabaseKeysIsNumeric = [True,False,True,True,False,True]
    minimalDatabaseKeys = [idKey, nameKey, descriptionKey]

    def __init__(self) -> None:
        super().__init__()

class Owned(Model):
    table = "shelf.owned"
    tableName = 'owned'

    idKey = "id"
    shelf_idKey = "shelf_id"
    user_idKey = "user_id"
    activeKey = "active"
    addedKey = "added"
    homeKey = "home"
    home_positionKey = "home_position"

    primaryForeignKey = shelf_idKey

    requiredFields = [shelf_idKey,user_idKey,addedKey]
    allDatabaseKeys = [idKey,shelf_idKey,user_idKey,activeKey,addedKey,homeKey,home_positionKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,False,True,True]
    minimalDatabaseKeys = [idKey, user_idKey]
    
    def __init__(self) -> None:
        super().__init__()

class Shelved(Model):
    table = "shelf.shelved"
    tableName = 'shelved'

    idKey = "id"
    shelf_idKey = "shelf_id" 
    record_idKey = "record_id" 
    activeKey = "active" 
    sortKey = "sort" 
    shelvedKey = "shelved" 
    preview_sortKey = "preview_sort"

    requiredFields = [shelf_idKey,record_idKey,shelvedKey]
    allDatabaseKeys = [idKey,shelf_idKey,record_idKey,activeKey,sortKey,shelvedKey,preview_sortKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,True,False,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Record(Model):
    table = "shelf.record"
    tableName = 'record'

    idKey = "id"
    titleKey = "title" 
    alias_idKey = "alias_id" 
    coverKey = "cover" 
    artist_idKey = "artist_id" 
    songKey = "song" 
    parent_record_idKey = "parent_record_id" 
    collaborationKey = "collaboration"

    primaryForeignKey = alias_idKey

    requiredFields = [titleKey,artist_idKey,alias_idKey]
    allDatabaseKeys = [idKey,titleKey,alias_idKey,coverKey,artist_idKey,songKey,parent_record_idKey,collaborationKey]
    allDatabaseKeysIsNumeric = [True,False,True,False,True,True,True,True]
    minimalDatabaseKeys = [idKey, titleKey, coverKey]
    
    def __init__(self) -> None:
        super().__init__()

class Artist(Model):
    table = "shelf.artist"
    tableName = 'artist'

    idKey = "id"
    primary_alias_idKey = "primary_alias_id"
    imageKey = "image"
    shared_nameKey = "shared_name"
    disambiguation_noteKey = "disambiguation_note"

    primaryForeignKey = primary_alias_idKey

    requiredFields = [primary_alias_idKey] #Always create alias first
    allDatabaseKeys = [idKey,primary_alias_idKey,imageKey,shared_nameKey,disambiguation_noteKey]
    allDatabaseKeysIsNumeric = [True,True,False,True,False]
    minimalDatabaseKeys = [idKey, primary_alias_idKey]
    
    def __init__(self) -> None:
        super().__init__()

    def setPrimaryAlias(self,alias_id: str):
        self.deliverableData[self.primary_alias_idKey] = alias_id

class Alias(Model):
    table = "shelf.alias"
    tableName = 'alias'

    idKey = "id"
    nameKey = "name" 
    artist_idKey = "artist_id" 
    vote_idKey = "vote_id"

    primaryForeignKey = vote_idKey

    requiredFields = [nameKey,artist_idKey,vote_idKey] #for new artists use id 1 then change after insert
    allDatabaseKeys = [idKey,nameKey,artist_idKey,vote_idKey]
    allDatabaseKeysIsNumeric = [True,False,True,False]
    minimalDatabaseKeys = [idKey, nameKey]
    
    def __init__(self) -> None:
        super().__init__()

    def setNewArtistHold(self):
        self.deliverableData[self.artist_idKey] = '1'

    def createGetIdByNameVoteQuery(self) -> str:
        query: str = "select "+self.idKey+" from " + self.table + " where "+self.nameKey+" = '" + self.deliverableData[self.nameKey] + "' AND "+self.vote_idKey+" = '" + self.deliverableData[self.vote_idKey] + "';"
        return query



class Collaboration(Model):
    table = "shelf.collaboration"
    tableName = 'collaboration'

    idKey = "id"
    record_idKey = "record_id"
    artist_idKey = "artist_id"

    primaryForeignKey = artist_idKey

    #Found from Record ID, used to populate additional artist links
    requiredFields = [record_idKey,artist_idKey]
    allDatabaseKeys = [idKey,record_idKey,artist_idKey]
    allDatabaseKeysIsNumeric = [True,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Connection(Model):
    table = "shelf.connection"
    tableName = 'connection'

    idKey = "id"
    artist_idKey = "artist_id" 
    connected_artist_idKey = "connected_artist_id" 
    nature_codeKey = "nature_code"  
    vote_idKey = "vote_id" 

    primaryForeignKey = connected_artist_idKey

    requiredFields = [artist_idKey,connected_artist_idKey,nature_codeKey]
    allDatabaseKeys = [idKey,artist_idKey,connected_artist_idKey,nature_codeKey,vote_idKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,False]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Vote(Model):
    table = "shelf.vote"
    tableName = 'vote'

    idKey = "id"
    up_countKey = "up_count"
    down_countKey = "down_count"

    requiredFields = [idKey]
    allDatabaseKeys = [idKey,up_countKey,down_countKey]
    allDatabaseKeysIsNumeric = [False,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

    def generateId(self):
        self.deliverableData[self.idKey] = str(uuid.uuid4())
        return self.deliverableData[self.idKey]
    
class Ballot(Model):
    table = "shelf.ballot"
    tableName = 'ballot'
    
    idKey = "id"
    vote_idKey = "vote_id"
    user_idKey = "user_id" 
    upKey = "up"

    requiredFields = [vote_idKey,user_idKey]
    allDatabaseKeys = [idKey,vote_idKey,user_idKey,upKey]
    allDatabaseKeysIsNumeric = [True,False,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()
    

class Blog(Model):
    table = "shelf.blog"
    tableName = 'blog'

    idKey = "id"
    nameKey = "name" 
    activeKey = "active"
    record_idKey = "record_id" 
    user_idKey = "user_id"
    artist_idKey = "artist_id"
    standaloneKey = "standalone" 
    privacy_idKey = "privacy_id"
    imageKey = "image"

    requiredFields = [nameKey]
    allDatabaseKeys = [idKey,nameKey,activeKey,record_idKey,user_idKey,artist_idKey,standaloneKey,privacy_idKey,imageKey]
    allDatabaseKeysIsNumeric = [True,False,True,True,True,True,True,True,False]
    minimalDatabaseKeys = [idKey,nameKey]
    
    def __init__(self) -> None:
        super().__init__()

class Admin(Model):
    table = "shelf.admin"
    tableName = 'admin'

    idKey = "id"
    user_idKey = "id" 
    blog_idKey = "id" 
    ownerKey = "id" 
    permission_codeKey = "id"

    requiredFields = [user_idKey,blog_idKey,permission_codeKey]
    allDatabaseKeys = [idKey,user_idKey,blog_idKey,ownerKey,permission_codeKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

    
class Post(Model):
    table = "shelf.post"
    tableName = 'post'

    idKey = "id"
    user_idKey = "user_id" 
    blog_idKey = "blog_id" 
    textKey = "text" 
    link_urlKey = "link_url"
    img_urlKey = "img_url" 
    postedKey = "posted" 
    activeKey = "active" 
    vote_idKey = "vote_id" 
    privacy_idKey = "privacy_id" 
    flag_codeKey = "flag_code" 
    embed_codeKey = "embed_code"

    primaryForeignKey = user_idKey

    requiredFields = [user_idKey,blog_idKey,textKey,postedKey,vote_idKey,]
    allDatabaseKeys = [idKey,user_idKey,blog_idKey,textKey,link_urlKey,img_urlKey,postedKey,activeKey,vote_idKey,privacy_idKey,flag_codeKey,embed_codeKey]
    allDatabaseKeysIsNumeric = [True,True,True,False,False,False,False,True,False,True,True,False]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()


    
class Follow(Model):
    table = "shelf.follow"
    tableName = 'follow'

    idKey = "id"
    blog_idKey = "blog_id" 
    user_idKey = "user_id" 
    activeKey = "active" 
    homeKey = "home" 
    home_positionKey = "home_position"

    primaryForeignKey = blog_idKey

    requiredFields = [blog_idKey,user_idKey]
    allDatabaseKeys = [idKey,blog_idKey,user_idKey,activeKey,homeKey,home_positionKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Link(Model):
    table = "shelf.link"
    tableName = 'link'

    idKey = "id"
    urlKey = "url"
    record_idKey = "record_id"
    vote_idKey = "vote_id"
    platform_idKey = "platform_id"

    primaryForeignKey = vote_idKey

    requiredFields = [urlKey,record_idKey,platform_idKey,vote_idKey]
    allDatabaseKeys = [idKey,urlKey,record_idKey,vote_idKey,platform_idKey]
    allDatabaseKeysIsNumeric = [True,False,True,False,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Platform(Model):
    table = "shelf.platform"
    tableName = 'platform'

    idKey = "id"
    nameKey = "name"

    requiredFields = [nameKey]
    allDatabaseKeys = [idKey,nameKey]
    allDatabaseKeysIsNumeric = [True,False]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Resource(Model):
    table = "shelf.resource"
    tableName = 'resource'

    idKey = "id"
    urlKey = "url" 
    record_idKey = "record_id" 
    variety_codeKey = "variety_code"  
    vote_idKey = "vote_id" 
    
    primaryForeignKey = vote_idKey

    requiredFields = [urlKey,record_idKey,variety_codeKey,vote_idKey,]
    allDatabaseKeys = [idKey,urlKey,record_idKey,variety_codeKey,vote_idKey]
    allDatabaseKeysIsNumeric = [True,False,True,True,False]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Tag(Model):
    table = "shelf.tag"
    tableName = 'tag'

    idKey = "id"
    record_idKey = "record_id" 
    user_idKey = "user_id" 
    flavor_idKey = "flavor_id" 
    activeKey = "active"

    primaryForeignKey = flavor_idKey

    requiredFields = [record_idKey,user_idKey,flavor_idKey]
    allDatabaseKeys = [idKey,record_idKey,user_idKey,flavor_idKey,activeKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()

class Flavor(Model):
    table = "shelf.flavor"
    tableName = 'flavor'

    idKey = "id"
    tagKey = "tag"
    activeKey = "active"

    requiredFields = [tagKey]
    allDatabaseKeys = [idKey,tagKey,activeKey]
    allDatabaseKeysIsNumeric = [True,False,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()


class Suggestion(Model):
    table = "shelf.suggestion"
    tableName = 'suggestion'

    idKey = "id"
    user_idKey = "user_id" 
    resource_codeKey = "resource_code" 
    textKey = "text" 
    addressedKey = "addressed" 
    validKey = "valid"

    requiredFields = [user_idKey,resource_codeKey,textKey]
    allDatabaseKeys = [idKey,user_idKey,resource_codeKey,textKey,addressedKey,validKey]
    allDatabaseKeysIsNumeric = [True,True,False,False,True,True]
    minimalDatabaseKeys = []
    
    def __init__(self) -> None:
        super().__init__()



