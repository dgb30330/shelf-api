import json
import jwt

secret = "whatever"

class ModelData:
    table = 'shelf.required'
    tableName = 'required'

    idKey = 'id'

    primaryForeignKey = None

    requestBodyData: dict = {}
    deliverableData: dict = {}

    requiredFieldsTuples = [] #(key, boolean to indicate numeric)
    allDatabaseKeys = []
    minimalDatabaseKeys = []

    joinObject = None
    allJoinedKeys = [] #does not need pre-populated

class Model(ModelData):

    def __init__(self) -> None:
        self.deliverableData = dict.fromkeys(self.allDatabaseKeys)


    def setId(self,incomingId):
        self.deliverableData[self.idKey] = incomingId

    def createJoinQuery(self,otherTableObject: ModelData, whereConditionFieldNumericboolValueTuple=None, foreignKey = None, thisMinimum = False, otherMinimum = False) -> str:
        #set conditions
        if foreignKey == None:
            foreignKey = self.primaryForeignKey
        relationCondition = self.tableName + "." + foreignKey + " = " + otherTableObject.tableName + "." + otherTableObject.idKey

        self.joinObject = otherTableObject #WATCH might be unneccessary 
        if whereConditionFieldNumericboolValueTuple != None:
            whereCondition = self.tableName + "." + whereConditionFieldNumericboolValueTuple[0] + " = "
            if whereConditionFieldNumericboolValueTuple[1]:
                whereCondition += whereConditionFieldNumericboolValueTuple[2]
            else:
                whereCondition += "'"+whereConditionFieldNumericboolValueTuple[2]+"'"
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

    def dictFromRaw(self, responseData: bytes):
        data = responseData.decode('UTF-8')
        data = data.replace("'",'"')
        newDict = json.loads(data)
        return newDict
    
    def populateFromRequest(self,rawBody: bytes):
        self.requestBodyData = self.dictFromRaw(rawBody)
        for key in self.requestBodyData:
            self.deliverableData[key] = self.requestBodyData[key]
    
    def prepDatabaseReturn(self,databaseData: tuple):
        if len(databaseData) == 1:
            databaseData = databaseData[0]
        for i in range(len(self.allDatabaseKeys)):
            self.deliverableData[self.allDatabaseKeys[i]] = databaseData[i]
        return self.deliverableData
    
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
        return self.deliverableData
    
    def manyJoinedDatabaseReturns(self,databaseData:tuple):
        allDecoded = []
        for innerTuple in databaseData:
            allDecoded.append(self.prepJoinedDatabaseReturn(innerTuple))
        return allDecoded

    
    def createGetMinimalByIdQuery(self) -> str:
        query: str = "select "
        for field in self.minimalDatabaseKeys:
            query += field + ", "
        query = query[0:-2] + " where id = " + str(self.deliverableData[self.idKey]) + ";"
        return query
    
    def createGetAllByIdQuery(self) -> str:
        query: str = "select * from " + self.table + " where id = " + str(self.deliverableData[self.idKey]) + ";"
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
        for field in self.requiredFieldsTuples:
            isNumeric = field[1]
            if self.deliverableData[field[0]] != None:
                textValue = self.deliverableData[field[0]]
            else:
                textValue = 'null'
                isNumeric = True
            query += "`"+field[0]+"`, "
            if isNumeric:
                values += textValue+", "
            else:
                values += "'"+textValue+"', "
        query = query[0:-2] + ") VALUES (" + values[0:-2] + ");"
        return query
        
        



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

    requiredFieldsTuples = [(displaynameKey,False), (emailKey,False), (imageKey,False), (privacy_idKey,True), (createdKey,False), (last_loginKey,False), (passwordKey,False), (signatureKey,False)]
    allDatabaseKeys = [idKey, displaynameKey, emailKey, imageKey, privacy_idKey, createdKey, last_loginKey, activeKey, passwordKey, signatureKey]
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

    requiredFieldsTuples = [(nameKey,False),(creator_idKey,True),(privacy_idKey,True),(descriptionKey,False)]
    allDatabaseKeys = [idKey,nameKey,creator_idKey,privacy_idKey,descriptionKey]
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

    requiredFieldsTuples = [(shelf_idKey,True),(user_idKey,True),(addedKey,False)]
    allDatabaseKeys = [idKey,shelf_idKey,user_idKey,activeKey,addedKey,homeKey,home_positionKey]
    minimalDatabaseKeys = [idKey, user_idKey]
    
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def createGetManyByUserIdQuery(user_id) -> str:
        return "select * from " + Owned.table + " INNER JOIN "+ Shelf.table +" where " + Owned.user_idKey + " = " + user_id + " ;"
        


