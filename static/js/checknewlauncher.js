socket = io();

socket.on("add_node_discover", (data) => {
    document.getElementById("node_warn_added").setAttribute("style", "display: block");
});

socket.on("node_crash_warning", (data) => {
    document.getElementById("node_warn_crash_txt").innerHTML = data[1] + " (" + data[0] + `) restarted. Some fireworks may have not been lit. <span><button class="yellow_close_button" onclick="close_warn_crash();">X</button></span>`;
    document.getElementById("node_warn_crash").setAttribute("style", "display: block");
});

function close_warn_crash() {
    document.getElementById("node_warn_crash").setAttribute("style", "");
}

function close_add_node() {
    document.getElementById("node_warn_added").setAttribute("style", "");
}