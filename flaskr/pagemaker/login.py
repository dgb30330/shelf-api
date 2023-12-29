import flaskr.pagemaker.base as base

class Login(base.Base):

    def getCustomBody(self):
        bodyHtml = '<div>'
        bodyHtml += r'<form id="loginForm" action="/">'
        bodyHtml += '<label for="displayname">Username:</label><br>'
        bodyHtml += '<input type="text" id="displayname" name="displayname" value=""><br>'
        bodyHtml += '<label for="password">Password:</label><br>'
        bodyHtml += '<input type="text" id="password" name="password" value=""><br><br>'
        bodyHtml += '</form>' 
        bodyHtml += '<button onclick="loginClick()">Login</button>'
        bodyHtml += "</div>"
        return bodyHtml
    
    def getCustomHead(self):
        script = '<script src="http://127.0.0.1:5000/static/login.js"></script>'
        return script