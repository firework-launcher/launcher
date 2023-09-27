var fireworks_launched = root["fireworks_launched"];
var firework_profiles = root["firework_profiles"];
var launcher_names = root["launcher_data"]["names"];
var launcher_counts = root["launcher_data"]["counts"];
var launchers_armed = root["launcher_data"]["armed"];
var launcher_channels_connected = root["launcher_data"]["channels_connected"];
var launchers = root["launchers"];
var notes = root["notes"];
var sequences = root["sequences"];

const socket = io();

managing_notes = false;
devmode = false;

function update_channels_connected() {
    if (!(managing_notes) && !(devmode)) {
        for (i = 0; i < Object.keys(launcher_channels_connected).length; i++) {
            launcher = Object.keys(launcher_channels_connected)[i];

            firework_buttons = document.getElementById("firework_buttons_" + launcher);
            x = 1;
            for(var button=firework_buttons.firstChild; button!==null; button=button.nextSibling) {
                if (launcher_channels_connected[launcher].includes(x)) {
                    button.classList.remove("disconnected");
                } else {
                    if (!(button.classList.contains("disconnected"))) {
                        button.classList.add("disconnected");
                    }
                }
                x += 1
            }
        }
    }
}

function check_all_armed() {
    all_armed = false;
    for (i = 0; i < launchers.length; i++) {
        if (launchers_armed[launchers[i]]) {
            all_armed = true;
        }
    }

    if (all_armed) {
        arm_all_button = document.getElementById("armbutton");
        arm_all_button.setAttribute("style", "display: none");
        arm_all_button = document.getElementById("armbutton_");
        arm_all_button.setAttribute("style", "display: none");
        disarm_all_button = document.getElementById("disarmbutton");
        disarm_all_button.setAttribute("style", "");
        disarm_all_button = document.getElementById("disarmbutton_");
        disarm_all_button.setAttribute("style", "");
    } else {
        arm_all_button = document.getElementById("armbutton");
        arm_all_button.setAttribute("style", "");
        arm_all_button = document.getElementById("armbutton_");
        arm_all_button.setAttribute("style", "");
        disarm_all_button = document.getElementById("disarmbutton");
        disarm_all_button.setAttribute("style", "display: none");
        disarm_all_button = document.getElementById("disarmbutton_");
        disarm_all_button.setAttribute("style", "display: none");
    }
}

socket.on("disconnect", () => {
    console.log("Lost Connection");
    for (let index = 0; index < fireworks_launched.length; ++index) {
        set_btn_blue(fireworks_launched[index]);
    }
})

function firework_launch(launcher, firework) {
    if (fireworks_launched[launcher] != undefined) {
        set_btn_red(launcher, firework);
        fireworks_launched[launcher].push(firework);
        console.log("New firework launched. Launcher: " + launcher + " Firework: " + firework);
    }
}

socket.on('firework_launch', (data) => {
    firework_launch(data['launcher'], data['firework']);
});

function reset_launcher(launcher) {
    for (let index = 0; index < fireworks_launched[launcher].length; ++index) {
        set_btn_blue(launcher, fireworks_launched[launcher][index]);
    }
}

function reset_all() {
    socket.emit('reset_all');
}

socket.on('reset', (data) => {
    launcher = data['launcher']
    reset_launcher(launcher)
});

socket.on('reset_all', () => {
    for (var launcher in fireworks_launched) {
        reset_launcher(launcher);
    }
});

socket.on('running_sequence', (sequence) => {
    steps = Object.keys(sequences[sequence]);
    for (i = 0; i < steps.length; i++) {
        pins = sequences[sequence][steps[i]]["pins"];
        for (x = 0; x < pins.length; x++) {
            firework_launch(sequences[sequence][steps[i]]["launcher"], pins[x]);
        }
    }
});

socket.on('arm', (launcher) => {
    if (launchers.includes(launcher)) {
        armbutton = document.getElementById("armbutton_" + launcher);
        disarmbutton = document.getElementById("disarmbutton_" + launcher);
        armbutton.setAttribute("style", "display: none");
        disarmbutton.setAttribute("style", "");
        launchers_armed[launcher] = true;
        firework_buttons = document.getElementById("firework_buttons_" + launcher);
        for(var button=firework_buttons.firstChild; button!==null; button=button.nextSibling) {
            button.classList.remove("disarmed");
        }
    }
    check_all_armed();
});

