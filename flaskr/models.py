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
    toUpdate = [] #does not need pre-populated
    queryConditions = [] #does not need pre-populated

class Model(ModelData):

    def __init__(self) -> None:
        self.deliverableData = dict.fromkeys(self.allDatabaseKeys)


    def setId(self,incomingId):
        self.deliverableData[self.idKey] = str(incomingId)     

    def dictFromRaw(self, responseData: bytes):
        data = responseData.decode('UTF-8')
        data = data.replace("'",'"')
        newDict = json.loads(data)
        return newDict
    
    def populateFromRequest(self,rawBody: bytes,forUpdate=False):
        if forUpdate:
            self.toUpdate = []
        self.requestBodyData = self.dictFromRaw(rawBody)
        for key in self.requestBodyData:
            self.deliverableData[key] = self.requestBodyData[key]
            if forUpdate:
                self.toUpdate.append(key)
    
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
    
    def setCondition(self,whereConditionFieldNumericboolValueTuple):
        self.queryConditions.append(whereConditionFieldNumericboolValueTuple)

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
        
        query = query[0:-2] + " from " + self.table + " INNER JOIN "+ otherTableObject.table +" where " + whereCondition + " AND "+ relationCondition 
        if len(self.queryConditions)>0:
            for conditionTuple in self.queryConditions:
                query = query + " AND " + self.decodeWhereConditionFieldNumericboolValueTuple(conditionTuple)    
        query += ";"
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
    
    def createUpdateQuery(self) -> str:
        ## !!! request body MUST match db fields - Id must be set
        query: str = "UPDATE " + self.table + " SET "
        for i in range(len(self.allDatabaseKeys)):
            if self.allDatabaseKeys[i] in self.toUpdate:
                isNumeric = self.allDatabaseKeysIsNumeric[i]
                query += self.allDatabaseKeys[i] + "="
                if isNumeric:
                    query += self.deliverableData[self.allDatabaseKeys[i]]+", "
                else:
                    query += "'"+self.deliverableData[self.allDatabaseKeys[i]]+"', " 
        query = query[0:-2] + " WHERE " +self.idKey+"="+str(self.deliverableData[self.idKey])
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

class Searchable(Model):
    searchFields = []
    searchJoin: ModelData = None
    searchJoinField = None
    searchForeignKey = None
    searchLimit = 20
    searchSort = None
    searchActiveOnly = True

    def createSearchQuery(self, searchString, thisMinimum = False, otherMinimum = False) -> str:
        #set conditions
        if self.searchJoin != None:
            otherTableObject: ModelData = self.searchJoin
            foreignKey = self.searchForeignKey
            relationCondition = self.tableName + "." + foreignKey + " = " + otherTableObject.tableName + "." + otherTableObject.idKey
            
        #operational data
        if thisMinimum:
            thisKeysList = self.minimalDatabaseKeys
        else:
            thisKeysList = self.allDatabaseKeys
        if self.searchJoin != None:
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
        if self.searchJoin != None:
            for field in otherKeysList:
                tableField = otherTableObject.tableName + "." + field
                self.allJoinedKeys.append(tableField)
                query +=  tableField + ", "
        
        query = query[0:-2] + " from " + self.table
        if self.searchJoin != None:
            query += " INNER JOIN "+ otherTableObject.table 
        query += " WHERE " 
        if self.searchJoin != None:
            query += relationCondition + " AND "
        query += "("
        parentheticalFirst = True
        for field in self.searchFields:
            if not parentheticalFirst:
                query+= " OR "
            parentheticalFirst = False
            query+= self.tableName + "." +field + " LIKE '%"+ searchString +"%'"
        if self.searchJoinField != None:
            query+= " OR " + self.searchJoin.tableName + "." + self.searchJoinField + " LIKE '%"+ searchString +"%'"
        query += ")"
        if len(self.queryConditions)>0:
            for conditionTuple in self.queryConditions:
                query = query + " AND " + self.decodeWhereConditionFieldNumericboolValueTuple(conditionTuple)   
        if self.searchActiveOnly:
            query+= " AND active = 1"
        if self.searchSort != None:
            query += " ORDER BY " + self.tableName + "." + self.searchSort  
        query += " LIMIT "+str(self.searchLimit)
        query += ";"
        return query
    
    def __init__(self) -> None:
        super().__init__()




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
        self.toUpdate.append(self.last_loginKey)
        self.toUpdate.append(self.signatureKey)
        #loginNeedTupleList = [(self.last_loginKey,False), (self.signatureKey,False)]
        return self.createUpdateQuery()
    
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
    
    


