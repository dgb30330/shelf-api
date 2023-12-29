import json
import flaskr.models

def dictFromRaw(responseData: bytes):
    data = responseData.decode('UTF-8')
    data = data.replace("'",'"')
    newDict = json.loads(data)
    return newDict

def encode(incoming):
    return json.dumps(incoming, separators=(',', ':'))

def printableType(variableInQuestion):
    typeString = str(type(variableInQuestion))
    return typeString

def tokenValidation(request,mysql):
    isValid = False
    try:
        rawToken = request.headers['Authorization']
    except:
        return isValid
    thisUser = flaskr.models.User(False)
    try:
        thisUser.populateFromToken(rawToken) #decoding token likely needs validation
    except:
        return isValid
    deliveredSignature = thisUser.getSignature()
    cur = mysql.connection.cursor()
    cur.execute(thisUser.createGetAllByIdQuery())
    userData = cur.fetchall()
    thisUser.prepDatabaseReturn(userData)
    cur.close()
    if deliveredSignature == thisUser.getSignature():
        isValid = True
    return isValid

def simpleInsert(request,mysql,dataModelObject: flaskr.models.Model,insertVote = False):
    dataModelObject.populateFromRequest(request.data)
    #Should daata be loaded seperately?
    if insertVote:
        newVote = flaskr.models.Vote()
        dataModelObject.setVoteId(newVote.generateId())
    try:
        cur = mysql.connection.cursor()
        if insertVote:
            cur.execute(newVote.createInsertQuery())
        #for debug
        #return dataModelObject.createInsertQuery()
        cur.execute(dataModelObject.createInsertQuery())
        mysql.connection.commit()
        cur.close()
        return str(True)
    except Exception as e:
        return str(e)
    
def simpleUpdate(id,request,mysql,dataModelObject: flaskr.models.Model):
    dataModelObject.setId(id)
    dataModelObject.populateFromRequest(request.data,forUpdate=True)
    try:
        cur = mysql.connection.cursor()
        #for debug
        #return dataModelObject.createUpdateQuery()
        cur.execute(dataModelObject.createUpdateQuery())
        mysql.connection.commit()
        changedData = simpleDatabaseGet(id,mysql,dataModelObject)
        cur.close()
        return changedData
    except Exception as e:
        return str(e)
        
    
def simpleDatabaseGet(id,mysql,dataModelObject: flaskr.models.Model,minimal=False):
        dataModelObject.setId(id)
        try:
            cur = mysql.connection.cursor()
            cur.execute(dataModelObject.createSelectByIdQuery())
            rv = cur.fetchall()
            cur.close()
            return dataModelObject.prepDatabaseReturn(rv)
        except Exception as e:
            return str(e)
    
def getRecordHtml(recordDataObject: flaskr.models.Record):
    html = ""
    html+="<html>"
    html+="<head>"
    """
        <title>Partner with Mastercard to deliver great consumer experiences through APIs</title>
        <meta property="og:image" content="https://developer.mastercard.com/media/partner-with-mastercard-banner-01.png" />
        <meta property="og:type" content="article" />
        <meta property="og:title" content="Partner with Mastercard to deliver great consumer experiences through APIs" />
        <meta property="og:url" content="https://developer.mastercard.com/blog/partner-with-mastercard-to-deliver-great-consumer-experiences-through-apis" />
        <meta property="og:description" content="In the very earliest days of Mastercard, we didn’t have an API (Application Programming Interface) – the shop attendant would call the bank to see if the card presented had enough credit to cover the purchase. This was card payments when the interface was human beings on the phone. For decades no..." />
    """
    html+="</head>"
    html+="<body><p>Testing</p><h1>"+recordDataObject.deliverableData[recordDataObject.titleKey]+"</h1></body>"
    html+="</html>"

    return html