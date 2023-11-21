import json

def dictFromRaw(responseData: bytes):
    data = responseData.decode('UTF-8')
    data = data.replace("'",'"')
    newDict = json.loads(data)
    return newDict

def printableType(variableInQuestion):
    typeString = str(type(variableInQuestion))
    return typeString