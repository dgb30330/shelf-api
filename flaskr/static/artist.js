function populateFullArtist(id){
    getArtist(id)
    getRecords(id)
}
const getArtist = async (artistId) => {
    const response = await fetch('http://127.0.0.1:5000/api/artist/'+artistId);
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    document.getElementById('artist').innerText = myJson.alias.name
}
const getRecords = async (artistId) => {
    const response = await fetch('http://127.0.0.1:5000/api/records/artist/'+artistId);
    const myJson = await response.json(); //extract JSON from the http response
    console.log(myJson)
    injectHTML = ''
    for (let i = 0; i < myJson.length; i++) {
        injectHTML += '<div style="border: 1px solid black; margin-bottom: 5px; margin-right: 5px; display: inline-block;">'
        injectHTML += '<div style="border: 1px solid black; height: 35px; width: 35px; margin: 5px;"></div>'
        injectHTML += '<p>'+myJson[i].alias.name+'</p>'
        injectHTML += '<p><a href="/record/'+myJson[i].id+'"><b>'+myJson[i].title+'</b></a></p>'
        //YEAR!
        injectHTML += '</div>'
    }
    document.getElementById('records').innerHTML = injectHTML
}