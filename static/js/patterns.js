socket = io();

interval_ids = {};

function finish_pattern(pattern) {
    run = document.getElementById("run_" + pattern);
    run.innerText = "Run";
    stop_pattern_element = document.getElementById("stop_" + pattern);
    stop_pattern_element.remove();
};

socket.on("running_pattern", (pattern) => {
    run = document.getElementById("run_" + pattern);
    run.innerText = "Running";
    id = setInterval(async function () { await check_pattern(pattern) }, 500); 
    interval_ids[pattern] = id;
    stop_pattern_element = document.createElement("button");
    stop_pattern_element.setAttribute("class", "pattern_delete_confirm");
    stop_pattern_element.setAttribute("id", "stop_" + pattern);
    stop_pattern_element.setAttribute("onclick", "stop_pattern('" + pattern + "')");
    stop_pattern_element.innerText = "Stop";
    h1pattern_element = document.getElementById("h1pattern_" + pattern);
    h1pattern_element.appendChild(stop_pattern_element);
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

function stop_pattern(pattern) {
    socket.emit("stop_pattern", pattern);
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
    if (data["error"] != undefined) {
        error_text_element = document.getElementById("error_text");
        error_text_element.innerText = "Pattern \"" + pattern + "\" failed to run. Check logs for more info.";
        error_element = document.getElementById("error");
        error_element.setAttribute("style", "display: block");
    }
    if (data["running"] == false) {
        finish_pattern(pattern);
        clearInterval(interval_ids[pattern]);
    } else {
        run = document.getElementById("run_" + pattern);
        run.innerText = "Running - " + data["step"] + " - Next step in " + data["next_step_in"] + " sec.";
    }
}
