var root = {};
async function fetch_variables(script) {
    response = await fetch(window.origin + "/home/launcher_json_data");
    root = await response.json();
    socketio_script = document.createElement("script");
    main_script = document.createElement("script");
    socketio_script.setAttribute("src", "/static/js/socketio.js");
    main_script.setAttribute("src", script);
    document.body.appendChild(socketio_script);
    setTimeout(function() {
        document.body.appendChild(main_script);
    }, 50);
}
