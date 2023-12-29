import flaskr.pagemaker.text as tv

class Base:
    baseStart = "<!DOCTYPE html><html>"
    baseEnd = "</html>"
    headStart = "<head>"
    headGlobal = '<link rel="stylesheet" href="' + tv.base_url + '/static/style.css">'
    headGlobal += '<script src="' + tv.base_url + '/static/universal.js"></script>'
    headEnd = "</head>"
    bodyStart = "<body>"
    bodyEnd = "</body>"
    bodyGlobal = ""
    metaTitle = '<meta property="og:title" content="'+tv.site_name+'" />'
    metaType = '<meta property="og:type" content="website" />'
    metaUrl = '<meta property="og:url" content="' + tv.base_url + '" />'
    metaImage = '<meta property="og:image" content="' + tv.base_url + '/static/main.jpg" />'
    metaSite = '<meta property="og:site_name" content="'+tv.site_name+'" />'
    metaDescription = '<meta property="og:description" content="'+tv.slogan+'" />'
    
    def getHTML(self):
        html = self.baseStart
        html += self.getHead()
        html += self.getBody()
        html += self.baseEnd
        return html

    def getCustomHead(self):
        return ""
    
    def getMetaTags(self):
        metas = self.metaTitle
        metas += self.metaSite
        metas += self.metaType
        metas += self.metaUrl
        metas += self.metaDescription
        metas += self.metaImage
        return metas
    
    def getHead(self):
        head = self.headStart
        head += self.getMetaTags()
        head += self.getCustomHead()
        head += self.headGlobal
        head += self.headEnd
        return head
    
    def getBody(self):
        body = self.bodyStart
        body += self.getCustomBody()
        body += self.bodyGlobal
        body += self.bodyEnd
        return body

    def getCustomBody(self):
        return ""
    

bas = Base()
print(bas.getMetaTags())