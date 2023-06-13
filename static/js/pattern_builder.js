btn_div = document.getElementById("btns");

clicked_btns = [];
pattern_data = {};

current_step = 1

document.getElementById("launcher_select").addEventListener("change", function() {
    reload_buttons();
    clicked_btns = []
});

function reload_buttons() {
    launcher = document.getElementById("launcher_select").value;
    btn_div.innerHTML = "";
    for (let i = 1; i < launcher_counts[launcher]+1; i++) {
        button = document.createElement("button")
        button.setAttribute("id", "btn_" + i);
        button.setAttribute("onclick", "buttonClick(" + i + ")");
        button.setAttribute("class", "firework_button");
        button.innerText = "#" + i;
        btn_div.appendChild(button);
    }
}

function fadeOut(element) {
    element.classList.add("remove");
}

function buttonClick(btn) {
    if (clicked_btns.includes(btn)) {
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "firework_button");
        index = clicked_btns.indexOf(btn);
        clicked_btns.splice(index, 1);
    } else {
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "yellow-fb");
        clicked_btns.push(btn);
    }
}

function addStep() {
    current_step += 1;
    step_count = document.getElementById("step");
    step_count.innerText = "Step " + current_step;
    for (let i = 0; i < clicked_btns.length; ++i) {
        btn = document.getElementById("btn_" + clicked_btns[i]);
        fadeOut(btn);
        btn.setAttribute("onclick", "");
    }
    delay = document.getElementById("delay").value;
    launcher = document.getElementById("launcher_select").value;
    pattern_data["Step " + (current_step-1)] = {
        "pins": clicked_btns,
        "delay": delay,
        "launcher": launcher
    };

    clicked_btns = [];
}

function submitPattern() {
    pattern_data_input = document.getElementById("pattern_data");
    pattern_name = document.getElementById("patternname").value;
    pattern_name_field = document.getElementById("pattern_name");
    pattern_name_field.value = pattern_name;
    pattern_data_input.value = JSON.stringify(pattern_data);
    pattern_data_form = document.getElementById("pattern_form");
    pattern_data_form.submit();
}

reload_buttons();
