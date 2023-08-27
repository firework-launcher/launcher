launcher_counts = root["launcher_data"]["counts"];
firework_profiles = root["firework_profiles"];
notes = root["notes"];

btn_div = document.getElementById("btns");


clicked_btns = {};
sequence_data = {};

current_step = 1

document.getElementById("launcher_select").addEventListener("change", function() {
    if (!(Object.keys(clicked_btns).includes(document.getElementById("launcher_select").value))) {
        clicked_btns[document.getElementById("launcher_select").value] = [];
    }
    reload_buttons();
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
        if (clicked_btns[launcher].includes(i)) {
            button.classList.add("yellow-fb");
        } else {
            button.setAttribute("style", "color: " + color + "; border-color: " + color + ";");
        }
        button.innerText = "#" + i;
        if (notes[launcher] != null) {
            if (notes[launcher][i.toString()] != null) {
                button.innerHTML += "<br/>" + notes[launcher][i.toString()];
            }
        }
        btn_div.appendChild(button);
    }
}

function fadeOut(element) {
    element.classList.add("remove");
}

function buttonClick(btn) {
    launcher = document.getElementById("launcher_select").value;
    if (clicked_btns[launcher].includes(btn)) {
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "firework_button");
        color = find_fp(btn, launcher)["color"];
        button.setAttribute("style", "color: " + color + "; border-color: " + color + ";");
        index = clicked_btns[launcher].indexOf(btn);
        clicked_btns[launcher].splice(index, 1);
    } else {
        button = document.getElementById("btn_" + btn);
        button.setAttribute("class", "yellow-fb");
        button.setAttribute("style", "");
        clicked_btns[launcher].push(btn)
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
    delay = document.getElementById("delay").value;
    if (/^\d+$/.test(delay)) {
        current_step += 1;
        step_count = document.getElementById("step");
        step_count.innerText = "Step " + current_step;
        launcher = document.getElementById("launcher_select").value;
        for (let i = 0; i < clicked_btns[launcher].length; ++i) {
            btn = document.getElementById("btn_" + clicked_btns[launcher][i]);
            fadeOut(btn);
            btn.setAttribute("onclick", "");
        }
        for (let i = 0; i < Object.keys(clicked_btns); i++) {
            if (clicked_btns[Object.keys(clicked_btns)[i]] == []) {
                delete clicked_btns[Object.keys(clicked_btns)[i]];
            }
        }
        
        sequence_data["Step " + (current_step-1)] = {
            "pins": clicked_btns,
            "delay": delay,
        };
    } else {
        delay_whole_number = document.getElementById("delay_whole_number");
        delay_whole_number.setAttribute("style", "color: red; display: block;");
    }
}

function submitSequence() {
    sequence_data_input = document.getElementById("sequence_data");
    sequence_name = document.getElementById("sequencename").value;
    if (/^[a-zA-Z 0-9\.\,\+\-].*$/g.test(sequence_name)) {
        sequence_name_field = document.getElementById("sequence_name");
        sequence_name_field.value = sequence_name;
        sequence_data_input.value = JSON.stringify(sequence_data);
        sequence_data_form = document.getElementById("sequence_form");
        sequence_data_form.submit();
    } else {
        special_characters = document.getElementById("special_characters");
        special_characters.setAttribute("style", "color: red; display: block;");
    }
}

reload_buttons();
add_legend();
