// function startTest(){
// window.location="dashboard.html"
// }

// document.getElementById("careerForm")?.addEventListener("submit",function(e){

// e.preventDefault()

// document.getElementById("careerResult").innerHTML="Software Engineer"

// var ctx=document.getElementById("careerChart")

// new Chart(ctx,{
// type:"bar",
// data:{
// labels:["Software","Data Science","Design"],
// datasets:[{
// label:"Career Match %",
// data:[85,70,60],
// backgroundColor:["blue","green","orange"]
// }]
// }
// })

// })

// function checkATS(){

// let text=document.getElementById("resumeText").value

// let score=Math.min(100,text.length/10)

// document.getElementById("atsScore").innerHTML=Math.floor(score)+"%"

// }

function startTest() {
    window.location.href = "/register";
}
// function startTest(){
// window.location="dashboard.html"
// }


// Career prediction

document.getElementById("careerForm")?.addEventListener("submit",function(e){

e.preventDefault()

var ctx=document.getElementById("skillChart")

new Chart(ctx,{
type:"radar",
data:{
labels:["Python","ML","SQL","Design","Communication"],
datasets:[{
label:"Your Skills",
data:[70,65,50,40,80],
backgroundColor:"rgba(56,189,248,0.4)"
}]
}
})

})


// ATS score simulation

function checkATS(){

let score=Math.floor(Math.random()*40)+60

document.getElementById("atsScore").innerHTML=score+"%"

}

const text = [
"AI Powered Career Recommendation",
"Find Your Dream Career",
"Smart Career Prediction"
];

let count = 0;
let index = 0;
let currentText = "";
let letter = "";

function type(){

if(count === text.length){
count = 0;
}

currentText = text[count];
letter = currentText.slice(0, ++index);

document.querySelector(".typing").textContent = letter;

if(letter.length === currentText.length){
count++;
index = 0;
}

setTimeout(type,100);
}

type();

function uploadResume() {

    let fileInput = document.getElementById("fileInput");

    if (fileInput.files.length === 0) {
        alert("Please select a file!");
        return;
    }

    let formData = new FormData();
    formData.append("resume", fileInput.files[0]);

    fetch("/ats", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {

        if (data.error) {
            alert(data.error);
        } else {
            showCircle(data.score);
        }

    })
    .catch(err => {
        console.error("Error:", err);
    });
}
let dropZone = document.querySelector(".drop-zone");

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.background = "#1a2a3a";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.background = "transparent";
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();

    let fileInput = document.getElementById("fileInput");
    fileInput.files = e.dataTransfer.files;

    alert("File selected: " + fileInput.files[0].name);
});