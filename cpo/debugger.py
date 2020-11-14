
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
        self.monitored = {}
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

    def monitor(self, name, state):
        self.monitored[name] = state

    def remove_monitor(self, name):
        del self.monitored[name]

    def clear_monitor(self, name):
        self.monitored = {}

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

        print(f'{len(active_threads)-2} threads active')  #
        for thread in active_threads:
            self.show_thread_state(file, thread, waiting.get(thread, None))

        print('', file=file)
        if len(self.monitored) > 0:
            print('== Monitored Expressions ==', file=file)
            for name, state in self.monitored.items():
                print(f'{name}: ', end='', file=file)
                if state is None:
                    print('<not available>', file=file)
                else:
                    print(state(), file=file)

        announced = False
        for _, ref in registered.items():
            obj: register.Debuggable = ref()
            if obj is not None:
                if not announced:
                    announced = True
                    print('== Registered Objects ==', file=file)
                try:
                    if obj.has_state:
                        print('', file=file)
                    obj.show_state(file=file)
                except Exception as e:
                    print('Exception while determining state'
                          ' of a registed object', file=file)
                    traceback.print_exc(file=file)  # TODO check this is the right call

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
            # state = thread.get_state() # nyi TODO
            # blocker = LockSupper.get_blocker(thread) # nyi TODO
            print(threads.get_thread_identity(thread), file=file)

    def show_blocker(self, blocker, file):
        raise NotImplementedError

    def show_stack_trace(self, thread, file):
        raise NotImplementedError

