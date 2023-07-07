socket = io();

function remove_launcher(launcher) {
    remove = document.getElementById("remove_" + launcher);
    remove.innerText = "Are you sure?";
    remove.setAttribute("class", "sequence_delete_confirm");
    remove.setAttribute("onclick", "remove_launcher_confirm('" + launcher + "')");
}

function remove_launcher_confirm(launcher) {
    socket.emit("remove_launcher", launcher);
    launcher_element = document.getElementById("launcher_" + launcher);
    launcher_element.remove();
}

function expand_hamburger () {
    menu = document.getElementById("hamburgerExpandMenu");
    if (menu.style.display == "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}