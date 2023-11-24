import json
import flaskr.models

def dictFromRaw(responseData: bytes):
    data = responseData.decode('UTF-8')
    data = data.replace("'",'"')
    newDict = json.loads(data)
    return newDict

def printableType(variableInQuestion):
    typeString = str(type(variableInQuestion))
    return typeString

def tokenValidation(request,mysql):
    isValid = False
    rawToken = request.headers['Authorization']
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
    if deliveredSignature == thisUser.getSignature():
        isValid = True
    return isValid