socket.on('disarm', (launcher) => {
    if (launchers.includes(launcher)) {
        armbutton = document.getElementById("armbutton_" + launcher);
        disarmbutton = document.getElementById("disarmbutton_" + launcher);
        armbutton.setAttribute("style", "");
        disarmbutton.setAttribute("style", "display: none");
        launchers_armed[launcher] = false;
        firework_buttons = document.getElementById("firework_buttons_" + launcher);
        for(var button=firework_buttons.firstChild; button!==null; button=button.nextSibling) {
            if (!(button.classList.contains("remove"))) {
                button.classList.add("disarmed");
            }
        }
    }
    check_all_armed();
});

socket.on('update_channels_connected', (channels_connected) => {
    launcher_channels_connected = channels_connected
    update_channels_connected();
})

function get_profile_id(launcher, btn_id) {
    profile = null;
    for (var key in firework_profiles[launcher]) {
        if (firework_profiles[launcher].hasOwnProperty(key)) {
            if (firework_profiles[launcher][key]["fireworks"].indexOf(btn_id) !== -1) {
                profile = key
            }
        }
    }
    return profile;
}

function add_btns(rows, launcher) {
    armed = launchers_armed[launcher];
    for (let i = 1; i < rows+1; i++) {
        profile_id = get_profile_id(launcher, i);
        profile = firework_profiles[launcher][profile_id]
        element = document.getElementById("firework_buttons_"+launcher);
        button = document.createElement("a");
        button_class = document.createAttribute("class");
        button_fp = document.createAttribute("profile");
        button_js_onclick = document.createAttribute("onclick");
        button_id = document.createAttribute("id");
        button_style = document.createAttribute("style");
        if (armed) {
            button_class.value = "firework_button";
        } else {
            button_class.value = "firework_button disarmed";
        }
        button_js_onclick.value = "trigger_firework(" + i + ", \"" + launcher + "\");";
        button_id.value = "fb_" + launcher + "_" + i;
        button_fp.value = profile_id;
        button.innerText = "#"+i;
        if (notes[launcher] != null) {
            if (notes[launcher][i.toString()] != null) {
                button.innerHTML += "<br/>" + notes[launcher][i.toString()];
            }
        }
        button_style.value = "color: "+profile["color"]+"; border-color: "+profile["color"]+";";
        button.setAttributeNode(button_class);
        button.setAttributeNode(button_js_onclick);
        button.setAttributeNode(button_id);
        button.setAttributeNode(button_fp);
        button.setAttributeNode(button_style);
        element.appendChild(button);
    }
}

