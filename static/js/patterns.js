socket = io();

interval_ids = {};

function finish_pattern(pattern) {
    run = document.getElementById("run_" + pattern);
    run.innerText = "Run";
};

socket.on("running_pattern", (pattern) => {
    run = document.getElementById("run_" + pattern);
    run.innerText = "Running";
    id = setInterval(async function () { await check_pattern(pattern) }, 1000); 
    interval_ids[pattern] = id;
});

function run_pattern(pattern) {
    socket.emit("run_pattern", pattern);
}

function delete_pattern(pattern) {
    delete_ = document.getElementById("delete_" + pattern);
    delete_.innerText = "Are you sure?";
    delete_.setAttribute("class", "pattern_delete_confirm");
    delete_.setAttribute("onclick", "delete_pattern_confirm('" + pattern + "')");
}

function delete_pattern_confirm(pattern) {
    socket.emit("delete_pattern", pattern);
    pattern_element = document.getElementById("pattern_" + pattern);
    pattern_element.remove();
}

function expand_hamburger () {
    menu = document.getElementById("hamburgerExpandMenu");
    if (menu.style.display == "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}

async function check_pattern(pattern) {
    request = await fetch(window.origin + "/pattern_status/" + pattern);
    data = await request.json();
    if (data["running"] == false) {
        finish_pattern(pattern);
        clearInterval(interval_ids[pattern]);
    }
}

