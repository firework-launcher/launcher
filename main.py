from flask import Flask, render_template, redirect, request, Response, make_response, jsonify, abort
import string
import threading
import time
import os
import flask_socketio
import sys
import json
import urllib.parse
import launcher_mgmt
import terminal_mgmt
import argparse
import logging
import subprocess
import copy
import socket
import random
import config_mgmt
import auto_discovery
import networkx as nx
from collections import deque

app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = {}
terminals = terminal_mgmt.Terminals()
config = config_mgmt.ConfigMGMT()
queue = {}
sequence_status = {}

config.load_file('firework_profiles.json')
config.load_file('sequences.json')
config.load_file('launchers.json')
config.load_file('drawflow_sequences.json')
config.load_file('labels.json')
config.load_file('branding.json', placeholder_data={'name': 'Firework Launcher'})

if not os.path.exists('config/branding.css'):
    open('config/branding.css', 'x').close()

update_filename = None

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

launcher_io = launcher_mgmt.LauncherIOMGMT(config, logging)
discovery = auto_discovery.AutoDiscovery(launcher_io, config)
threading.Thread(target=discovery.discover).start()

@app.route('/')
def home():
    """
    Path / for the webserver.
    """

    launchers_armed = {}
    for launcher in launcher_io.launchers:
        launchers_armed[launcher] = launcher_io.launchers[launcher].armed

    return render_template('home.html', 
        launchers=launcher_io.get_ports(),
        launchers_armed=launchers_armed,
        name=config.config['branding']['name']
    )

@app.route('/home/launcher_json_data')
def launcher_json_data():
    launcher_ports = []
    old_ports = launcher_io.get_ports()
    for launcher in old_ports:
        launcher_ports.append(old_ports[launcher])
    root = {
        'fireworks_launched': fireworks_launched,
        'firework_profiles': config.config['firework_profiles'],
        'launchers': launcher_ports,
        'labels': config.config['labels'],
        'sequences': config.config['sequences'],
        'drawflow_sequences': config.config['drawflow_sequences']
    }

    root['launcher_data'] = {
        'counts': {},
        'names': {},
        'armed': {},
        'channels_connected': {}
    }
    for launcher in launcher_io.launchers:
        root['launcher_data']['counts'][launcher] = launcher_io.launchers[launcher].count
        root['launcher_data']['names'][launcher] = launcher_io.launchers[launcher].name
        root['launcher_data']['armed'][launcher] = launcher_io.launchers[launcher].armed
        if not launcher_io.launchers[launcher].channels_connected == None:
            root['launcher_data']['channels_connected'][launcher] = launcher_io.launchers[launcher].channels_connected
    
    return jsonify(root)

@app.route('/branding.css')
def branding_css():
    if not os.path.exists('config/branding.css'):
        open('config/branding.css', 'x').close()
    f = open('config/branding.css')
    css = f.read()
    f.close()
    resp = make_response(css)
    resp.headers['Content-Type'] = 'text/css'
    return resp

@socketio.on("label_update")
def label_update(label_data):
    if not label_data['launcher'] in config.config['labels']:
        config.config['labels'][label_data['launcher']] = {}
    config.config['labels'][label_data['launcher']][str(label_data['firework'])] = label_data['label']
    config.save_config()
    socketio.emit('full_label_update', config.config['labels'])
    socketio.emit('label_update', label_data)

@app.route('/update_connected_channels')
def update_connected_channels():
    connected_channels = {}
    for launcher in launcher_io.launchers:
        if not launcher_io.launchers[launcher].channels_connected == None:
            connected_channels[launcher] = launcher_io.launchers[launcher].channels_connected
    socketio.emit('update_channels_connected', connected_channels)
    return 'OK'

@app.route('/settings/terminals')
def terminals_():
    """
    Path for managing terminals.
    """

    return render_template('settings/terminals/terminals.html', terminals=terminals.open_terminal_processes, name=config.config['branding']['name'], page='Terminals')

