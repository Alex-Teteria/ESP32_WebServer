''' Вебсервер на ESP32
    V0.16 26.09.2023
'''
import network, machine, time, sys, hashlib, random
from machine import I2C
import read_key
import dht
from bmp280 import *
import socket

#initialization led & button & input sensor
led = machine.Pin(2, machine.Pin.OUT)
relay_1 = machine.Pin(32, machine.Pin.OUT)
relay_2 = machine.Pin(33, machine.Pin.OUT)
l_relay = [relay_1, relay_2]
button_reset = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
sens_dht = dht.DHT22(machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP))
bus = I2C(scl=machine.Pin(22),sda=machine.Pin(21), freq=100000)
bmp = BMP280(bus)
bmp.use_case(BMP280_CASE_WEATHER)
uart = machine.UART(2,9600)
rtc = machine.RTC()

def create_accesspoint(ssid, password, ipinfo):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password, authmode=3)
    if ipinfo:
        ap.ifconfig(ipinfo)
    while ap.active() == False:
        pass
    print('Access point ready!')
    return ap

def connect(ssid, passwd):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    wlan.connect(ssid, passwd)
    while not wlan.isconnected():
        pass
    return wlan

def create_wlan():
    if not button_reset.value():
        ssid = 'ESP-32'
        password = '12345678'
        ipinfo = ('192.168.8.2', '255.255.255.0', '192.168.8.1', '8.8.8.8')
        with open('passwd.txt', 'w', encoding='utf-8') as out_file:
            print(password, file=out_file)
        return create_accesspoint(ssid, password, ipinfo)
    with open('config.txt', 'r') as config:
        d_config = {}
        for line in config:
            key, val = line.rstrip().split(':')
            d_config[key] = val
    if d_config['ap_mode']:
        ipinfo = (d_config['ip'], d_config['subnet_mask'], d_config['gw'], d_config['dns'])
        wlan = create_accesspoint(d_config['ssid'], d_config['password'], ipinfo)
    else:
        wlan = connect(d_config['wlan_id'], d_config['wlan_pass'])
    print(wlan.ifconfig())
    return wlan

def send_anything(foo_send):
    '''
    Декоратор - відсилає дані (content), які вертає функція на сокет sock,
    якщо помилка, то апаратний перезапуск контролера
    Функція при цьому приймає та вертає обов'язковий параметр sock (примірник об'єкта сокета,
    з яким іде обмін по http)
    '''
    def f(sock, *args):
        content, sock = foo_send(sock, *args)
        try:
            sock.sendall(content)
        except (OSError):
            print('Error!!!')
            machine.reset()
    return f

@send_anything
def send_login(sock, path, method, *args):
    global flag_login, random_str, attempt_cnt
    d_body = {'text': '', 'passwd': '0'}
    if method == 'POST':
        d_body = get_body(str(sock.recv(4096), "utf8"), d_body)
        print(d_body['passwd'], random_str)
        
        with open('passwd.txt', 'r') as passwd_file:
            passwd = passwd_file.readline().rstrip()
        result = hashlib.sha256(passwd + random_str)
        passwd_hash = result.digest().hex()
        print(passwd_hash)
        if passwd_hash == d_body['passwd']:
            flag_login = True
            attempt_cnt = 3
            with open('html/menu.html', 'r') as in_file:
                content = in_file.read() % ''
        else:
            flag_login = False
            attempt_cnt -= 1
            if not attempt_cnt:
                with open('html/login_later.html', 'r') as in_file:
                    content = in_file.read()
                return content , sock
            with open('html/false_login.html', 'r') as in_file:
                content = in_file.read() % str(attempt_cnt)
        return content , sock
    else:
        with open('html/login.html', 'r') as in_file:
            content = in_file.read()
        random_str = random_string(8)
        in_tuple = ('%', '%', random_str)
        return content % in_tuple, sock
    
@send_anything
def send_main_menu(*args):
    sock, path, *anything, params = args
    if path == '/send_time.html':
        uart.write('AT&time;' + params + '\r\n')
    with open('html/menu.html', 'r') as in_file:
        content = in_file.read()
    return content % 'checked', sock

@send_anything
def send_main_config(*args):
    sock, *anything = args
    with open('html/config_main.html', 'r') as in_file:
        content = in_file.read()
    return content, sock

