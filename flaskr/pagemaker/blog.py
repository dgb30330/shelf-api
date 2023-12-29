import flaskr.pagemaker.base as base

class Blog(base.Base):

    def getCustomBody(self):
        return ""

    def getCustomHead(self):
        return ""