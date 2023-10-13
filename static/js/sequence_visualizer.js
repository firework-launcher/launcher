launchers = root["launchers"]
launcher_counts = root["launcher_data"]["counts"]
labels = root["labels"];
sequences = root["sequences"];
drawflow_sequences = root["drawflow_sequences"];
profiles = root["firework_profiles"];

var id = document.getElementById("drawflow");
const editor = new Drawflow(id);
editor.editor_mode = 'edit';
editor.start();

current_nodeId = null;
selectedNode = null;
startId = 1;
endId = 2;
fireworks_used = [];
current_step = null;
time_step_changed = null;

function makeid(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
      counter += 1;
    }
    return result;
}

function updateNodeWithFirework(nodeId, launcher, firework) {

    document.getElementById("node-" + nodeId).children[1].children[0].children[0].children[0].innerHTML = labels[launcher][firework] + "<br/>" + launcher + ", " + firework; // Using innerHTML is safe here since special characters are filtered out
}

socketio_id = makeid(16);

function getFireworkByLabel(label) {
    firework_ = null;
    launcher_ = null;
    for (let i = 0; i < Object.keys(labels).length; i++) {
        launcher__ = Object.keys(labels)[i];
        for (let x = 0; x < Object.keys(labels[launcher__]).length; x++) {
            if (labels[launcher__][Object.keys(labels[launcher__])[x]] == label) {
                firework_ = Object.keys(labels[launcher__])[x];
                launcher_ = JSON.parse(JSON.stringify(launcher__));
            }
        }
    }
    return [launcher_, firework_];
}

function sequence_error(msg) {
    errortext = document.getElementById("error")
    errortext.innerText = msg;
    errortext.setAttribute("style", "color: red;");
}

function updateAllText() {
    launch_nodes = editor.getNodesFromName("launch");
    delay_nodes = editor.getNodesFromName("delay")
    for (let i = 0; i < launch_nodes.length; i++) {
        node_data = editor.getNodeFromId(launch_nodes[i])["data"]
        updateNodeWithFirework(launch_nodes[i], node_data["launcher"], node_data["firework"])
    }
    for (let i = 0; i < delay_nodes.length; i++) {
        node_data = editor.getNodeFromId(delay_nodes[i])["data"]
        document.getElementById("node-" + delay_nodes[i]).children[1].children[0].children[0].children[0].innerText = node_data["delay"] + " second(s)";
    }
}

function addNodeToDrawFlow(name) {
    if(editor.editor_mode === 'fixed') {
        return false;
    }

    switch (name) {
        case 'launch':
            var launch = `
            <div>
            <div class="title-box" style="line-height: 25px">Launch Firework<p style="margin: 0"></p></div>
            </div>
            `;
            editor.addNode('launch', 1,  1, 50, 50, 'launch', {}, launch );
            break;
        case 'delay':
            var delay = `
            <div>
            <div class="title-box" style="line-height: 25px">Delay<p style="margin: 0"></p></div>
            </div>
            `;
            editor.addNode('delay', 1,  1, 50, 50, 'delay', {}, delay );
            break;
        case 'start':
            var start = `
            <div>
            <div class="title-box">Start of sequence</div>
            </div>
            `;
            editor.addNode('start', 0,  1, 50, 50, 'start', {}, start );
            break;
        case 'end':
            var end = `
            <div>
            <div class="title-box">End of sequence</div>
            </div>
            `;
            editor.addNode('end', 1,  0, 50, 150, 'end', {}, end );
            break;
        default:
    }
}



interval_id = null;

function resetFiredColors() {
    launch_nodes = editor.getNodesFromName("launch");
    for (let i = 0; i < launch_nodes.length; i++) {
        document.getElementById("node-" + launch_nodes[i]).classList.remove("node-running");
    }
    delay_nodes = editor.getNodesFromName("delay");
    for (let i = 0; i < delay_nodes.length; i++) {
        document.getElementById("node-" + delay_nodes[i]).classList.remove("node-running");
    }
    end_nodes = editor.getNodesFromName("end");
    for (let i = 0; i < end_nodes.length; i++) {
        document.getElementById("node-" + end_nodes[i]).classList.remove("node-running");
    }
}

