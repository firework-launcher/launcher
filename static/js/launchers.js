
function remove_launcher(launcher) {
    remove = document.getElementById("remove_" + launcher);
    remove.innerText = "Are you sure?";
    remove.setAttribute("class", "sequence_delete_confirm");
    remove.setAttribute("onclick", "remove_launcher_confirm('" + launcher + "')");
}

function launcher_addonstart(launcher) {
    socket.emit("launcher_addonstart", launcher);
    addonstart_button = document.getElementById("addonstart_" + launcher);
    if (Array.from(addonstart_button.classList).includes("addonstart_on")) {
        addonstart_button.classList.remove("addonstart_on");
        addonstart_button.classList.add("addonstart_off");
    } else {
        addonstart_button.classList.remove("addonstart_off");
        addonstart_button.classList.add("addonstart_on");
    }
}

function remove_launcher_confirm(launcher) {
    socket.emit("remove_launcher", launcher);
    launcher_element = document.getElementById("launcher_" + launcher);
    launcher_element.remove();
}
