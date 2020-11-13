
import socket
import threading

from . import config

class DEBUGGER:

    def __init__(self, debug_port: int):
        self.debug_port = debug_port
        self.port = config.get('port', self.debug_port)
        self.SUPPRESS = config.get('suppress', '')
        if self.port >= 0:
            self.socket = socket.create_server(('localhost', self.port))
            self.port = self.socket.getsockname()[1]
            self.thread = threading.Thread(
                name=f"CSO Debugger Server (Port: {self.port})",
                target=self.run_server,
            )
            self.thread.start()

    def __str__(self):
        return f'Debugger(http://localhost:{self.port})'

    def run_server(self):
        while True:
            conn, addr = self.socket.accept()
            handler = threading.Thread(
                name="CSO Debugger Responder",
                target=self.handle,
                args=(conn,)
            )
            self.handler.start()

    def handle(self, conn: socket.socket):
        raise NotImplementedError

    def show_stack_trace(self, thread, out):
        raise NotImplementedError





