var profiles = root["firework_profiles"][launcher];

function remove_profile(profile) {
    profile_button = document.getElementById("remove_" + profile);
    profile_button.setAttribute("class", "sequence_delete_confirm");
    profile_button.innerText = "Are you sure?";
    profile_button.setAttribute("onclick", "remove_profile_confirm('" + profile + "')");
}

function exit_editor() {
    document.getElementById("profileeditor").setAttribute("style", "display: none");
    document.getElementById("profilelist").setAttribute("style", "")
}

function add_profile_to_list(profile) {
    profile_h2 = document.createElement("h2");
    profile_h2.setAttribute("id", "profile_" + profile);
    profile_h2.setAttribute("style", "color: " + profiles[profile]["color"]);

    profile_text = document.createElement("div");
    profile_text.setAttribute("style", "display: inline");
    profile_text.innerText = profiles[profile]["name"];
    profile_h2.appendChild(profile_text);

    edit_button = document.createElement("button");
    edit_button.setAttribute("class", "firework_button");
    edit_button.setAttribute("id", "edit_" + profile);
    edit_button.setAttribute("onclick", "edit_profile('" + profile + "')");
    edit_button.innerText = "Edit";
    profile_h2.appendChild(edit_button);

    remove_button = document.createElement("button");
    remove_button.setAttribute("class", "firework_button");
    remove_button.setAttribute("id", "remove_" + profile);
    remove_button.setAttribute("onclick", "remove_profile('" + profile + "')");
    remove_button.innerText = "Remove";
    profile_h2.appendChild(remove_button);

    document.getElementById("profilelist").insertBefore(profile_h2, document.getElementById("addprofilebutton"));

}

function save_editor(profile) {
    profile_existed = true;
    if (!(profile in profiles)) {
        profiles[profile] = {"fireworks": []};
        profile_existed = false;
    }
    profiles[profile]["name"] = document.getElementById("nameinput").value;
    profiles[profile]["color"] = document.getElementById("colorselector").value;
    profiles[profile]["pwm"] = parseInt(document.getElementById("pwm_slider").value);
    if (profile_existed == false) {
        add_profile_to_list(profile)
    } else {
        document.getElementById("profiletext_" + profile).innerText = profiles[profile]["name"];
        document.getElementById("profile_" + profile).setAttribute("style", "color: " + profiles[profile]["color"])
    }
    socket.emit("update_fp", {"launcher": launcher, "profiles": profiles});
    exit_editor();
}

function edit_profile(profile) {
    document.getElementById("profilelist").setAttribute("style", "display: none");
    document.getElementById("profileeditor").setAttribute("style", "");
    profilename = document.getElementById("profilename");
    profilename.setAttribute("style", "color: " + profiles[profile]["color"]);
    profilename.innerText = profiles[profile]["name"];
    document.getElementById("nameinput").value = profiles[profile]["name"];
    document.getElementById("colorselector").value = profiles[profile]["color"];
    document.getElementById("pwm_slider").value = profiles[profile]["pwm"];
    document.getElementById("pwm_slider_percentage").innerText = ((profiles[profile]["pwm"]/7500)*100).toFixed(2) + "%";
    document.getElementById("savebutton").setAttribute("onclick", "save_editor('" + profile + "')")
}

function add_profile() {
    profile = Object.keys(profiles).length + 1
    profile = profile.toString();
    document.getElementById("profilelist").setAttribute("style", "display: none");
    document.getElementById("profileeditor").setAttribute("style", "");
    profilename = document.getElementById("profilename");
    profilename.setAttribute("style", "color: #FFFFFF");
    profilename.innerText = "New profile";
    document.getElementById("nameinput").value = "";
    document.getElementById("colorselector").value = "#000000";
    document.getElementById("pwm_slider").value = 1875;
    document.getElementById("savebutton").setAttribute("onclick", "save_editor('" + profile + "')")
}

function change_profile_id(old_profile, new_profile) {
    document.getElementById("profile_" + old_profile).setAttribute("id", "profile_" + new_profile);
    edit_button = document.getElementById("edit_" + old_profile);
    remove_button = document.getElementById("remove_" + old_profile);
    edit_button.setAttribute("onclick", "edit_profile('" + new_profile + "')");
    edit_button.setAttribute("id", "edit_" + new_profile);
    remove_button.setAttribute("id", "remove_" + new_profile);
    remove_button.setAttribute("onclick", "remove_profile('" + new_profile + "')");
    
}

function remove_profile_confirm(profile) {
    if (Object.keys(profiles).length == 1) {
        document.getElementById("error").setAttribute("style", "");
    } else {
        document.getElementById("profile_" + profile).remove();
        if (profile == "1") {
            adding_to = "2";
        } else {
            adding_to = "1";
        }
        for (i = 0; i < profiles[profile]["fireworks"].length; i++) {
            profiles[adding_to]["fireworks"].push(profiles[profile]["fireworks"][i])
        }
        delete profiles[profile];
        for (i = 1; i < Object.keys(profiles).length+1; i++) {
            key = Object.keys(profiles)[i-1];
            change_profile_id(key, i);
            profile_data = profiles[key];
            delete profiles[key];
            console.log(profile_data)
            profiles[i.toString()] = profile_data;
        }
        socket.emit("update_fp", {"launcher": launcher, "profiles": profiles});
    }
}

document.getElementById("pwm_slider").addEventListener("input", (event) => {
    document.getElementById("pwm_slider_percentage").innerText = ((event.target.value/7500)*100).toFixed(2) + "%";
});
