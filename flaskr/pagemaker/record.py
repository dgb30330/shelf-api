import flaskr.pagemaker.base as base

class Record(base.Base):
    bodyStart = '<body onload="populateFullRecord()">'

    def incorporateObjectId(self,objectId):
        self.bodyStart = '<body onload="populateFullRecord('+objectId+')">'

    def getCustomBody(self):
        body = '<div>'
        body += '<h2 id="artist"></h2>'
        body += '<h1 id="title"></h1>'
        body += '</div>'
        body += '<button style="display: inline;" onclick="tag()">Like</button>'
        body += '<button style="display: inline;" onclick="shelveRecord()">Add to Shelf</button>'
        body += '<select name="cars" id="shelfSelect">'

        body += '</select>'
        body += '<div><h5>Listen Links:</h5>'
        body += '<div id="links">'

        body += '</div>'
        body += '</div>'
        body += '<div><h5>Other Resources:</h5>'
        body += '<div id="resources">'

        body += '</div>'
        body += '</div>'
        body += '<div><h5 id="shelvesLabel" style="display: none;">Shelved:</h5>'
        body += '<div id="yourShelves">'

        body += '</div>'
        body += '</div>'
        return body

    def getCustomHead(self):
        script = '<script src="http://127.0.0.1:5000/static/record.js"></script>'
        return script