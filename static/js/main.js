const socket = io();

socket.on("connect", () => {
    console.log("Connected");
});

socket.on("disconnect", () => {
    console.log("Lost Connection");
    for (let index = 0; index < fireworks_launched.length; ++index) {
        set_btn_blue(fireworks_launched[index]);
    }
})

socket.on('firework_launch', (data) => {
    set_btn_red(data['firework']);
    fireworks_launched.push(data['firework']);
});

socket.on('reset', () => {
    for (let index = 0; index < fireworks_launched.length; ++index) {
        set_btn_blue(fireworks_launched[index]);
    }
});

function add_btns(rows) {
    for (let i = 1; i < rows+1; i++) {
        element = document.getElementById("firework_buttons");
        button = document.createElement("a");
        button_class = document.createAttribute("class");
        button_js_onclick = document.createAttribute("onclick");
        button_id = document.createAttribute("id");
        button_class.value = "firework_button";
        button_js_onclick.value = "trigger_firework(" + i + ");";
        button_id.value = "fb_"+i
        button.innerText = "#"+i;
        button.setAttributeNode(button_class);
        button.setAttributeNode(button_js_onclick);
        button.setAttributeNode(button_id);
        element.appendChild(button);
    }
}

function trigger_firework(fb_id) {
    socket.emit("launch_firework", {"firework": fb_id});
}

function set_btn_red(btn_id) {
    button = document.getElementById("fb_" + btn_id);
    if (button != null) {
        button_color = document.createAttribute("style");
        button_color.value = "background-color: red;";
        button.removeAttribute("onclick");
        button.setAttributeNode(button_color);
    }
}

function reset() {
    socket.emit("exec_reset");
}

function set_btn_blue(btn_id) {
    button = document.getElementById("fb_" + btn_id);
    if (button != null) {
        button.removeAttribute("style");
        button.removeAttribute("onclick");
        button_js_onclick = document.createAttribute("onclick");
        button_js_onclick.value = "trigger_firework(" + btn_id + ");";
        button.setAttributeNode(button_js_onclick);
    }
}

add_btns(rows);

for (let index = 0; index < fireworks_launched.length; ++index) {
    set_btn_red(fireworks_launched[index]);
}
