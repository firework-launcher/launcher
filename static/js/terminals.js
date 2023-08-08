socket = io();

function remove_terminal(terminal) {
    remove = document.getElementById("remove_" + terminal);
    remove.innerText = "Are you sure?";
    remove.setAttribute("class", "sequence_delete_confirm");
    remove.setAttribute("onclick", "remove_terminal_confirm('" + terminal + "')");
}

function remove_terminal_confirm(terminal) {
    socket.emit("remove_terminal", terminal);
    terminal_element = document.getElementById("terminal_" + terminal);
    terminal_element.remove();
}

add_terminal_button = document.getElementById("add_terminal");
add_terminal_button.setAttribute("href", "/settings/terminals/add/" + (window.innerHeight > window.innerWidth));