function expand_hamburger () {
    menu = document.getElementById("hamburgerExpandMenu");
    if (menu.style.display == "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}

function add_legend() {
    legend_div = document.getElementById("legend");
    fp_length = Object.keys(firework_profiles[launchers[0]]).length;;
    for (let i = 1; i < fp_length+1; i++) {
        key = i.toString();
        color = firework_profiles[launchers[0]][key]["color"];
        pname = firework_profiles[launchers[0]][key]["name"];
        text = document.createElement("p");
        text_class = document.createAttribute("class");
        text_style = document.createAttribute("style");
        text.innerText = pname;
        text_class.value = "legend-txt";
        text_style.value = "color: "+color+";";
        text.setAttributeNode(text_class);
        text.setAttributeNode(text_style);
        legend_div.appendChild(text);
    }
}

function trigger_firework(fb_id, launcher) {
    socket.emit("launch_firework", {"firework": fb_id, "launcher": launcher});
}

function fadeOut(element) {
    element.classList.add("remove");
}

function fadeIn(launcher, element) {
    if (launchers_armed[launcher] == false) {
        element.classList.add("disarmed");
    }
    element.classList.remove("remove");
}


function set_btn_red(launcher, btn_id) {
    button = document.getElementById("fb_" + launcher + "_" + btn_id);
    console.log([button, "fb_" + launcher + "_" + btn_id])
    if (button != null) {
        button_color = document.createAttribute("style");
        fadeOut(button);
        button.removeAttribute("onclick");
    }
}

function reset(launcher) {
    socket.emit("exec_reset", {"launcher": launcher});
}

function set_btn_blue(launcher, btn_id) {
    button = document.getElementById("fb_" + launcher + "_" + btn_id);
    if (button != null) {
        fadeIn(launcher, button);
        button.removeAttribute("onclick");
        button_js_onclick = document.createAttribute("onclick");
        button_js_onclick.value = "trigger_firework(" + btn_id + ", '" + launcher + "');";
        button.setAttributeNode(button_js_onclick);
    }
}

function arm_all() {
    socket.emit("arm_all");
}

function disarm_all() {
    socket.emit("disarm_all");
}

function dev() {
    devbutton = document.getElementById("devbutton")
    devbutton.innerText = "Save";
    devbutton.removeAttribute("onclick");
    devbutton_js_onclick = document.createAttribute("onclick");
    devbutton_js_onclick.value = "save_fp();";
    devbutton.setAttributeNode(devbutton_js_onclick);
    devbutton = document.getElementById("devbutton_")
    devbutton.innerText = "Save";
    devbutton.removeAttribute("onclick");
    devbutton_js_onclick = document.createAttribute("onclick");
    devbutton_js_onclick.value = "save_fp();";
    devbutton.setAttributeNode(devbutton_js_onclick);
    notes_button = document.getElementById("notesbutton");
    notes_button_2 = document.getElementById("notesbutton_");
    notes_button.setAttribute("onclick", "");
    notes_button_2.setAttribute("onclick", "");
    devmode = true;
    for (let index = 0; index < launchers.length; ++index) {
        for (let i = 1; i < launcher_counts[launchers[index]]+1; i++) {
            button = document.getElementById("fb_" + launchers[index] + "_" + i);
            if (button != null) {
                button.classList.remove("disconnected")
                button.removeAttribute("onclick");
                button_js_onclick = document.createAttribute("onclick");
                button_js_onclick.value = "change_profile('" + launchers[index] + "', " + i + ");";
                button.setAttributeNode(button_js_onclick);
            }
        }
    }
}

function save_fp() {
    socket.emit("save_fp", firework_profiles);
    devbutton = document.getElementById("devbutton");
    devbutton.innerText = "Profiles";
    devbutton.removeAttribute("onclick");
    devbutton_js_onclick = document.createAttribute("onclick");
    devbutton_js_onclick.value = "dev();";
    devbutton.setAttributeNode(devbutton_js_onclick);
    devbutton = document.getElementById("devbutton_");
    devbutton.innerText = "Profiles";
    devbutton.removeAttribute("onclick");
    devbutton_js_onclick = document.createAttribute("onclick");
    devbutton_js_onclick.value = "dev();";
    devbutton.setAttributeNode(devbutton_js_onclick);
    notes_button = document.getElementById("notesbutton");
    notes_button_2 = document.getElementById("notesbutton_");
    notes_button.setAttribute("onclick", "manage_notes()");
    notes_button_2.setAttribute("onclick", "manage_notes()");
    for (let li = 0; li < launchers.length; li++) {
        launcher = li
        for (let i = 1; i < launcher_counts[launchers[launcher]]+1; i++) {
            button = document.getElementById("fb_" + launchers[launcher] + "_" + i);
            if (button != null) {
                if (!(button.classList.contains("disconnected"))) {
                    button.setAttribute("onclick", "trigger_firework(" + i + ", '" + launchers[launcher] + "');");
                }
            } else {
                console.warn("Tried to change non-existant button, fb_" + launchers[launcher] + "_" + i)
            }
        }
    }
    devmode = false;
    update_channels_connected();
}

function removeItem(array, item) {
    var i = array.length;

    while (i--) {
        if (array[i] === item) {
            array.splice(array.indexOf(item), 1);
        }
    }
}

function change_profile(launcher, btn_id) {
    button = document.getElementById("fb_" + launcher + "_" + btn_id);
    old_profile_id = parseInt(button.getAttribute("profile"));
    fp_length = Object.keys(firework_profiles[launcher]).length;;
    if (old_profile_id+1 > fp_length) {
        profile_id = 1;
    } else {
        profile_id = old_profile_id + 1;
    }
    new_profile = firework_profiles[launcher][profile_id];
    button.removeAttribute("style");
    button.removeAttribute("profile");
    button_style = document.createAttribute("style");
    button_fp = document.createAttribute("profile");
    button_style.value = "color: "+new_profile["color"]+"; border-color: "+new_profile["color"]+";";
    button_fp.value = profile_id;
    button.setAttributeNode(button_style);
    button.setAttributeNode(button_fp);
    removeItem(firework_profiles[launcher][old_profile_id]["fireworks"], btn_id)
    firework_profiles[launcher][profile_id]["fireworks"].push(btn_id)
}

function set_note(firework, launcher) {
    launcher_indicator = document.getElementById("launcher-indicator");
    firework_indicator = document.getElementById("firework-indicator");
    note = document.getElementById("note_content");
    if (notes[launcher] != null) {
        if (notes[launcher][firework] == null) {
            note.value = "";
        } else {
            note.value = notes[launcher][firework];
        }
    } else {
        note.value = "";
    }
    modal_launcher = launcher;
    modal_firework = firework;
    launcher_indicator.innerText = "Launcher: " + launcher_names[launcher] + " (" + launcher + ")";
    firework_indicator.innerText = "Firework: " + firework;
    special_characters = document.getElementById("special_characters");
    special_characters.setAttribute("style", "display: none");
    modal = document.getElementById("modal");
    modal.style.display = "block";
    content = document.getElementById("content");
    content.style.pointerEvents = "none";
    content.classList.add("blur");
}

function add_note() {
    note = document.getElementById("note_content");
    if (/^[a-zA-Z 0-9\.\,\+\-]*$/g.test(note.value)) {
        if (note.value == "") {
            socket.emit("delete_note", modal_launcher + "_" + modal_firework);
        } else {
            socket.emit("note_update", {
                "launcher": modal_launcher,
                "firework": modal_firework,
                "note": note.value
            });
        }
        close_modal();
    } else {
        special_characters = document.getElementById("special_characters");
        special_characters.setAttribute("style", "color: red; display: block;")
    }
}

socket.on("note_update", (note) => {
    button = document.getElementById("fb_" + note["launcher"] + "_" + note["firework"]);
    button.innerHTML = "#" + note["firework"] + "<br/>" + note["note"];
    if (notes[note["launcher"]] == null) {
        notes[note["launcher"]] = {};
    }
    notes[note["launcher"]][note["firework"]] = note["note"];
});

socket.on("delete_note", (note) => {
    button = document.getElementById("fb_" + note["launcher"] + "_" + note["firework"]);
    button.innerHTML = "#" + note["firework"];
    delete notes[note["launcher"]][note["firework"]]
});

function close_modal() {
    modal = document.getElementById("modal");
    modal.style.display = "none";
    content = document.getElementById("content");
    content.classList.remove("blur");
    content.style.pointerEvents = "auto"
}

function arm(launcher) {
    socket.emit("arm", launcher);
}

function disarm(launcher) {
    socket.emit("disarm", launcher);
    
}

function manage_notes() {
    notes_button = document.getElementById("notesbutton");
    notes_button_2 = document.getElementById("notesbutton_");
    devbutton = document.getElementById("devbutton");
    devbutton_2 = document.getElementById("devbutton_");
    if (managing_notes) {
        devbutton.setAttribute("onclick", "dev();");
        devbutton_2.setAttribute("onclick", "dev();");
        notes_button.innerText = "Notes";
        notes_button_2.innerText = "Notes";
        managing_notes = false;
        for (let li = 0; li < launchers.length; li++) {
            launcher = li
            for (let i = 1; i < launcher_counts[launchers[launcher]]+1; i++) {
                button = document.getElementById("fb_" + launchers[launcher] + "_" + i);
                if (button != null) {
                    button.setAttribute("onclick", "trigger_firework(" + i + ", '" + launchers[launcher] + "');");
                } else {
                    console.warn("Tried to change non-existant button, fb_" + launchers[launcher] + "_" + i)
                }
            }
        }
        update_channels_connected();
    } else {
        notes_button.innerText = "Finish";
        notes_button_2.innerText = "Finish";
        devbutton.setAttribute("onclick", "");
        devbutton_2.setAttribute("onclick", "");
        managing_notes = true;
        for (let li = 0; li < launchers.length; li++) {
            launcher = li
            for (let i = 1; i < launcher_counts[launchers[launcher]]+1; i++) {
                button = document.getElementById("fb_" + launchers[launcher] + "_" + i);
                if (button != null) {
                    button.classList.remove("disconnected");
                    button.setAttribute("onclick", "set_note(" + i + ", '" + launchers[launcher] + "');");
                } else {
                    console.warn("Tried to change non-existant button, fb_" + launchers[launcher] + "_" + i)
                }
            }
        }
    }
}

for (let index = 0; index < launchers.length; ++index) {
    add_btns(launcher_counts[launchers[index]], launchers[index]);
}

add_legend();
update_channels_connected();

Object.entries(fireworks_launched).forEach(([launcher,launched]) => {
    for (let index = 0; index < launched.length; ++index) {
        set_btn_red(launcher, launched[index]);
    }
})

check_all_armed()