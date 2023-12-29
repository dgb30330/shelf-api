function decode(token) {
    try {
        return JSON.parse(atob(token.split(".")[1]));
    } catch (e) {
        console.log("error decoding token");
    }
}

const loginClick = async () => {
    bodyData = {
        'displayname':document.getElementById('displayname').value,
        'email':null,
        'password':document.getElementById('password').value,
        'last_login': getTimeStamp()
    }
    const jsonBody = JSON.stringify(bodyData);
    console.log(jsonBody)
    const response = await fetch('http://127.0.0.1:5000/api/login', {
    method: 'PUT',
    body: jsonBody,
    headers: {
        'Content-Type': 'application/json',
        
    }
    });
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    localStorage.setItem('shelf_user_token', myJson);
    var decoded = decode(myJson);
    console.log(decoded);

    localStorage.setItem('shelf_user_id', decoded.id);
    location.assign('/home.html?id='+decoded.id);
}