@app.route('/settings/terminals/add/<string:small_screen>')
def add_terminal(small_screen):
    """
    Generates a random port and creates a terminal session.
    """
    
    if small_screen == 'true':
        small_screen = True
    else:
        small_screen = False
    port = random.randrange(13000, 23000)
    terminals.create_terminal(port, small_screen)
    return redirect('/settings/terminals/sessions/{}'.format(port))

@socketio.on('remove_terminal')
def remove_terminal(port):
    """
    Removes a terminal.
    """

    terminals.delete_terminal(port)

@app.route('/settings/terminals/sessions/<string:port>')
def terminal_client(port):
    """
    Displays a terminal session
    """

    if not port in terminals.open_terminal_processes:
        abort(404)
    
    return render_template('settings/terminals/client.html', url='http://' + socket.gethostbyname(socket.gethostname()) + ':' + port + '/s/local/.', name=config.config['branding']['name'], page='Terminal')

@app.route('/settings/launchers')
def launcher_settings():
    """
    Path for adding and removing launchers.
    """

    if launcher_io.launchers == {}:
        return redirect('/settings/launchers/none')

    return render_template('settings/launchers/launchers.html', launchers=launcher_io.get_ports(), add_on_start=config.config['launchers'], urlencode=urllib.parse.quote, name=config.config['branding']['name'], page='Launchers')

@app.route('/settings/launchers/none')
def no_launchers():
    """
    Path for showing a message saying that
    there are no launchers
    """

    return render_template('settings/launchers/none.html', page='No Launchers', name=config.config['branding']['name'])

@app.route('/add_node_discover', methods=['POST'])
def add_node_discover():
    node = request.form['node']
    crashed = node in launcher_io.launchers
    if node in launcher_io.launchers:
        node_name = launcher_io.launchers[node].name
        remove_launcher(node)
        socketio.emit("node_crash_warning", [node, node_name])
    else:
        node_name = 'Node ' + node.split('.')[3]
    launcher_data = {
        'type': 'espnode',
        'name': node_name,
        'count': 16,
        'port':  node
    }
    launcher = node
    launcher_io.launcher_types[launcher_data['type']](launcher_io, launcher_data['name'], launcher, launcher_data['count'])

    fireworks_launched[launcher] = []
    if not launcher in config.config['firework_profiles']:
        config.config['firework_profiles'][launcher] = {'1': {'color': '#177bed', 'fireworks': list(range(1, launcher_data['count']+1)), 'name': 'One Shot', 'pwm': 1875}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot', 'pwm': 3750}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot', 'pwm': 5625}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale', 'pwm': 3750}}
    else:
        for channel in range(1, launcher_data['count']+1):
            found = False
            for profile in config.config['firework_profiles'][launcher]:
                if channel in config.config['firework_profiles'][launcher][profile]['fireworks']:
                    found = True
            if not found:
                for profile in config.config['firework_profiles'][launcher]:
                    break
                config.config['firework_profiles'][launcher][profile]['fireworks'].append(channel)
    config.save_config()
    threading.Thread(target=firework_serial_write, args=[launcher]).start()
    if not crashed:
        socketio.emit('add_node_discover', launcher_data)
    return 'OK'

@app.route('/settings/launchers/edit_fp/<path:launcher>')
def launcher_edit_fp(launcher):
    launcher = launcher[5:]
    if not launcher in launcher_io.launchers:
        abort(404)
    return render_template('settings/launchers/edit_fp.html',
        profilesjson=json.dumps(config.config['firework_profiles'][launcher]),
        profiles=config.config['firework_profiles'][launcher],
        launcher_port=launcher,
        launcher=launcher_io.launchers[launcher].name,
        name=config.config['branding']['name'],
        show_pwm=launcher_io.launchers[launcher].type == 'espnode',
        page='Edit Profiles',
    )

@app.route('/settings/launchers/edit_name/<path:launcher>', methods=['GET', 'POST'])
def launcher_edit_name(launcher):
    launcher = launcher[5:]
    if request.method == 'POST':
        launcher_io.launchers[launcher].name = request.form['name']
        return redirect('/settings/launchers')
    if not launcher in launcher_io.launchers:
        abort(404)
    return render_template('settings/launchers/edit_name.html', page='Change Name', name=config.config['branding']['name'], launcher_name=launcher_io.launchers[launcher].name)

