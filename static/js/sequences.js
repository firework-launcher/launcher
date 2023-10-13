
interval_ids = {};

function finish_sequence(sequence) {
    run = document.getElementById("run_" + sequence);
    run.innerText = "Run";
    run.setAttribute("onclick", "run_sequence('" + sequence + "')");
    stop_sequence_element = document.getElementById("stop_" + sequence);
    stop_sequence_element.remove();
    document.getElementById("firenow_" + sequence).setAttribute("style", "display: none");
};

function firenow(sequence) {
    socket.emit("firenow", sequence);
}

socket.on("running_sequence", (sequence) => {
    run = document.getElementById("run_" + sequence);
    run.setAttribute("onclick", "");
    run.innerText = "Running";
    id = setInterval(async function () { await check_sequence(sequence) }, 500); 
    interval_ids[sequence] = id;
    stop_sequence_element = document.createElement("button");
    stop_sequence_element.setAttribute("class", "sequence_delete_confirm");
    stop_sequence_element.setAttribute("id", "stop_" + sequence);
    stop_sequence_element.setAttribute("onclick", "stop_sequence('" + sequence + "')");
    stop_sequence_element.innerText = "Stop";
    h1sequence_element = document.getElementById("h1sequence_" + sequence);
    h1sequence_element.appendChild(stop_sequence_element);
    document.getElementById("firenow_" + sequence).setAttribute("style", "");
});

function run_sequence(sequence) {
    socket.emit("run_sequence", sequence);
}

function edit_sequence(sequence) {
    window.open(window.origin + "/sequences/edit/" + sequence, '_blank').focus();
}

function delete_sequence(sequence) {
    delete_ = document.getElementById("delete_" + sequence);
    delete_.innerText = "Are you sure?";
    delete_.setAttribute("class", "sequence_delete_confirm");
    delete_.setAttribute("onclick", "delete_sequence_confirm('" + sequence + "')");
}

function delete_sequence_confirm(sequence) {
    socket.emit("delete_sequence", sequence);
    sequence_element = document.getElementById("sequence_" + sequence);
    sequence_element.remove();
}

function stop_sequence(sequence) {
    socket.emit("stop_sequence", sequence);
}

async function check_sequence(sequence) {
    request = await fetch(window.origin + "/sequence_status/" + sequence);
    data = await request.json();
    if (data["error"] != undefined) {
        error_text_element = document.getElementById("error_text");
        if (data["error"] == "failed") {
            error_text_element.innerText = "Sequence \"" + sequence + "\" failed to run. Check logs for more info.";
        } else if (data["error"] == "unarmed") {
            error_text_element.innerText = "Sequence \"" + sequence + "\" failed to run. One or more launchers is unarmed.";
        } else if (data["error"] == "notadded") {
            error_text_element.innerText = "Sequence \"" + sequence + "\" failed to run. One or more launchers is not added.";
        }
        error_element = document.getElementById("error");
        error_element.setAttribute("style", "display: block");
    }
    if (data["running"] == false) {
        finish_sequence(sequence);
        clearInterval(interval_ids[sequence]);
    } else {
        run = document.getElementById("run_" + sequence);
        run.innerText = "Running - " + data["step"] + " - Next step in " + data["next_step_in"] + " sec.";
    }
}
