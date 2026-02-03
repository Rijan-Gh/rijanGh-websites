let currentTime = 0;
let timer = null;
let startTime = null;

function updateDisplay(){
    let currentTime = Date .now() - startTime;
    let milliseconds = currentTime % 1000;
    let seconds = Math.floor((currentTime / 1000) % 60);
    let minutes = Math.floor((currentTime / (1000 * 60)) % 60);
    let hours = Math.floor((currentTime / (1000 * 60 * 60)) % 24);


    let displayhour = hours < 10 ? '0' + hours : hours;
    let displayminute = minutes < 10 ? '0' + minutes : minutes;
    let displaysecond = seconds < 10 ? '0' + seconds : seconds;
    let displaymillisecond = milliseconds < 10 ? '00' + milliseconds : milliseconds < 100 ? '0' + milliseconds : milliseconds;
    
    document.getElementById("display").innerText = `${displayhour}:${displayminute}:${displaysecond}:${displaymillisecond}`;
}
function startStopWatch(){
    if(timer === null){
        startTime = Date.now() - currentTime;
        timer = setInterval(updateDisplay, 1);
    }
}

function stopStopWatch(){
    clearInterval(timer);
    timer = null;
}

function resetStopWatch(){
    clearInterval(timer);
    timer = null;
    currentTime = 0;
    document.getElementById("display").innerText = "00:00:00:00";
}   

function Lap(){
    let lapTime = document.getElementById("display").innerText;
    let lapList = document.getElementById("lapList");
    let listItem = document.createElement("li");
    listItem.innerText = lapTime;
    lapList.appendChild(listItem);
}