@app.route('/settings/launchers/espnode_settings')
def espnode_settings_listing():
    nodes = []
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].type == 'espnode':
            nodes.append(launcher_io.launchers[launcher])
    return render_template('settings/launchers/node_settings/listing.html', page='Node Settings', name=config.config['branding']['name'], urlencode=urllib.parse.quote, nodes=nodes)

@app.route('/settings/launchers/espnode_settings/<path:node>')
def node_manage(node):
    if launcher_io.launchers == {}:
        return redirect('/settings/launchers/none')
    node = node[5:]
    if not node in launcher_io.launchers:
        abort(404)
    return render_template('settings/launchers/node_settings/manage.html', node=launcher_io.launchers[node], page='Manage Node - ' + launcher_io.launchers[node].name, name=config.config['branding']['name'])

@app.route('/settings/launchers/espnode_settings/<path:node>/reboot')
def node_reboot(node):
    node = node[5:]
    if not node in launcher_io.launchers:
        abort(404)
    node = launcher_io.launchers[node]
    node.reboot()
    return redirect(request.path[:-7])

@app.route('/settings/launchers/espnode_settings/<path:node>/wifi')
def node_wifi(node):
    node = node[5:]
    if not node in launcher_io.launchers:
        abort(404)
    node = launcher_io.launchers[node]
    if node.check_version_required(2):
        return redirect('http://{}'.format(node.port))
    node.enter_ota()
    remove_launcher(node.port)
    return redirect('http://{}'.format(node.port))

@app.route('/settings/launchers/espnode_settings/<path:node>/remove')
def node_remove(node):
    node = node[5:]
    if not node in launcher_io.launchers:
        abort(404)
    node = launcher_io.launchers[node]
    remove_launcher(node.port)
    return redirect('/settings/launchers/espnode_settings')

@socketio.on('update_fp')
def update_fp(data):
    launcher = data['launcher']
    profiles = data['profiles']
    config.config['firework_profiles'][launcher] = profiles
    config.save_config()

@socketio.on('launcher_addonstart')
def launcher_addonstart(launcher):
    """
    Adds or removes from the launchers config file.
    """

    if launcher in config.config['launchers']:
        del config.config['launchers'][launcher]
    else:
        config.config['launchers'][launcher] = {
            'name': launcher_io.launchers[launcher].name,
            'type': launcher_io.launchers[launcher].type,
            'count': launcher_io.launchers[launcher].count
        }
    
    config.save_config()

@socketio.on("arm")
def arm(launcher):
    """
    Arms a launcher
    """

    launcher_io.launchers[launcher].arm()
    socketio.emit('arm', launcher)

@socketio.on("disarm")
def disarm(launcher):
    """
    Disarms a launcher
    """
    
    launcher_io.launchers[launcher].disarm()
    socketio.emit('disarm', launcher)

@socketio.on('remove_launcher')
def remove_launcher(launcher):
    """
    Removes a launcher.
    """
    
    launcher_io.launchers[launcher].remove()
    del launcher_io.launchers[launcher]

@app.route('/sequence_status/<string:sequence>')
def sequence_status_checker(sequence):
    if sequence in sequence_status:
        response = {'running': sequence_status[sequence], 'error': False}
        if response['running']:
            response.update(launcher_io.running_sequence_data[sequence])
        if response['error'] == 'failed':
            logging.error('sequence "{}" failed to run'.format(sequence))
            sequence_status[sequence] = False
            return jsonify({'error': 'failed', 'next_step_in': 0, 'step': 'Failed'})
        elif response['error'] == 'notadded':
            logging.error('sequence "{}" tried to run with launchers not added'.format(sequence))
            sequence_status[sequence] = False
            return jsonify({'error': 'notadded', 'next_step_in': 0, 'step': 'Failed'})
        elif response['error'] == 'unarmed':
            logging.error('sequence "{}" tried to run with launchers unarmed'.format(sequence))
            sequence_status[sequence] = False
            return jsonify({'error': 'unarmed', 'next_step_in': 0, 'step': 'Failed'})
        else:
            del response['error']
        
        response['next_step_in'] = launcher_io.running_sequence_data[sequence]['next_step_epoch_est'] - int(time.time())
        return jsonify(response)
    else:
        return jsonify({'running': False})

