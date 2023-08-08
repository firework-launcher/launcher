async function check_server() {
    request = await fetch(window.origin + "/ping");
    if (request.ok) {
        window.location.href = "/settings";
    }
}

setInterval(async function () { await check_server() }, 500);

fetch(window.origin + "/update_ready");