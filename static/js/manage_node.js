function are_you_sure(button_id, link) {
    btn = document.getElementById(button_id);
    btn.classList.add("sequence_delete_confirm");
    btn.setAttribute("onclick", "goto('" + link + "')");
    btn.innerText = "Are you sure?";
}

function goto(link) {
    window.location.href = link
}

function reboot() {
    are_you_sure("reboot", "/settings/launchers/espnode_settings/start" + node_port + "/reboot")
}

function change_wifi() {
    are_you_sure("change_wifi", "/settings/launchers/espnode_settings/start" + node_port + "/wifi")
}

function remove_node() {
    are_you_sure("remove", "/settings/launchers/espnode_settings/start" + node_port + "/remove")
}