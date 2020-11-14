
import datetime
import socket
import threading
import traceback

from . import config
from . import register
from . import server
from . import threads
from . import util

class DEBUGGER:

    def __init__(self, debug_port: int = 0):
        self.debug_port = debug_port
        self.host = 'localhost'
        self.port = config.get('port', self.debug_port)
        self.SUPPRESS = config.get('suppress', '')
        if self.port >= 0:
            self.socket = server.create_server(self.host, self.port)
            self.port = self.socket.getsockname()[1]
            self.thread = threading.Thread(
                name=str(self),
                target=self.run_server,
                daemon=True,
            )
            self.thread.start()
            util.synced_print(str(self) + ': ACTIVE')

    def __str__(self):
        return f'Debugger(http://{self.host}:{self.port})'

    def run_server(self):
        try:
            while True:
                conn, addr = self.socket.accept()
                handler = threading.Thread(
                    name="CSO Debugger Responder",
                    target=self.handle,
                    args=(conn,)
                )
                handler.start()
        finally:
            self.socket.close()

    def handle(self, conn: socket.socket):
        try:
            in_ = conn.makefile('r')
            out = conn.makefile('w')

            # we must read in the full header even if we dont
            # intend to use it...
            header = []
            line = " "
            while line not in ['\n', '\r\n', '']:
                line = in_.readline()
                header.append(line)

            print(
f"""HTTP/1.1 201
Content-Type: text/plain; charset=UTF-8
Server-name: CPO debugger

CPO State {datetime.datetime.now()}
""", file=out)
            self.show_cso_state(file=out)

            out.flush()
            out.close()
            conn.shutdown(0)
            conn.close()
        finally:
            if conn is not None:
                conn.close()

    def show_cso_state(self, file):
        active_threads = threads.get_active_threads()
        waiting = register.waiting()
        registered = register.registered

        for thread in active_threads:
            self.show_thread_state(file, thread, waiting.get(thread, None))

    def show_thread_state(self, file, thread: threading.Thread, waiting):
        if waiting is not None:
            for thing in waiting:
                print(f'THREAD {threads.get_thread_identity(thread)}',
                      end='', file=file)
                try:
                    thing.show_state(file)
                    print('', file=file)
                except Exception as e:
                    print("Exception while showing the state "
                          "of a registered component", file=file)
                    traceback.print_exc(file=file)  # TODO check this is the right call
                    print("--------------", file=file)
        elif waiting is None:
            raise NotImplementedError




    def show_stack_trace(self, thread, out):
        raise NotImplementedError





