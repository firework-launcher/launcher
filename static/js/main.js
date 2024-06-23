const socket = io();

function firework_launch(launcher, firework) {
    if (root.fireworks_launched[launcher] != undefined) {
        root.fireworks_launched[launcher].push(firework);
        console.log("New firework launched. Launcher: " + launcher + " Firework: " + firework);
    }
}

socket.on("disconnect", () => {
    console.log("Lost Connection");
});

socket.on("firework_launch", (data) => {
    firework_launch(data.launcher, data.firework);
});

socket.on("arm", (launcher) => {
    root.launcher_data.armed[launcher] = true;
});

socket.on("disarm", (launcher) => {
    root.launcher_data.armed[launcher] = false;
});

socket.on("reset", (data) => {
    root.fireworks_launched[data.launcher] = [];
});

socket.on("update_channels_connected", (channels_connected) => {
    root.launcher_data.channels_connected = channels_connected;
});

app = createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            root: root
        }
    },
    methods: {
        arm_toggle(event) {
            launcher = event.target.parentElement.parentElement.parentElement.id;
            if (root.launcher_data.armed[launcher]) {
                socket.emit("disarm", launcher);
            } else{
                socket.emit("arm", launcher);
            }
        },
        reset(launcher) {
            socket.emit("exec_reset", {"launcher": launcher})
        },
        button_clicked(launcher, firework) {
            socket.emit("launch_firework", {
                firework: firework,
                launcher: launcher
            });
        }
    }
});

app.mount("#app");