@app.route('/sequences')
def sequences_():
    """
    Path that shows the page for viewing and managing
    sequences
    """

    return render_template('sequences/sequences.html', sequences=config.config['sequences'], name=config.config['branding']['name'], page='Sequences')

@app.route('/sequences/builder', methods=['GET', 'POST'])
def sequence_builder():
    """
    Path for the new sequence builder using drawflow.
    """

    if request.method == 'POST':
        sequence_name = request.form['sequence_name']
        sequence_data = json.loads(request.form['sequence_data'])
        config.config['sequences'][sequence_name] = sequence_data
        config.save_config()
        return redirect('/sequences')

    launcher_counts = {}
    launchers = {}
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].sequences_supported:
            launchers[launcher] = launcher_io.launchers[launcher].name
            launcher_counts[launcher] = launcher_io.launchers[launcher].count
    
    if launchers == {}:
        return redirect('/settings/launchers/none')

    return render_template('sequences/builder.html', launchers=launchers, name=config.config['branding']['name'], page='Sequence Builder')

@app.route('/sequences/edit/<string:sequence>', methods=['GET', 'POST'])
def sequence_edit(sequence):
    """
    Path to edit a sequence.
    """

    if request.method == 'POST':
        sequence_name = request.form['sequence_name']
        sequence_data = json.loads(request.form['sequence_data'])
        config.config['sequences'][sequence_name] = sequence_data
        config.save_config()
        return redirect('/sequences')

    launcher_counts = {}
    launchers = {}
    for launcher in launcher_io.launchers:
        if launcher_io.launchers[launcher].sequences_supported:
            launchers[launcher] = launcher_io.launchers[launcher].name
            launcher_counts[launcher] = launcher_io.launchers[launcher].count
    
    if launchers == {}:
        return redirect('/settings/launchers/none')

    return render_template('sequences/builder.html', launchers=launchers, name=config.config['branding']['name'], page='Sequence Builder', edit=True, sequence=sequence)

@app.route('/sequences/visualize/<string:sequence>')
def sequence_visualize(sequence):
    """
    Path to visualize a sequence.
    """

    return render_template('sequences/visualize.html', page='Sequence Visualizer - ' + sequence, name=config.config['branding']['name'], sequence_name=sequence)

def secure_filename(filename):
    """
    Replacement for werkzeug.secure_filename()
    since I was having trouble trying to get it
    working. This works fine.
    """

    allowed_characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + '-.'
    new_filename = []
    for x in filename:
        if not x in allowed_characters:
            new_filename.append('_')
        else:
            new_filename.append(x)
    return ''.join(new_filename)

@app.route('/settings')
def settings():
    """
    Settings menu path
    """

    return render_template('settings/settings.html', name=config.config['branding']['name'], page='Settings')

@app.route('/settings/update', methods=['POST'])
def settings_update():
    """
    Saves files uploaded and prepares to update
    using the uploaded file.
    """

    update_file = request.files['update']
    filename = secure_filename(update_file.filename)
    update_file.save(filename)
    global update_filename
    update_filename = filename
    return render_template('settings/update/wait_for_update.html', name=config.config['branding']['name'], page='Updating')

@app.route('/update_ready')
def update_ready():
    """
    The wait for update page makes a request
    here to show that the wait for update page
    is loaded and it can shut down the webserver
    for updating.
    """

    if not update_filename == None:
        subprocess.Popen([sys.executable, 'update.py', update_filename, str(os.getpid())])
    else:
        abort(400)