class Shelf(Searchable):
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
    queryConditions = []

    searchFields = [nameKey,descriptionKey]
    searchJoin: ModelData = User()
    searchJoinField = searchJoin.displaynameKey
    searchForeignKey = creator_idKey
    searchLimit = 20
    searchSort = nameKey
    searchActiveOnly = False

    def __init__(self) -> None:
        super().__init__()

    def createGetByRecordAndUserQuery(self,record_id,user_id):
        ownedModel = Owned()
        shelvedModel = Shelved()
        query = "select " 
        for key in self.allDatabaseKeys:
            query += self.tableName + "." + key + ", "
        query = query[0:-2]
        query += " from " + self.table
        query += " INNER JOIN " + ownedModel.table + " ON " +self.tableName + "." + self.idKey + " = " + ownedModel.tableName + "." + ownedModel.shelf_idKey 
        query += " INNER JOIN " + shelvedModel.table + " ON " + ownedModel.tableName + "." + ownedModel.shelf_idKey + " = " + shelvedModel.tableName + "." + shelvedModel.shelf_idKey
        query += " WHERE " + ownedModel.tableName + "." + ownedModel.user_idKey + " = " + user_id + " AND " 
        query += shelvedModel.tableName + "." + shelvedModel.record_idKey + " = " + record_id
        query += " AND " + shelvedModel.tableName + "." + shelvedModel.activeKey + " = 1 AND " + ownedModel.tableName + "." + ownedModel.activeKey + " = 1;"
        return query


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
    editKey = "edit"

    primaryForeignKey = shelf_idKey

    requiredFields = [shelf_idKey,user_idKey,addedKey]
    allDatabaseKeys = [idKey,shelf_idKey,user_idKey,activeKey,addedKey,homeKey,home_positionKey,editKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,False,True,True,True]
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

    primaryForeignKey = record_idKey

    requiredFields = [shelf_idKey,record_idKey,shelvedKey]
    allDatabaseKeys = [idKey,shelf_idKey,record_idKey,activeKey,sortKey,shelvedKey,preview_sortKey]
    allDatabaseKeysIsNumeric = [True,True,True,True,True,False,True]
    minimalDatabaseKeys = []
    
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
    minimalDatabaseKeys = [idKey, primary_alias_idKey,disambiguation_noteKey]
    queryConditions = []
    
    def __init__(self) -> None:
        super().__init__()

    def setPrimaryAlias(self,alias_id: str):
        self.deliverableData[self.primary_alias_idKey] = alias_id

    def createGetIdByPrimaryAlias(self) -> str:
        query: str = "select "+self.idKey+" from " + self.table + " where "+self.primary_alias_idKey+" = " + self.deliverableData[self.primary_alias_idKey] + ";"
        return query

class Alias(Searchable):
    table = "shelf.alias"
    tableName = 'alias'

    idKey = "id"
    nameKey = "name" 
    artist_idKey = "artist_id" 
    vote_idKey = "vote_id"
    activeKey = "active"

    primaryForeignKey = vote_idKey

    requiredFields = [nameKey,artist_idKey,vote_idKey] #for new artists use id 1 then change after insert
    allDatabaseKeys = [idKey,nameKey,artist_idKey,vote_idKey,activeKey]
    allDatabaseKeysIsNumeric = [True,False,True,False,True]
    minimalDatabaseKeys = [idKey, nameKey]
    queryConditions = []

    searchFields = [nameKey]
    searchJoin: ModelData = Artist()
    searchJoinField = searchJoin.disambiguation_noteKey
    searchForeignKey = artist_idKey
    searchLimit = 20
    searchSort = nameKey
    searchActiveOnly = True
    
    def __init__(self) -> None:
        super().__init__()

    def setArtistIdToUpdate(self,artistId):
        self.deliverableData[self.artist_idKey] = artistId
        self.toUpdate.append(self.artist_idKey)

    def setNewArtistHold(self):
        self.deliverableData[self.artist_idKey] = '1'

    def createGetIdByNameVoteQuery(self) -> str:
        query: str = "select "+self.idKey+" from " + self.table + " where "+self.nameKey+" = '" + self.deliverableData[self.nameKey] + "' AND "+self.vote_idKey+" = '" + self.deliverableData[self.vote_idKey] + "';"
        return query

