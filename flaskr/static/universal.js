function getTimeStamp() {
    const date = new Date();
    var formattedDateString = date.getFullYear() + '-' + date.getMonth() + '-' + date.getDate();
    formattedDateString += ' ';
    formattedDateString += date.getHours()+":"+date.getMinutes()+":"+date.getSeconds()+"."+date.getMilliseconds();
    return formattedDateString;

}