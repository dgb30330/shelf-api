import json


class Model:
    table = 'required'

    idKey = 'id'
    id = 0

    requestBodyData: dict = {}
    deliverableData: dict = {}

    requiredFieldsTuples = [] #(key, boolean to indicate numeric)
    allDatabaseKeys = []



    def __init__(self, isNew: bool) -> None:
        self.isNew = isNew
        self.deliverableData = dict.fromkeys(self.allDatabaseKeys)
        

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
        return str(self.deliverableData)
        
    
    def createGetAllByIdQuery(self) -> str:
        query: str = "select * from " + self.table + " where id = " + self.id + ";"
        return query

    def createInsertQuery(self) -> str:
        query: str = "INSERT INTO " + self.table + " ("
        values: str = ""
        for field in self.requiredFieldsTuples:
            query += "`"+field[0]+"`, "
            if field[1]:
                values += self.deliverableData[field[0]]+", "
            else:
                values += "'"+self.deliverableData[field[0]]+"', "
        query = query[0:-2] + ") VALUES (" + values[0:-2] + ");"
        return query
        
        



class User(Model):
    table = "shelf.user"

    displaynameKey = 'displayname' #varchar45
    emailKey = 'email' #
    imageKey = 'image'
    privacy_idKey = 'privacy_id'
    createdKey = 'created'
    last_loginKey = 'last_login'
    activeKey = 'active'
    passwordKey = 'password'

    def __init__(self, isNew:bool) -> None:
        super().__init__(self,isNew)
        if(self.isNew):
            self.id = None

    def populateFromRequest(self,rawBody: bytes):
        dict = super().dictFromRaw(rawBody)
        self.displayname = dict[self.displaynameKey]
        self.email = dict[self.emailKey]
        self.image = dict[self.imageKey]
        self.privacy_id = dict[self.privacy_idKey]
        self.created = dict[self.createdKey]
        self.last_login = dict[self.last_loginKey]
        self.active = dict[self.activeKey]
        self.password = dict[self.passwordKey]


class Shelf(Model):
    table = "shelf.shelf"

    idKey = 'id'
    nameKey = "name" 
    creator_idKey = "creator_id"
    privacy_idKey = "privacy_id"
    descriptionKey = "description"

    requiredFieldsTuples = [(nameKey,False),(creator_idKey,True),(privacy_idKey,True),(descriptionKey,False)]
    allDatabaseKeys = [idKey,nameKey,creator_idKey,privacy_idKey,descriptionKey]

    def __init__(self, isNew:bool) -> None:
        super().__init__(isNew)
        if(self.isNew):
            self.id = None


