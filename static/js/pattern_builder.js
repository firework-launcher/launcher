btn_div = document.getElementById("btns");


clicked_btns = [];
pattern_data = {};

current_step = 1

document.getElementById("launcher_select").addEventListener("change", function() {
    reload_buttons();
    clicked_btns = []
});

function find_fp(firework, launcher) {
    fp = firework_profiles[launcher];
    for (i = 0; i < Object.keys(fp).length; i++) {
        profile_name = Object.keys(fp)[i];
        profile_data = fp[profile_name];
        if (profile_data["fireworks"].includes(firework)) {
            return profile_data;
        }
    }
}

function reload_buttons() {
    launcher = document.getElementById("launcher_select").value;
    btn_div.innerHTML = "";
    for (let i = 1; i < launcher_counts[launcher]+1; i++) {
        button = document.createElement("button")
        button.setAttribute("id", "btn_" + i);
        button.setAttribute("onclick", "buttonClick(" + i + ")");
        button.setAttribute("class", "firework_button");
        color = find_fp(i, launcher)["color"];
        button.setAttribute("style", "color: " + color + "; border-color: " + color + ";");
        button.innerText = "#" + i;
        btn_div.appendChild(button);
    }
}

function fadeOut(element) {
    element.classList.add("remove");
}

function buttonClick(btn) {
    if (clicked_btns.includes(btn)) {
        launcher = document.getElementById("launcher_select").value;
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "firework_button");
        color = find_fp(btn, launcher)["color"];
        button.setAttribute("style", "color: " + color + "; border-color: " + color + ";");
        index = clicked_btns.indexOf(btn);
        clicked_btns.splice(index, 1);
    } else {
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "yellow-fb");
        button.setAttribute("style", "");
        clicked_btns.push(btn);
    }
}

function add_legend() {
    legend_div = document.getElementById("legend");
    launcher = document.getElementById("launcher_select").value;
    fp_length = Object.keys(firework_profiles[launcher]).length;;
    for (let i = 1; i < fp_length+1; i++) {
        key = i.toString();
        color = firework_profiles[launcher][key]["color"];
        pname = firework_profiles[launcher][key]["name"];
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
add_legend();
