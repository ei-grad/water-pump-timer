from machine import reset
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
                    message='',
                    status=self.app.get_status().replace(' ', '<br/>'),
                    **self.app.config.__dict__))
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
                message=message,
                status=self.app.get_status().replace(' ', '<br/>'),
                **self.app.config.__dict__))
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
