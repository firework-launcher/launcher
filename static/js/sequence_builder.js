launchers = root["launchers"]
launcher_counts = root["launcher_data"]["counts"]

var id = document.getElementById("drawflow");
const editor = new Drawflow(id);
editor.editor_mode = 'edit';
editor.start();

selectedNode = null;
startId = 1;
endId = 2;

function updateNodeData(id, key, value) {
    node_data = editor.getNodeFromId(id)["data"];
    node_data[key] = value;
    editor.updateNodeDataFromId(id, node_data)
}

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

socketio_id = makeid(16);
socket = io()

sequence_name = null;

socket.on(socketio_id + "_save", (data) => {
    if (data["success"] == true) {
        console.log("Saved");
    } else {
        sequence_error(data["error"]);
    }
});

possibleConnections = {
    "start": ["launch"],
    "launch": ["delay", "end"],
    "delay": ["launch", "end"]
};

node_prettynames = {
    "start": "Start of sequence",
    "end": "End of sequence",
    "launch": "Launch Firework",
    "delay": "Delay"
}

function sequence_error(msg) {
    errortext = document.getElementById("error")
    errortext.innerText = msg;
    errortext.setAttribute("style", "color: red;");
}

editor.on('nodeCreated', function(id) {
    console.log("Node created " + id);
    if (editor.getNodeFromId(id)["name"] == "launch") {
        editor.updateNodeDataFromId(id, {"launcher": launchers[0], "firework": 1, "outConnected": false, "inConnected": false});
        document.getElementById("node-" + id).children[1].children[0].children[0].children[0].innerText = launchers[0] + ", 1";
    } else if (editor.getNodeFromId(id)["name"] == "delay") {
        editor.updateNodeDataFromId(id, {"delay": 1});
        document.getElementById("node-" + id).children[1].children[0].children[0].children[0].innerText = "1 second(s)";
    } else if (editor.getNodeFromId(id)["name"] == "start") {
        startId = id;
    } else if (editor.getNodeFromId(id)["name"] == "end") {
        endId = id;
    }
});

editor.on('nodeRemoved', function(id) {
    console.log("Node deleted " + id);
    if (id == startId) {
        var start = `
        <div>
        <div class="title-box">Start of sequence</div>
        </div>
        `;
        editor.addNode('start', 0,  1, 50, 50, 'start', {}, start );
    } else if (id == endId) {
        var end = `
        <div>
        <div class="title-box">End of sequence</div>
        </div>
        `;
        editor.addNode('end', 1,  0, 50, 150, 'end', {}, end );
    }
});

editor.on('nodeSelected', function(id) {
    console.log("Node selected " + id);
    selectedNode = id;
});

editor.on('nodeUnselected', function(ret) {
    console.log("Node unselected ");
    selectedNode = null;
});

function checkConnection(from, to) { return (possibleConnections[from].includes(to)) };

function getPossibleConnectionPrettyNames(nodename) {
    result = "";
    for (let i = 0; i < possibleConnections[nodename].length; i++) {
        result += node_prettynames[possibleConnections[nodename][i]];
        if (i < possibleConnections[nodename].length-1) {
            result += ", ";
        }
    }
    return result;
}

editor.on('connectionCreated', function(connection) {
    console.log('Connection created');
    fromNode = editor.getNodeFromId(connection["output_id"]);
    toNode = editor.getNodeFromId(connection["input_id"])
    error = false;
    if (fromNode["name"] == "launch") {
        if (fromNode["data"]["outConnected"] == true) {
            editor.removeSingleConnection(connection["output_id"], connection["input_id"], "output_1", "input_1");
            sequence_error("Launch Firework blocks can only have 1 out connection.");
            error = true;
        }
        updateNodeData(connection["output_id"], "outConnected", true);
    }
    if (toNode["name"] == "launch") {
        if (fromNode["data"]["inConnected"] == true) {
            editor.removeSingleConnection(connection["output_id"], connection["input_id"], "output_1", "input_1");
            sequence_error("Launch Firework blocks can only have 1 in connection.");
            error = true;
        }
        updateNodeData(connection["output_id"], "inConnected", true);
    }
    if (!(error)) {
        toNode = editor.getNodeFromId(connection["input_id"]);
        if (!(checkConnection(fromNode["name"], toNode["name"]))) {
            editor.removeSingleConnection(connection["output_id"], connection["input_id"], "output_1", "input_1");
            sequence_error("Connection invalid, these are all possible connections for " + node_prettynames[fromNode["name"]] + ": " + getPossibleConnectionPrettyNames(fromNode["name"]) + ".");
        }
    }
})