@app.route('/ping')
def ping():
    """
    Used by the wait for update page to see
    if the webserver is up.
    """

    return 'Pong'

@socketio.on('save_fp')
def save_fp(firework_profiles):
    """
    Writes to the firework_profiles.json file new data
    from the client.
    """

    config.config['firework_profiles'] = firework_profiles
    socketio.emit('fp_update', firework_profiles);
    config.save_config()

@socketio.on('run_sequence')
def run_sequence(sequence):
    """
    Runs a sequence, this is called from SocketIO,
    /static/js/sequences.js.
    """

    socketio.emit('running_sequence', sequence)
    sequence_status[sequence] = True
    threading.Thread(target=run_sequence_threaded, args=[sequence]).start()

def parse_drawflow_export(save_data, name):
    data = {
        'nodes': [],
        'connections': [],
        'name': name
    }
    for node in save_data:
        node = save_data[node]
        data['nodes'].append({
            'id': node['id'],
            'name': node['name'],
            'data': node['data']
        })
        if 'output_1' in node['outputs']:
            for connection in node['outputs']['output_1']['connections']:
                data['connections'].append([node['id'], int(connection['node'])])
    return data


def validate_full_path(G, data):
    """
    Validates that nodes either have a path to
    both the start and end nodes, or they have
    no path.
    """

    for node in data['nodes']:
        id = node['id']
        if node['name'] not in ['start', 'end']:
            path_to_start = False
            path_to_end = False
            try:
                path_to_start = nx.has_path(G, 1, id)
            except nx.NodeNotFound:
                pass
            try:
                path_to_end = nx.has_path(G, id, 2)
            except nx.NodeNotFound:
                pass
            if path_to_start != path_to_end:
                return False
    return True


def find_all_paths(data):
    G = nx.DiGraph()
    G.add_nodes_from([node['id'] for node in data['nodes']])
    G.add_edges_from(data['connections'])
    start_node = [node["id"] for node in data["nodes"] if node["name"] == "start"][0]
    end_node = [node["id"] for node in data["nodes"] if node["name"] == "end"][0]
    all_paths = list(nx.all_simple_paths(G, start_node, end_node))
    return all_paths

def parse_sequence(data):
    paths = find_all_paths(data)
    getNodeFromId = lambda id, data: next((node for node in data['nodes'] if node['id'] == id), None)

    steps = {}
    delay_times = []
    for path in paths:
        current_time = 0
        for node in path:
            node_data = getNodeFromId(node, data)
            if node_data['name'] == 'delay':
                current_time += node_data['data']['delay']
            elif node_data['name'] == 'launch':
                if not str(current_time) in steps:
                    steps[str(current_time)] = []
                    delay_times.append(current_time)
                if not node in steps[str(current_time)]:
                    steps[str(current_time)].append(node)
    new_steps = {
        data['name']: {}
    }
    x = 1

    for step in steps:
        new_steps[data['name']]['Step {}'.format(x)] = {}
        new_steps[data['name']]['Step {}'.format(x)]['pins'] = {}
        for node in steps[step]:
            node_data = getNodeFromId(node, data)
            if not node_data['data']['launcher'] in new_steps[data['name']]['Step {}'.format(x)]['pins']:
                new_steps[data['name']]['Step {}'.format(x)]['pins'][node_data['data']['launcher']] = []
            new_steps[data['name']]['Step {}'.format(x)]['pins'][node_data['data']['launcher']].append(node_data['data']['firework'])
            if len(delay_times) == x:
                delay = 1
            else:
                delay = delay_times[x]-delay_times[x-1]
            new_steps[data['name']]['Step {}'.format(x)]['delay'] = delay
        x += 1
    return new_steps

