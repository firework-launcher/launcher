var id = document.getElementById("drawflow");
const editor = new Drawflow(id);
editor.editor_mode = 'edit';
editor.start();

function addNodeToDrawFlow(name) {
    if(editor.editor_mode === 'fixed') {
        return false;
    }

    switch (name) {
        case 'launch':
            var launch = `
            <div>
            <div class="title-box" onclick="openmodal('launchmodal')">Launch Firework</div>
            </div>
            `;
            editor.addNode('launch', 1,  1, 50, 50, 'launch', {}, launch );
            break;
        case 'delay':
            var delay = `
            <div>
            <div class="title-box">Delay</div>
            </div>
            `;
            editor.addNode('delay', 1,  1, 50, 50, 'delay', {}, delay );
            break;
        case 'start':
            var start = `
            <div>
            <div class="title-box">Start of sequence</div>
            </div>
            `;
            editor.addNode('start', 0,  1, 50, 50, 'start', {}, start );
            break;
        case 'end':
            var end = `
            <div>
            <div class="title-box">End of sequence</div>
            </div>
            `;
            editor.addNode('end', 1,  0, 50, 150, 'end', {}, end );
            break;
        default:
    }
}

addNodeToDrawFlow('start');
addNodeToDrawFlow('end');

function close_modal(modal) {
    modal = document.getElementById(modal);
    modal.style.display = "none";
    editor.editor_mode = "edit";
}

function openmodal(modal) {
    modal = document.getElementById(modal);
    modal.style.display = "block";
    editor.editor_mode = "fixed";
}
