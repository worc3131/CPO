
import socket

def create_server(host, port, max_backlog=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.listen(max_backlog)
        return sock
    except Exception as e:
        sock.close()
        raise e
