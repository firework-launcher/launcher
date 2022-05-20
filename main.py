from flask import Flask, render_template, redirect, request, Response, make_response
import uuid
import threading
import time
import os
import flask_socketio
from serial import Serial
app = Flask(__name__)
socketio = flask_socketio.SocketIO(app)
fireworks_launched = []
queue = []
did_reset = False
if_reset = False

# ser = Serial('/dev/ttyACM0', 115200)
def get_theme_link(theme):
    return '/static/themes/' + theme

@app.route('/')
def home():
    global did_reset
    cookies = dict(request.cookies)
    print(cookies)
    if 'admin' in cookies:
        pass
    else:
        cookies['admin'] = 'false'
    if 'theme' in cookies:
        pass
    else:
        cookies['theme'] = 'light.css'
    if cookies['theme'] == 'dark.css' or cookies['theme'] == 'dark_red.css':
        darkmode = True
    else:
        darkmode = False
    if cookies['admin'] == 'true':
        return render_template('home.html', has_admin=True, theme=cookies['theme'], get_theme_link=get_theme_link, darkmode=darkmode)
    else:
        return render_template('home.html', has_admin=False, theme=cookies['theme'], get_theme_link=get_theme_link, darkmode=darkmode)

@app.route('/get_admin')
def admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'true')
    return resp

@app.route('/theme/<string:theme>')
def select_theme(theme):
    resp = make_response(redirect('/'))
    resp.set_cookie('theme', theme)
    return resp

@app.route('/themes')
def themes():
    cookies = dict(request.cookies)
    if 'theme' in cookies:
        pass
    else:
        cookies['theme'] = 'light.css'
    if cookies['theme'] == 'dark.css' or cookies['theme'] == 'dark_red.css':
        darkmode = True
    else:
        darkmode = False
    return render_template('themes.html', theme=cookies['theme'], get_theme_link=get_theme_link, darkmode=darkmode)

@app.route('/remove_admin')
def remove_admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'false')
    return resp

# @app.before_request
# def rickastley():
#    if not request.remote_addr == '192.168.3.1':
#        return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

def firework_serial_write():
    global queue
    global queue_reset_inprogress
    print('Serial Proccessing Thread Starting...')
    while True:
        try:
            i = 0
            for pin in queue:
                #ser.write('/digital/{}/0\r\n'.format(pin).encode())
                #data = ser.read()
                #time.sleep(0.5)
                #data_left = ser.inWaiting()
                #data += ser.read(data_left)
                #print(data)
                #time.sleep(0.5)
                #ser.write('/digital/{}/1\r\n'.format(pin).encode())
                #data = ser.read()
                #time.sleep(0.5)
                #data_left = ser.inWaiting()
                #data += ser.read(data_left)
                #print(data)
                #del queue[i]
                #i = i + 1
                print(queue)
        except:
            pass

@app.route('/trigger_firework/<string:firework>')
def trigger_firework(firework):
    global fireworks_launched
    fireworks_launched.append(firework)
    pin = str(int(firework)+2)
    global queue
    queue.append(pin)
    return redirect('/')

@app.route('/reset')
def reset():
    global queue
    global fireworks_launched
    global if_reset
    fireworks_launched = []
    queue = []
    if_reset = True
    time.sleep(1)
    if_reset = False
    return redirect('/')

if __name__ == '__main__':
    threading.Thread(target=firework_serial_write).start()
    socketio.run(app, host='0.0.0.0', port=80)
