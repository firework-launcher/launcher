launchers = root["launchers"]
launcher_counts = root["launcher_data"]["counts"]

var id = document.getElementById("drawflow");
const editor = new Drawflow(id);
editor.editor_mode = 'edit';
editor.start();

selectedNode = null;
launchNodes = {};
delayNodes = {};
startId = 1;
endId = 2;

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

nodeList = [];
connectionList = [];

function sequence_error(msg) {
    errortext = document.getElementById("error")
    errortext.innerText = msg;
    errortext.setAttribute("style", "color: red;");
}

editor.on('nodeCreated', function(id) {
    console.log("Node created " + id);
    if (editor.getNodeFromId(id)["name"] == "launch") {
        launchNodes[id.toString()] = {"launcher": launchers[0], "firework": 1, "outConnected": false};
        document.getElementById("node-" + id).children[1].children[0].children[0].children[0].innerText = launchers[0] + ", 1";
        nodeList.push({"id": id, "type": "Trigger Firework"});
    } else if (editor.getNodeFromId(id)["name"] == "delay") {
        delayNodes[id.toString()] = {"delay": 1};
        document.getElementById("node-" + id).children[1].children[0].children[0].children[0].innerText = "1 second(s)";
        nodeList.push({"id": id, "type": "Delay"});
    } else if (editor.getNodeFromId(id)["name"] == "start") {
        startId = id;
        nodeList.push({"id": id, "type": "Start of sequence"});
    } else if (editor.getNodeFromId(id)["name"] == "end") {
        endId = id;
        nodeList.push({"id": id, "type": "End of sequence"});
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
    delete launchNodes[id];
    delete delayNodes[id];
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

function correctConnections(input) {
    const nodes = input.nodes;
    const connections = input.connections;
    const correctedConnections = [...connections];
    const lastConnection = connections[connections.length - 1];
    const fromNode = nodes.find(node => node.id === lastConnection.from);
    const toNode = nodes.find(node => node.id === lastConnection.to);

    if (fromNode.type === 'Start of sequence' && toNode.type === 'Trigger Firework') {
        const nextNode = nodes.find(node => connections.some(conn => conn.from === toNode.id && conn.to === node.id));
        const otherTriggerFireworkNodes = nodes.filter(node => node.type === 'Trigger Firework' && connections.some(conn => conn.from === fromNode.id && conn.to === node.id));
        
        for (const node of otherTriggerFireworkNodes) {
            correctedConnections.push({ from: node.id, to: nextNode.id });
        }
    }
    
    return { nodes, connections: correctedConnections };
}

function getLayout() {
    result = {
        "nodes": [
            nodeList
        ], 
        "connections": [
            connectionList
        ]
    };
    return result;
}

function processLayout(layout) {
    newConnections = layout["connections"];
    oldConnectionList = JSON.parse(JSON.stringify(connectionList));
    for (let i = 0; i < oldConnectionList.length; i++) {
        connection = oldConnectionList[i];
        editor.removeSingleConnection(connection["from"], connection["to"], "output_1", "input_1");
    }
    for (let i = 0; i < newConnections.length; i++) {
        connection = newConnections[i];
        console.log(newConnections, connection)

        editor.addConnection(connection["from"], connection["to"], "output_1",  "input_1");
    }
}

editor.on('connectionCreated', function(connection) {
    console.log('Connection created');
    connectionList.push({"from": connection["output_id"], "to": connection["input_id"]})
    processLayout(correctConnections(getLayout()))
    fromNode = editor.getNodeFromId(connection["output_id"]);
    error = false;
    if (fromNode["name"] == "launch") {
        if (launchNodes[fromNode["id"]]["outConnected"] == true) {
            editor.removeSingleConnection(connection["output_id"], connection["input_id"], "output_1", "input_1");
            sequence_error("Launch Firework blocks can only have 1 out connection.");
            error = true;
        }
        launchNodes[fromNode["id"]]["outConnected"] = true;
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
    for (let i = 0; i < connectionList.length; i++) {
        if (JSON.stringify(connectionList[i]) == JSON.stringify({"from": connection["output_id"], "to": connection["input_id"]})) {
            delete connectionList[i];
        }
    }
    node = editor.getNodeFromId(connection["output_id"])
    if (node["name"] == "launch") {
        launchNodes[node["id"]]["outConnected"] = false;
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
    launchNodes[nodeId]["firework"] = parseInt(modal_firework.value);
    launchNodes[nodeId]["launcher"] = modal_launcher.value;
    close_modal("launchmodal");
    document.getElementById("node-" + nodeId).children[1].children[0].children[0].children[0].innerText = modal_launcher.value + ", " + modal_firework.value;
}

function save_delaymodal() {
    modal_delay = document.getElementById("delaymodal_delay");
    modal_nodeId = document.getElementById("delaymodal_nodeId");
    nodeId = modal_nodeId.value;
    delayNodes[nodeId] = {"delay": parseInt(modal_delay.value)};
    close_modal("delaymodal");
    document.getElementById("node-" + nodeId).children[1].children[0].children[0].children[0].innerText = modal_delay.value + " second(s)";
}

function close_modal(modal) {
    modal = document.getElementById(modal);
    modal.style.display = "none";
    editor.editor_mode = "edit";
}

function openmodal(modal, nodeId) {
    if (modal == "launchmodal") {
        modal_launcher = document.getElementById("launchmodal_launcher");
        modal_firework = document.getElementById("launchmodal_firework");
        modal_launcher.innerHTML = "";
        for (let i = 0; i < launchers.length; i++) {
            modal_launcher.innerHTML += '<option value="' + launchers[i] + '">' + launchers[i] + '</option>'
        }
        for (let i = 1; i < launcher_counts[launchNodes[nodeId]["launcher"]]+1; i++) {
            modal_firework.innerHTML += '<option value="' + i + '">' + i + '</option>'
        }
        
        modal_firework.value = launchNodes[nodeId]["firework"];
        modal_launcher.value = launchNodes[nodeId]["launcher"];
    } else if (modal == "delaymodal") {
        modal_delay = document.getElementById("delaymodal_delay");
        modal_delay.value = delayNodes[nodeId]["delay"];
    }
    modal_nodeId = document.getElementById(modal + "_nodeId");
    modal_nodeId.value = nodeId;
    modal = document.getElementById(modal);
    modal.style.display = "block";
    editor.editor_mode = "fixed";
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

document.getElementById("launchmodal_launcher").addEventListener("change", function (ev) {
    modal_firework = document.getElementById("launchmodal_firework");
    modal_launcher = document.getElementById("launchmodal_launcher");
    modal_firework.innerHTML = "";
    for (let i = 1; i < launcher_counts[modal_launcher.value]+1; i++) {
        modal_firework.innerHTML += '<option value="' + i + '">' + i + '</option>';
    }
});
