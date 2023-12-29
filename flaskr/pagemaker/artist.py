import flaskr.pagemaker.base as base

class Artist(base.Base):
    bodyStart = '<body onload="populateFullArtist()">'

    def incorporateObjectId(self,objectId):
        self.bodyStart = '<body onload="populateFullArtist('+objectId+')">'

    def getCustomBody(self):
        body = '<div>'
        body += '<h1 id="artist"></h1>'
        body += '</div>'
        body += '<div><h5>Discography:</h5>'
        body += '<div id="records">'

        body += '</div>'
        body += '</div>'
        return body

    def getCustomHead(self):
        script = '<script src="http://127.0.0.1:5000/static/artist.js"></script>'
        return script