function finish_sequence(sequence) {
    run = document.getElementById("run_button");
    run.innerText = "Run";
    run.setAttribute("onclick", "run_sequence('" + sequence + "')");
    document.getElementById("stop_button").setAttribute("style", "display: none");
    document.getElementById("firenow").setAttribute("style", "display: none");
    resetFiredColors();
};

socket.on("running_sequence", () => {
    run = document.getElementById("run_button");
    run.setAttribute("onclick", "");
    run.innerText = "Running";
    id = setInterval(async function () { await check_sequence(sequence) }, 500); 
    interval_id = id;
    document.getElementById("stop_button").setAttribute("style", "");
    document.getElementById("firenow").setAttribute("style", "")
});

function firenow() {
    socket.emit("firenow", sequence);
}

function run_sequence() {
    socket.emit("run_sequence", sequence);
}

function stop_sequence() {
    socket.emit("stop_sequence", sequence);
}

function getNodeFromFirework(launcher, firework) {
    launch_nodes = editor.getNodesFromName("launch");
    for (let i = 0; i < launch_nodes.length; i++) {
        node = editor.getNodeFromId(launch_nodes[i]);
        if (node["data"]["launcher"] == launcher && node["data"]["firework"] == firework) {
            return launch_nodes[i];
        }
    }
}

async function check_sequence() {
    request = await fetch(window.origin + "/sequence_status/" + sequence);
    data = await request.json();
    if (data["error"] != undefined) {
        error_text_element = document.getElementById("error_text");
        if (data["error"] == "failed") {
            error_text_element.innerText = "Failed to run. Check logs for more info.";
        } else if (data["error"] == "unarmed") {
            error_text_element.innerText = "Failed to run. One or more launchers is unarmed.";
        } else if (data["error"] == "notadded") {
            error_text_element.innerText = "Failed to run. One or more launchers is not added.";
        }
        error_element = document.getElementById("error");
        error_element.setAttribute("style", "display: block");
    }
    if (data["running"] == false) {
        finish_sequence(sequence);
        clearInterval(interval_id);
    } else {
        run = document.getElementById("run_button");
        run.innerText = "Running - " + data["step"] + " - Next step in " + data["next_step_in"] + " sec.";
        step = sequences[sequence][data["step"]];
    
        if (step != undefined) {
            resetFiredColors();
            console.log(current_step)
            if (current_step != data["step"]) {
                current_step = JSON.parse(JSON.stringify(data["step"]));
                time_step_changed = Date.now();
            }
            if (Date.now() - time_step_changed >= 1) {
                for (let i = 0; i < Object.keys(step["pins"]).length; i++) {
                    fireworks = step["pins"][Object.keys(step["pins"])[i]];
                    launcher = Object.keys(step["pins"])[i];
                    for (let x = 0; x < fireworks.length; x++) {
                        firework = fireworks[x];
                        node = getNodeFromFirework(launcher, firework);
                        node = editor.getNodeFromId(node);
                        delay_node = parseInt(node["outputs"]["output_1"]["connections"][0]["node"]);
                        document.getElementById("node-" + delay_node).classList.add("node-running");
                    }
                }
            } else {
                for (let i = 0; i < Object.keys(step["pins"]).length; i++) {
                    fireworks = step["pins"][Object.keys(step["pins"])[i]];
                    launcher = Object.keys(step["pins"])[i];
                    for (let x = 0; x < fireworks.length; x++) {
                        firework = fireworks[x];
                        node = getNodeFromFirework(launcher, firework);
                        document.getElementById("node-" + node).classList.add("node-running");
                    }
                }
            }
        }
    }
}


editor.import(drawflow_sequences[sequence]);
fireworks_used = [];
export_data = editor.export()["drawflow"]["Home"]["data"];
for (let i = 0; i < Object.keys(export_data).length; i++) {
    node = export_data[Object.keys(export_data)[i]];
    if (node["name"] == "launch") {
        if (!(node["data"]["launcher"] == null)) {
            fireworks_used.push(labels[node["data"]["launcher"]][node["data"]["firework"].toString()])
        }
    }
}
updateAllText();

editor.editor_mode = 'view';