@socketio.on('sequencebuilder_save')
def sequencebuilder_save(save_data):
    """
    Interprets drawflow's export data to build
    the sequence.
    """

    socketio_id = copy.copy(save_data['socketio_id'])
    name = copy.copy(save_data['name'])
    original_save_data = copy.copy(save_data)
    del original_save_data['socketio_id']
    del original_save_data['name']
    save_data = save_data['drawflow']['Home']['data']
    data = parse_drawflow_export(save_data, name)
    getNodeFromId = lambda id, data: next((node for node in data['nodes'] if node['id'] == id), None)
    startNodeId = None
    endNodeId = None
    for node in data['nodes']:
        if node['name'] == 'start':
            startNodeId = node['id']
        elif node['name'] == 'end':
            endNodeId = node['id']
    G = nx.DiGraph()
    G.add_edges_from(data['connections'])

    if not validate_full_path(G, data):
        socketio.emit(socketio_id + '_save', {
            'success': False,
            'error': 'Some blocks have an incomplete path from start to end.'
        })
        return
    for node in data['nodes']:
        if node['name'] == 'launch':
            if node['data']['launcher'] == None:
                socketio.emit(socketio_id + '_save', {
                    'success': False,
                    'error': 'One or more launch blocks do not have a firework selected.'
                })
                return
    sequence_data = parse_sequence(data)

    config.config['sequences'][name] = copy.copy(sequence_data[name])
    config.config['drawflow_sequences'][name] = original_save_data
    config.save_config()

    socketio.emit(socketio_id + '_save', {
        'success': True
    })

def run_sequence_threaded(sequence):
    """
    Thread run_sequence() starts. This is a thread
    because it has delays and interrupts the flask
    app.
    """

    if not sequence in config.config['sequences']:
        return None
    sequence_data = config.config['sequences'][sequence]
    pins_changed = []
    for step in sequence_data:
        launchers_added = True
        for launcher in sequence_data[step]['pins']:
            if not launcher in launcher_io.launchers:
                launchers_added = False
                break
            pins_changed.append([launcher, sequence_data[step]['pins'][launcher]])
    if not launchers_added:
        launcher_io.running_sequence_data[sequence] = {'error': 'notadded', 'next_step_epoch_est': 0}
    else:
        global fireworks_launched
        for pin in pins_changed:
            fireworks_launched[pin[0]] += pin[1]
        launcher_io.run_sequence(sequence, sequence_data)
        if not launcher_io.running_sequence_data[sequence]['error']:
            sequence_status[sequence] = False

@socketio.on('delete_sequence')
def delete_sequence(sequence):
    """
    Deletes a sequence, called from the sequences
    js file.
    """

    if not sequence in config.config['sequences']:
        return None
    del config.config['sequences'][sequence]
    config.save_config()

@socketio.on('delete_label')
def delete_label(label):
    """
    Deletes a label, called from the labels
    js file.
    """

    launcher = label.split('_')[0]
    firework = label.split('_')[1]
    if launcher in config.config['labels']:
        if firework in config.config['labels'][launcher]:
            exists = True
    if not exists:
        return None
    
    del config.config['labels'][launcher][firework]
    config.save_config()
    socketio.emit('full_label_update', config.config['labels'])
    socketio.emit('delete_label', {
        'launcher': launcher,
        'firework': firework
    })

@socketio.on('stop_sequence')
def stop_sequence(sequence):
    """
    Stops a sequence
    """

    launcher_io.running_sequence_data[sequence]['stop'] = True
    launcher_io.running_sequence_data[sequence]['running'] = False

@app.before_request
def beforerequest():
    """
    Redirects anyone who is not in a private network to
    Rick Astley - Never Gonna Give You Up. This also
    redirects anyone not logged in to the login page
    if they are on a private network.
    """
    if request.path == '/add_node_discover' and request.remote_addr.startswith('127.'):
        pass
    else:
        if not request.path == '/update_connected_channels':
            if not request.remote_addr.startswith('192.168.') and not request.remote_addr.startswith('172.16.') and not request.remote_addr.startswith('10.') and not request.remote_addr.startswith('127.'):
                return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            else:
                if not request.path.startswith('/static') and not request.path == '/home/launcher_json_data':

                    if launcher_io.launchers == {} and not request.path.startswith('/settings'):
                        return redirect('/settings/launchers/none')

