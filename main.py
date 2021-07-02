from flask import Flask, render_template, redirect, request, Response, make_response
import uuid
import threading
import time
import os
import serial
app = Flask(__name__)
col_num = {}
fireworks_launched = []
queue = []
did_reset = False
if_reset = False
def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    return rv

ser = serial.Serial('/dev/ttyACM0', 115200)
def add_col(site_id):
    global col_num
    col_num[site_id] = col_num[site_id] + 1
    return col_num[site_id]

def col(site_id):
    return col_num[site_id]

def get_class_name(site_id):
    if str(col_num[site_id]) in fireworks_launched:
        return 'danger'
    else:
        return 'primary'

def get_href(site_id):
    if str(col_num[site_id]) in fireworks_launched:
        return '#'
    else:
        return '/trigger_firework/{}'.format(col_num[site_id])

    

def ifnot_col_33(site_id):
    if col_num[site_id] == 32:
        return False
    else:
        return True

def get_if_reset():
    global if_reset
    if if_reset == True:
        return True
    else:
        return False

@app.route('/')
def home():
    global did_reset
    cookies = dict(request.cookies)
    print(cookies)
    if 'admin' in cookies:
        pass
    else:
        cookies['admin'] = 'false'

    if 'dark_mode' in cookies:
        pass
    else:
        cookies['dark_mode'] = 'false'
    
    def g():
        while True:
            time.sleep(0.1)
            global fireworks_launched
            yield fireworks_launched
    site_id = str(uuid.uuid4())
    col_num[site_id] = 0
    if cookies['dark_mode'] == 'true':
        if cookies['admin'] == 'true':
            return Response(stream_template('home.html', add_col=add_col, col=col, site_id=site_id, ifnot_col_33=ifnot_col_33, data=g(), did_reset=False, get_if_reset=get_if_reset, has_admin=True, get_class_name=get_class_name, get_href=get_href, darkmode=True))
        else:
            return Response(stream_template('home.html', add_col=add_col, col=col, site_id=site_id, ifnot_col_33=ifnot_col_33, data=g(), did_reset=False, get_if_reset=get_if_reset, has_admin=False, get_class_name=get_class_name, get_href=get_href, darkmode=True))
    else:
        if cookies['admin'] == 'true':
            return Response(stream_template('home.html', add_col=add_col, col=col, site_id=site_id, ifnot_col_33=ifnot_col_33, data=g(), did_reset=False, get_if_reset=get_if_reset, has_admin=True, get_class_name=get_class_name, get_href=get_href, darkmode=False))
        else:
            return Response(stream_template('home.html', add_col=add_col, col=col, site_id=site_id, ifnot_col_33=ifnot_col_33, data=g(), did_reset=False, get_if_reset=get_if_reset, has_admin=False, get_class_name=get_class_name, get_href=get_href, darkmode=False))
@app.route('/get_admin')
def admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'true')
    return resp

@app.route('/dark_mode')
def darkmode():
    resp = make_response(redirect('/'))
    resp.set_cookie('dark_mode', 'true')
    return resp

@app.route('/light_mode')
def darkmode():
    resp = make_response(redirect('/'))
    resp.set_cookie('dark_mode', 'false')
    return resp

@app.route('/remove_admin')
def remove_admin():
    resp = make_response(redirect('/'))
    resp.set_cookie('admin', 'false')
    return resp

@app.before_request
def rickastley():
    if not request.remote_addr == '192.168.3.1':
        return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

def firework_serial_write():
    global queue
    global queue_reset_inprogress
    print('Serial Proccessing Thread Starting...')
    while True:
        try:
            i = 0
            for pin in queue:
                ser.write('/digital/{}/0\r\n'.format(pin).encode())
                data = ser.read()
                time.sleep(0.5)
                data_left = ser.inWaiting()
                data += ser.read(data_left)
                print(data)
                time.sleep(0.5)
                ser.write('/digital/{}/1\r\n'.format(pin).encode())
                data = ser.read()
                time.sleep(0.5)
                data_left = ser.inWaiting()
                data += ser.read(data_left)
                print(data)
                del queue[i]
                i = i + 1
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
    app.run(host='0.0.0.0', port=80)
