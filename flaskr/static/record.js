function populateFullRecord(recordId){
    console.log(recordId)
    getRecord(recordId)
    userId = localStorage.getItem('shelf_user_id');
    populateShelfDropdown(userId)
    checkShelved(userId,recordId)
}
const getRecord = async (recordId) => {
    const response = await fetch('http://127.0.0.1:5000/api/record/'+recordId);
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    document.getElementById('artist').innerHTML = '<a href="/artist/'+myJson.artist_id+'">'+ myJson.alias.name+'</a>'
    document.getElementById('title').innerText = myJson.title
    injectLinks = ''
    for (let i = 0; i < myJson.link.length; i++) {
        injectLinks += '<p><a href="' + myJson.link[i].url + '">'
        if(myJson.link[i].platform_id == '1'){
            injectLinks+="YouTube"
        }
        else{
            injectLinks+="Other Streaming"
        }
            
        injectLinks += '</a> <i>'+myJson.link[i].url+'</i></p>'
    }
    document.getElementById('links').innerHTML = injectLinks
    injectResources = ''
    for (let i = 0; i < myJson.resource.length; i++) {
        injectResources += '<p><a href="' + myJson.resource[i].url + '">'
        if(myJson.resource[i].variety_code == '1'){
            injectResources+="Reference"
        }
        else if(myJson.resource[i].variety_code == '2'){
            injectResources+="Marketplace"
        }
        else if(myJson.resource[i].variety_code == '3'){
            injectResources+="Review"
        }
        else{
            injectResources+="Other Resource"
        }
            
        injectResources += '</a> <i>'+myJson.resource[i].url+'</i></p>'
    }
    document.getElementById('resources').innerHTML = injectResources
}
const populateShelfDropdown = async (userId) => {
    const response = await fetch('http://127.0.0.1:5000/api/shelves/edit/'+userId);
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    injectOptions = ''
    for (let i = 0; i < myJson.length; i++) {
        injectOptions += '<option value="'+myJson[i].shelf.id+'">'+myJson[i].shelf.name+'</option>'
    }
    document.getElementById('shelfSelect').innerHTML = injectOptions            
}
const shelveRecord = async () => {
    console.log(document.getElementById('shelfSelect').value)
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id')
    bodyData = {
        'shelf_id':document.getElementById('shelfSelect').value,
        'record_id':id,
        'shelved':'2023-12-04 03:03:04.05'
    }
    const jsonBody = JSON.stringify(bodyData);
    console.log(jsonBody)
    const response = await fetch('http://127.0.0.1:5000/api/shelved/0', {
    method: 'POST',
    body: jsonBody,
    headers: {
        'Content-Type': 'application/json', 
    }
    });
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)   
         
}
const tag = async () => {
    console.log(document.getElementById('shelfSelect').value)
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id')
    bodyData = {
        'shelf_id':document.getElementById('shelfSelect').value,
        'record_id':id,
        'shelved':'2023-12-04 03:03:04.05'
    }
    const jsonBody = JSON.stringify(bodyData);
    console.log(jsonBody)
    const response = await fetch('http://127.0.0.1:5000/api/shelved/0', {
    method: 'POST',
    body: jsonBody,
    headers: {
        'Content-Type': 'application/json', 
    }
    });
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)   
         
}
const checkShelved = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const recordId = urlParams.get('id')
    userId = localStorage.getItem('shelf_user_id');
    const response = await fetch('http://127.0.0.1:5000/api/shelf/r/u/'+recordId+'/'+userId);
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    if(myJson.length > 0){
        document.getElementById('shelvesLabel').style = "display: block;"
        injectHtml = ""
        for (let i = 0; i < myJson.length; i++) {
            injectHtml += '<p><a href="/shelf.html?id=' + myJson[i].id + '">'+myJson[i].name+'</a><i> ' +myJson[i].description + '</i></p>' 
        }
        document.getElementById('yourShelves').innerHTML = injectHtml
    }
    
         
}