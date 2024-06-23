const { reactive, createApp } = Vue

var root_noreact = {};

async function fetch_variables(script) {
    response = await fetch(window.origin + "/home/launcher_json_data");
    root_noreact = await response.json();
    root = reactive(root_noreact)
    main_script = document.createElement("script");
    main_script.setAttribute("src", script);
    setTimeout(function() {
        document.body.appendChild(main_script);
    }, 50);
}
