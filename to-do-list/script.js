$(document).ready(function () {
    loadTasks();
    $("#taskInput").on("keypress", function (e) {
        if (e.which === 13) {
            $("#addTask").click();
        }
    });
});

function loadTasks() {
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    $("#taskList").empty();
    tasks.forEach(function (task, index) {
        $("#taskList").append(`
            <li>
                ${task}
                <button onclick="deleteTask(${index})" class="delete-btn">X</button>
            </li>
        `);
    });
}

$("#addTask").click(function () {
    let task = $("#taskInput").val();
    if (task === "") return;
    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    tasks.push(task);
    localStorage.setItem("tasks", JSON.stringify(tasks));
    $("#taskInput").val("");
    loadTasks();
});


function deleteTask(index) {
    let tasks = JSON.parse(localStorage.getItem("tasks"));
    tasks.splice(index, 1);

    localStorage.setItem("tasks", JSON.stringify(tasks));
    loadTasks();
}
