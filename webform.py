from machine import reset
import socket


class WebForm(object):

    template = '''<html><head>
<style>
h1, h3, div {{margin:1%;}}
form {{max-width:480px;margin:0;}}
label, input {{display:inline-block;width:48%;margin:1%;}}
input[type=submit] {{width:98%;}}
input[type=text] {{text-align:right;}}
</style>
<body>
<div>{message}</div>
<h1>Water pump timer</h1>
<form action=switch method=POST><input type=submit value=Switch></form>
<form action=reset method=POST><input type=submit value=Reboot></form>
<form action=start method=POST><input type=submit value=Start></form>
<form action=stop method=POST><input type=submit value=Stop></form>
<h3>Configuration</h3>
<form action=config method=POST>
<label>Interval:</label><input type=text name=interval value={interval}><br/>
<label>Duration:</label><input type=text name=duration value={duration}><br/>
<label>Rounds:</label><input type=text name=rounds value={rounds}><br/>
<input type=submit value="Apply and save">
</form>
'''

    def __init__(self, app, address, port):
        self.app = app
        self.address = address
        self.port = port
        self.clients = {}

    def start(self):
        self.listen_socket = listen_socket = socket.socket()
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ai = socket.getaddrinfo(self.address, self.port)
        addr = ai[0][4]
        listen_socket.bind(addr)
        listen_socket.listen(1)
        listen_socket.setsockopt(socket.SOL_SOCKET, 20, self.accept_handler)
        print('\nWebForm service started http://%s:%d' % (self.address, self.port))

    def accept_handler(self, listen_socket):

        client_socket, client_address = listen_socket.accept()
        client_stream = client_socket.makefile('rwb', 0)

        method, action = client_stream.readline().strip().decode('ascii').split()[:2]

        content_length = 0

        # skipping the request headers, so the next line would be the request body
        while True:
            line = client_stream.readline()
            if line.startswith(b'Content-Length:'):
                content_length = int(line.decode('ascii').split(':')[1])
            if line in (b'\r\n', b''):
                break

        body = client_stream.read(content_length).decode('ascii').strip()

        if method == 'GET':
            if action == '/':
                send_http_response(client_socket, 200, self.template.format(
                    message='', **self.app.config.__dict__))
            else:
                send_http_response(client_socket, 404, '')
        elif method == 'POST':
            if action == '/config':
                for i in body.split('&'):
                    k, v = i.split('=')
                    assert k in ('interval', 'duration', 'rounds')
                    setattr(self.app.config, k, int(v))
                self.app.config.save()
                message = '* parameters updated'
            elif action == '/reset':
                reset()
            elif action == '/switch':
                message = self.app.switch_relays()
            elif action == '/stop':
                self.app.stop()
                message = '* timer stopped'
            elif action == '/start':
                self.app.start()
                message = '* timer started'
            else:
                send_http_response(client_socket, 404, '')
                return
            send_http_response(client_socket, 200, self.template.format(
                message=message, **self.app.config.__dict__))
        else:
            send_http_response(client_socket, 405, '')


def send(sock, data):
    bytes_sent = sock.send(data)
    if bytes_sent != len(data):
        print("ERROR: couldn't send data in one chunk")


http_status_messages = {
    200: 'OK',
    404: 'Not Found',
    405: 'Method Not Allowed',
}


def send_http_response(sock, status, data):
    send(sock, "HTTP/1.1 %d %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % (
        status, http_status_messages[status], len(data)))
    send(sock, data)
