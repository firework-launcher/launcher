socket = io();

function delete_note(note) {
    delete_ = document.getElementById("delete_" + note);
    delete_.innerText = "Are you sure?";
    delete_.setAttribute("class", "pattern_delete_confirm");
    delete_.setAttribute("onclick", "delete_note_confirm('" + note + "')")
}

function delete_note_confirm(note) {
    socket.emit("delete_note", note);
    note_element = document.getElementById("note_" + note);
    note_element.remove();
}

function expand_hamburger () {
    menu = document.getElementById("hamburgerExpandMenu");
    if (menu.style.display == "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}