def firework_serial_write(launcher):
    """
    This is the queue thread. There is a seperate queue for
    each launcher.
    """

    global queue
    queue[launcher] = []
    logging.info('Serial Proccessing Thread Starting for launcher {}...'.format(launcher))
    queue_for_thread = []
    while True:
        try:
            if not launcher in launcher_io.launchers:
                break
            i = 0
            for pin in queue[launcher]:
                launcher_io.trigger_firework(launcher, int(pin))
                del queue[launcher][i]
                i = i + 1
                logging.info('{} Queue update: {}'.format(launcher, queue))
        except Exception as e:
            logging.error('Recieved error from queue {}: {}: {}'.format(launcher, type(e).__name__, str(e)))
            queue[launcher] = []
            logging.debug('Due to the previous error, launcher\'s queue was completely cleared')
        time.sleep(0.01)

@socketio.on("launch_firework")
def trigger_firework(data):
    """
    This is ran when a firework is launched using SocketIO
    from /static/js/main.js. It adds to a dictionary that
    the queue thread reads.
    """

    firework = data['firework']
    ports = launcher_io.get_ports()
    launcher = data['launcher']
    armed = launcher_io.launchers[launcher].armed
    if armed:
        global fireworks_launched
        fireworks_launched[launcher].append(firework)
        global queue
        queue[launcher].append(firework)
        socketio.emit('firework_launch', {'firework': firework, 'launcher': launcher})

@socketio.on("firenow")
def firenow(sequence):
    """
    Skips delays in sequence for if a firework ends
    earlier than expected.
    """

    launcher_io.running_sequence_data[sequence]['firenow'] = True

def reset_queue():
    """
    This fully clears the queue.
    """
    for launcher in queue:
        queue[launcher] = []

def reset_launcher(launcher):
    """
    This resets a launcher.
    """

    global fireworks_launched
    fireworks_launched[launcher] = []
    reset_queue()

@socketio.on('exec_reset')
def reset(data):
    """
    Function called when a launcher is reset from
    SocketIO.
    """

    reset_launcher(data['launcher'])
    socketio.emit('reset', data)

@socketio.on('reset_all')
def reset_all():
    """
    Resets all launchers.
    """
    
    for launcher in fireworks_launched:
        reset_launcher(launcher)
    socketio.emit('reset_all')

@socketio.on('arm_all')
def arm_all():
    """
    Arms all launchers.
    """
    
    for launcher in launcher_io.launchers:
        arm(launcher)
    
@socketio.on('disarm_all')
def disarm_all():
    """
    Disarms all launchers.
    """
    
    for launcher in launcher_io.launchers:
        disarm(launcher)

if __name__ == '__main__':
    for launcher in config.config['launchers']:
        launcher_data = config.config['launchers'][launcher]
        launcher_io.launcher_types[launcher_data['type']](launcher_io, launcher_data['name'], launcher, launcher_data['count'])

        fireworks_launched[launcher] = []
        if not launcher in config.config['firework_profiles']:
            config.config['firework_profiles'][launcher] = {'1': {'color': '#177bed', 'fireworks': list(range(1, launcher_data['count']+1)), 'name': 'One Shot', 'pwm': 1875}, '2': {'color': '#5df482', 'fireworks': [], 'name': 'Two Shot', 'pwm': 3750}, '3': {'color': '#f4ff5e', 'fireworks': [], 'name': 'Three Shot', 'pwm': 5625}, '4': {'color': '#ff2667', 'fireworks': [], 'name': 'Finale', 'pwm': 3750}}
        else:
            for channel in range(1, launcher_data['count']+1):
                found = False
                for profile in config.config['firework_profiles'][launcher]:
                    if channel in config.config['firework_profiles'][launcher][profile]['fireworks']:
                        found = True
                if not found:
                    for profile in config.config['firework_profiles'][launcher]:
                        break
                    config.config['firework_profiles'][launcher][profile]['fireworks'].append(channel)
        config.save_config()
        threading.Thread(target=firework_serial_write, args=[launcher]).start()

    socketio.run(app, host='0.0.0.0', port=80)