@send_anything
def password_change(sock, path, method, *args):
    global d, n
    d_body = {'text': '', 'passwd': '0', 'new_passwd': '0'}
    if method == 'POST':
        d_body = get_body(str(sock.recv(4096), "utf8"), d_body)
        print(d_body['new_passwd'])
        dec_num = pow(int(d_body['new_passwd']), int(d), int(n))
        bytes_val = (dec_num // 100).to_bytes(dec_num % 100, 'little')
        dec_str = bytes_val.decode()
        with open('passwd.txt', 'w', encoding='utf-8') as out_file:
            print(dec_str, file=out_file)
        global flag_login
        flag_login = False
        with open('html/logout.html', 'r') as in_file:
            content = in_file.read()
        return content, sock
    else:
        e, d, n = read_key.get_key()
        with open('html/password_change.html', 'r') as in_file:
            content = in_file.read()
        in_tuple = (e + 'n',
                    n + 'n',
                   '%', '%', '%')
        return content % in_tuple, sock

@send_anything
def send_logout(sock, *args):
    global flag_login
    flag_login = False
    with open('html/logout.html', 'r') as in_file:
        content = in_file.read()
    return content, sock

@send_anything
def send_css(sock, path, *args):
    d_css = {'/menu.css': 'html/menu.css', '/button.css': 'html/button.css',
             '/sens_status.css': 'html/sens_status.css'}
    file = d_css[path] if path in d_css else 'html/menu.css'
    with open(file, 'rb') as in_file:
        return in_file.read(), sock
    
@send_anything
def send_sens_status(sock, path, *args):
    sens_tem, sens_hum = '???', '???'
    pressure = bmp.pressure
    if path == '/sens_to_led.html':
        uart.write('AT&dht_to_neo' + '\r\n')
    else:
        uart.write('AT&environment' + '\r\n')
    if uart.any():
        try:
            sens_tem, sens_hum, *tail = str(uart.read(), 'UTF-8').rstrip().split(';')
        except UnicodeError:
            sens_tem, sens_hum = '???', '???'
    s_hum = 'Humidity: ' + sens_hum + ' %'
    s_temper = 'Temperature: ' + sens_tem + '&degC'
    p_mmHg = 'Pressure: ' + str(round(pressure / 133.3224)) + ' mmHg'
    with open('html/sens_status.html', 'r') as in_file:
        sens_status = in_file.read()
    in_html = (s_temper, s_hum, p_mmHg, 'div-Off')
    return sens_status % in_html, sock

@send_anything
def send_image(sock, path, *args):
    d_image = {'/favicon': 'html/favicon.png', '/relay_on.jpg': 'html/relay_on.gif',
               '/relay_off.jpg': 'html/relay_off.gif', '/relay_off_mov.jpg': 'html/relay_off_mov.gif',
               '/relay_on_mov.jpg': 'html/relay_on_mov.gif'}
    file = d_image[path] if path in d_image else 'html/favicon.png'
    with open(file, 'rb') as in_file:
        return in_file.read(), sock    
        
@send_anything
def send_send_text(sock, path, method, *args):
    d_body = {'text': '', 'passwd': ''}
    if path == '/stop_run_text.html':
        uart.write('stoprun' + '\r\n')
    if method == 'POST':
        d_body = get_body(str(sock.recv(4096), "utf8"), d_body)
#        print(d_body['text'])
        if d_body['text'] != 'AT%26environment':
            uart.write(d_body['text'])
    with open('html/send_text.html', 'r') as in_file:
        return in_file.read(), sock    

@send_anything
def dev_manager(*args):
    '''
    Змінює значення виходу relay_1 або relay_2 на протилежне в залежності від значення параметру
    (якщо параметр 'dev1', то інвертується вихід relay_1, якщо 'dev2', то relay_2)
    Зчитує файл 'html/dev_manager.html' та добавляє в нього рядки 'On', 'On', 'relay_on.jpg'
    або 'Off', 'Off', 'relay_off.jpg' в залежності від стану виходів на реле ("1" чи "0")
    Вертає рядок формату html та примірник об'єкта сокета
    '''
    sock, *tail, params = args
    d_relay = {'dev1': relay_1, 'dev2': relay_2}
    if params:
        d_relay[params].value(not d_relay[params].value())
    rel_on = 'On', 'On', 'relay_on.jpg'
    rel_on_mov = 'On', 'On', 'relay_on_mov.jpg'
    rel_off = 'Off', 'Off', 'relay_off.jpg'
    rel_off_mov = 'Off', 'Off', 'relay_off_mov.jpg'
    
    l_content = []
    for relay in l_relay:
        if params and relay == d_relay[params]:
            l_content.extend(rel_on_mov) if relay.value() else l_content.extend(rel_off_mov)
        else:
            l_content.extend(rel_on) if relay.value() else l_content.extend(rel_off)

    with open('html/dev_manager.html', 'r') as in_file:
        content = in_file.read()
    return content % tuple(l_content), sock    

@send_anything
def config_connection(sock, path, method, *args):
    if method == 'POST':
        body = str(sock.recv(4096), "utf8").split('&')
        d = {}
        for el in body:
            key, val = el.split('=')
            d[key] = val
        if d['connect_mode'] != 'Access+point+mode':
            d['connect_mode'] = ''
        d_params = {'ap_mode': 'connect_mode', 'wlan_id': 'ssid', 'wlan_pass': 'ssid_pwd',
                    'ssid': 'ssid_ap', 'password': 'ap_pwd', 'ip': 'ip',
                    'subnet_mask': 'mask', 'gw': 'gw', 'dns': 'dns'}
        with open('config.txt', 'w') as config:
            for k, v in d_params.items():
                print(k + ':' + d[v], file=config)
    with open('config.txt', 'r') as config:
        d_config = {}
        for line in config:
            key, val = line.rstrip().split(':')
            d_config[key] = val
    if d_config['ap_mode']:
        in_tuple = ('checked', '', d_config['wlan_id'], d_config['ssid'], d_config['ip'],
                    d_config['subnet_mask'], d_config['gw'], d_config['dns'])
    else:
        in_tuple = ('', 'checked', d_config['wlan_id'], d_config['ssid'], d_config['ip'],
                    d_config['subnet_mask'], d_config['gw'], d_config['dns'])
    with open('html/config_connection.html', 'r') as in_file:
        content = in_file.read()
    return content % in_tuple, sock

@send_anything
def config_devices(sock, path, method, *args):
    if method == 'POST':
        body = str(sock.recv(4096), "utf8").split('&')
        d = {}
        for el in body:
            key, val = el.split('=')
            d[key] = val
        with open('config_devices.txt', 'w') as config:
            for k, v in d.items():
                print(k + ':' + v, file=config)
                
    with open('config_devices.txt', 'r') as config:
        d_config = {}
        for line in config:
            key, val = line.rstrip().split(':')
            d_config[key] = val
    t = ('checked', '')
    t_rev = ('', 'checked')
    l_insert = []
    for key in sorted(d_config):
        l_insert.extend(t) if d_config[key] == 'On' else l_insert.extend(t_rev)
    with open('html/config_devices.html', 'r') as in_file:
        content = in_file.read()
    return content % tuple(l_insert), sock

def random_string(num):
    s_ch = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*+,-.:;<=>?@[\]^_`{|}~'
    s_out = ''
    for i in range(num):
        s_out += random.choice(s_ch)
    return s_out

def get_body(str_body, d_body):
    key, value = str_body.split('=')
    d_body[key] = value
    return d_body

def init_devices():
    with open('config_devices.txt', 'r') as config:
        d_config = {}
        for line in config:
            key, val = line.rstrip().split(':')
            d_config[key] = val
    for relay, key in zip(l_relay, sorted(d_config)):
        relay.value(1) if d_config[key] == 'On' else relay.value(0)

def main_run():
    global flag_login, attempt_cnt
    init_devices()
    wlan = create_wlan()
    addr = socket.getaddrinfo(wlan.ifconfig()[0], 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)
    flag_login = False
    attempt_cnt = 3
    while True:
        if not attempt_cnt:
            attempt_cnt = 3
            time.sleep(300)
        cl, addr = s.accept()
        print('client connected from', addr)
        cl.settimeout(5.0)
        try:
            cl_file = cl.makefile('rwb', 0)
            line = cl_file.readline()
            if not line:
                cl.close()
                continue
            method, s_temp, *tail = str(line, "utf8").split() if line else ['', '']
            while line and line != b'\r\n':
                line = cl_file.readline()
            path = s_temp.split('?')[0]
            params = '?'.join(s_temp.split('?')[1:])
            print(method, path, params)
            # Для усіх запитів, крім у яких path буде '/favicon' або '*.css' надсилаємо заголовок:
            if path.find('.css') == -1 and path != '/favicon':
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            if flag_login:
                d_send[path](cl, path, method, params) if path in d_send else d_send['/'](cl, path, method, params)
            else:
                d_send[path](cl, path, method, params) if path.find('.css') != -1 or path == '/favicon' else d_send['/login.html'](cl, path, method, params)
            print(flag_login)
            cl.close()
        except OSError:
            cl.close()

d_send = {'/favicon': send_image,
          '/': send_main_menu, '/sens_status.html': send_sens_status,
          '/send_text.html': send_send_text,
          '/menu.css' : send_css, '/sens_status.css': send_css,
          '/login.html': send_login, '/logout.html': send_logout, '/settings.html': send_main_config,
          '/sens_to_led.html': send_sens_status, '/stop_run_text.html': send_send_text,
          '/password_change.html': password_change, '/config_connection.html': config_connection,
          '/reboot.html': lambda *args: machine.reset(),
          '/button.css': send_css, '/dev_manager.html': dev_manager,
          '/relay_on.jpg': send_image, '/relay_off.jpg': send_image,
          '/relay_on_mov.jpg': send_image, '/relay_off_mov.jpg': send_image,
          '/config_devices.html': config_devices
          }

main_run()