class Record(Searchable):
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
    release_yearKey = "release_year"

    primaryForeignKey = alias_idKey

    requiredFields = [titleKey,artist_idKey,alias_idKey]
    allDatabaseKeys = [idKey,titleKey,alias_idKey,coverKey,artist_idKey,songKey,parent_record_idKey,collaborationKey,release_yearKey]
    allDatabaseKeysIsNumeric = [True,False,True,False,True,True,True,True,True]
    minimalDatabaseKeys = [idKey, titleKey, coverKey]
    queryConditions = []

    searchFields = [titleKey]
    searchJoin: ModelData = Alias()
    searchJoinField = searchJoin.nameKey
    searchForeignKey = alias_idKey
    searchLimit = 20
    searchSort = titleKey
    searchActiveOnly = True
    
    def __init__(self) -> None:
        super().__init__()

    def createCollabJoinByArtistId(self,artist_id,limit = None):
        collabObject = Collaboration()
        aliasObject = Alias()
        
        innerOnCondition = self.tableName + "." + self.alias_idKey + " = " + aliasObject.tableName + "." + aliasObject.idKey 
        leftOnCondition = self.tableName + "." + self.idKey + " = " + collabObject.tableName + "." + collabObject.record_idKey


        whereCondition = "(" + self.tableName + "." + self.artist_idKey + " = " + artist_id + " OR " 
        whereCondition += collabObject.tableName + "." + collabObject.artist_idKey + " = " + artist_id + ")"

        thisKeysList = self.allDatabaseKeys
        otherKeysList = aliasObject.minimalDatabaseKeys
        
        self.allJoinedKeys = []

        #set fields to return
        query = "select "
        for field in thisKeysList:
            self.allJoinedKeys.append(field)
            query += self.tableName + "." + field + ", "
        for field in otherKeysList:
            tableField = aliasObject.tableName + "." + field
            self.allJoinedKeys.append(tableField)
            query +=  tableField + ", "
        
        query = query[0:-2] + " from " + self.table + " LEFT JOIN "+ collabObject.table + " ON " + leftOnCondition
        query += " INNER JOIN "+ aliasObject.table + " ON " + innerOnCondition + " where " + whereCondition
        if limit != None:
            query += " LIMIT "+str(limit)
        query += ";"
        return query
    
    def createShelvedJoinByShelfId(self,shelf_id,limit = None):
        shelvedObject = Shelved()
        aliasObject = Alias()
        
        innerOnCondition = self.tableName + "." + self.alias_idKey + " = " + aliasObject.tableName + "." + aliasObject.idKey 
        leftOnCondition = self.tableName + "." + self.idKey + " = " + shelvedObject.tableName + "." + shelvedObject.record_idKey


        whereCondition = shelvedObject.tableName + "." + shelvedObject.shelf_idKey + " = " + shelf_id

        thisKeysList = self.allDatabaseKeys
        otherKeysList = aliasObject.minimalDatabaseKeys
        
        self.allJoinedKeys = []

        #set fields to return
        query = "select "
        for field in thisKeysList:
            self.allJoinedKeys.append(field)
            query += self.tableName + "." + field + ", "
        for field in otherKeysList:
            tableField = aliasObject.tableName + "." + field
            self.allJoinedKeys.append(tableField)
            query +=  tableField + ", "
        
        query = query[0:-2] + " from " + self.table + " LEFT JOIN "+ shelvedObject.table + " ON " + leftOnCondition
        query += " INNER JOIN "+ aliasObject.table + " ON " + innerOnCondition + " where " + whereCondition
        if limit != None:
            query += " LIMIT "+str(limit)
        query += ";"
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
    

class Blog(Searchable):
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
    descriptionKey = "description"

    requiredFields = [nameKey]
    allDatabaseKeys = [idKey,nameKey,activeKey,record_idKey,user_idKey,artist_idKey,standaloneKey,privacy_idKey,imageKey,descriptionKey]
    allDatabaseKeysIsNumeric = [True,False,True,True,True,True,True,True,False,False]
    minimalDatabaseKeys = [idKey,nameKey]
    queryConditions = []

    searchFields = [nameKey,descriptionKey]
    searchLimit = 20
    searchSort = nameKey

    
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



