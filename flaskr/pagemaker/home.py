import flaskr.pagemaker.base as base

class Home(base.Base):

    def getCustomBody(self):
        return "<div>HOME</div>1"

    def getCustomHead(self):
        return ""