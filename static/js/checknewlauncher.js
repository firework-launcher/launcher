socket = io();

socket.on("add_node_discover", (data) => {
    document.getElementById("node_warn_added").setAttribute("style", "display: block");
});

socket.on("node_crash_warning", (data) => {
    document.getElementById("node_warn_crash_txt").innerText = data[1] + " (" + data[0] + ") restarted. Some fireworks may have not been lit.";
    document.getElementById("node_warn_crash").setAttribute("style", "display: block")
});
