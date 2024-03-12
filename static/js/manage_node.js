function are_you_sure(button_id, link) {
    btn = document.getElementById(button_id);
    btn.classList.add("sequence_delete_confirm");
    btn.setAttribute("onclick", "goto('" + link + "')");
    btn.innerText = "Are you sure?";
}

function will_reboot(button_id, link) {
    btn = document.getElementById(button_id);
    btn.classList.add("sequence_delete_confirm");
    btn.setAttribute("onclick", "goto('" + link + "')");
    btn.innerText = "Are you sure? This will reboot the node.";
}

function goto(link) {
    window.location.href = link;
}

function reboot() {
    are_you_sure("reboot", "/settings/launchers/espnode_settings/start" + node_port + "/reboot");
}

function configure() {
    if (node_version > 1) {
        are_you_sure("configure", "http://" + node_port);
    } else {
        will_reboot("configure", "/settings/launchers/espnode_settings/start" + node_port + "/wifi");
    }
}

function remove_node() {
    are_you_sure("remove", "/settings/launchers/espnode_settings/start" + node_port + "/remove")
}