var root = {};
async function fetch_variables(script) {
    response = await fetch(window.origin + "/home/launcher_json_data");
    root = await response.json();
    main_script = document.createElement("script");
    main_script.setAttribute("src", script);
    setTimeout(function() {
        document.body.appendChild(main_script);
    }, 50);
}