editor.on('connectionRemoved', function(connection) {
    console.log('Connection removed');
    node = editor.getNodeFromId(connection["output_id"])
    if (node["name"] == "launch") {
        updateNodeData(node["id"], "outConnected", false);
    }
    node = editor.getNodeFromId(connection["input_id"])
    if (node["name"] == "launch") {
        updateNodeData(node["id"], "inConnected", false);
    }
})

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

addNodeToDrawFlow('start');
addNodeToDrawFlow('end');

function save_launchmodal() {
    modal_firework = document.getElementById("launchmodal_firework");
    modal_launcher = document.getElementById("launchmodal_launcher");
    modal_nodeId = document.getElementById("launchmodal_nodeId");
    nodeId = modal_nodeId.value;
    updateNodeData(nodeId, "firework", parseInt(modal_firework.value));
    updateNodeData(nodeId, "launcher", modal_launcher.value);
    close_modal("launchmodal");
    document.getElementById("node-" + nodeId).children[1].children[0].children[0].children[0].innerText = modal_launcher.value + ", " + modal_firework.value;
}

function save_delaymodal() {
    modal_delay = document.getElementById("delaymodal_delay");
    modal_nodeId = document.getElementById("delaymodal_nodeId");
    nodeId = modal_nodeId.value;
    editor.updateNodeDataFromId(nodeId, {"delay": parseInt(modal_delay.value)});
    close_modal("delaymodal");
    document.getElementById("node-" + nodeId).children[1].children[0].children[0].children[0].innerText = modal_delay.value + " second(s)";
}

function close_modal(modal) {
    modal = document.getElementById(modal);
    modal.style.display = "none";
    editor.editor_mode = "edit";
}

function updateAllText() {
    launch_nodes = editor.getNodesFromName("launch");
    delay_nodes = editor.getNodesFromName("delay")
    for (let i = 0; i < launch_nodes.length; i++) {
        node_data = editor.getNodeFromId(launch_nodes[i])["data"]
        document.getElementById("node-" + launch_nodes[i]).children[1].children[0].children[0].children[0].innerText = node_data["launcher"] + ", " + node_data["firework"];
    }
    for (let i = 0; i < delay_nodes.length; i++) {
        node_data = editor.getNodeFromId(delay_nodes[i])["data"]
        document.getElementById("node-" + delay_nodes[i]).children[1].children[0].children[0].children[0].innerText = node_data["delay"] + " second(s)";
    }
}

function openmodal(modal, nodeId) {
    if (modal == "launchmodal") {
        modal_launcher = document.getElementById("launchmodal_launcher");
        modal_firework = document.getElementById("launchmodal_firework");
        modal_launcher.innerHTML = "";
        for (let i = 0; i < launchers.length; i++) {
            modal_launcher.innerHTML += '<option value="' + launchers[i] + '">' + launchers[i] + '</option>'
        }
        for (let i = 1; i < launcher_counts[editor.getNodeFromId(nodeId)["data"]["launcher"]]+1; i++) {
            modal_firework.innerHTML += '<option value="' + i + '">' + i + '</option>'
        }
        
        modal_firework.value = editor.getNodeFromId(nodeId)["data"]["firework"];
        modal_launcher.value = editor.getNodeFromId(nodeId)["data"]["launcher"];
    } else if (modal == "delaymodal") {
        modal_delay = document.getElementById("delaymodal_delay");
        modal_delay.value = editor.getNodeFromId(nodeId)["data"]["delay"];
    }
    if (!(modal == "savemodal")) {
        modal_nodeId = document.getElementById(modal + "_nodeId");
        modal_nodeId.value = nodeId;
    }
    modal = document.getElementById(modal);
    modal.style.display = "block";
    editor.editor_mode = "fixed";
}

function save_button() {
    if (sequence_name == null) {
        openmodal("savemodal", null);
    } else {
        save(sequence_name);
    }
}

function editSelectedNode() {
    if (!(selectedNode == null)) {
        node = editor.getNodeFromId(selectedNode);
        if (node["name"] == "launch") {
            openmodal("launchmodal", selectedNode);
        } else if (node["name"] == "delay") {
            openmodal("delaymodal", selectedNode);
        }
    }
}


function save(name) {
    save_data = editor.export();
    save_data["socketio_id"] = socketio_id;
    save_data["name"] = name
    socket.emit("sequencebuilder_save", save_data);
}

function save_savemodal() {
    sequence_name = document.getElementById("savemodal_name").value;
    save(sequence_name);
    close_modal("savemodal");
}

document.getElementById("launchmodal_launcher").addEventListener("change", function (ev) {
    modal_firework = document.getElementById("launchmodal_firework");
    modal_launcher = document.getElementById("launchmodal_launcher");
    modal_firework.innerHTML = "";
    for (let i = 1; i < launcher_counts[modal_launcher.value]+1; i++) {
        modal_firework.innerHTML += '<option value="' + i + '">' + i + '</option>';
    }
});
