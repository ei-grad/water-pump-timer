import socket


class WebForm(object):

    def __init__(self, app, address, port):
        self.app = app
        self.address = address
        self.port = port
        self.clients = {}

    @property
    def template(self):
        return open('webform.tpl').read()

    def start(self):
        self.listen_socket = listen_socket = socket.socket()
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ai = socket.getaddrinfo(self.address, self.port)
        addr = ai[0][4]
        listen_socket.bind(addr)
        listen_socket.listen(1)
        listen_socket.setsockopt(socket.SOL_SOCKET, 20, self.accept_handler)
        print('\nWebForm service started http://%s:%d' % (self.address, self.port))

    def get_actions(self):
        return '\n'.join([
            '<form action=%s method=POST><input type=submit value=%s></form>' % i
            for i in [
                    ('switch', 'Switch'),
                    ('pause', 'Pause') if self.app.running else ('resume', 'Resume'),
                    ('reset', 'Reset'),
            ]
        ])

    def accept_handler(self, listen_socket):

        client_socket, client_address = listen_socket.accept()
        client_stream = client_socket.makefile('rwb', 0)

        try:
            method, action = client_stream.readline().strip().decode('ascii').split()[:2]
        except Exception:
            print("ERROR: got incomplete request from ", client_address, ", closing connection")
            client_socket.close()
            return

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
            send_http_response(client_socket, 200, self.template.format(
                message='',
                status=self.app.get_status().replace(' ', '<br/>'),
                actions=self.get_actions(),
                **self.app.config.__dict__))
        elif method == 'POST':
            if action == '/config':
                for i in body.split('&'):
                    k, v = i.split('=')
                    assert k in ('tick_period', 'load_duration',
                                 'pump_duration', 'rounds', 'switch_delay')
                    setattr(self.app.config, k, int(v))
                self.app.config.save()
                message = '* parameters updated'
            elif action == '/reset':
                self.app.start()
                message = '* counters set to zero, timer restarted'
            elif action == '/switch':
                message = self.app.switch_relays()
            elif action == '/pause':
                self.app.pause()
                message = '* timer stopped'
            elif action == '/resume':
                self.app.resume()
                message = '* timer started'
            else:
                send_http_response(client_socket, 404, 'Not Found')
                return
            send_http_response(client_socket, 200, self.template.format(
                message=message,
                status=self.app.get_status().replace(' ', '<br/>'),
                actions=self.get_actions(),
                **self.app.config.__dict__))
        else:
            send_http_response(client_socket, 405, 'Method Not Allowed')


def send(sock, data):
    while True:
        bytes_sent = sock.send(data)
        if bytes_sent != len(data):
            data = data[bytes_sent:]
        else:
            break


http_status_messages = {
    200: 'OK',
    404: 'Not Found',
    405: 'Method Not Allowed',
}


def send_http_response(sock, status, data):
    send(sock, "HTTP/1.1 %d %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % (
        status, http_status_messages[status], len(data)))
    send(sock, data)
