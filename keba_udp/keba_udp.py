import select
import socket
import json
import logging
from typing import Optional

T_UDP_PAUSE = 0.1
T_COM_PAUSE = 5.0
T_DIS_PAUSE = 2.0
MAX_RESPONSE_SIZE = 512
LOCAL_PORT = 7090
RESPONSE_TIMEOUT = 0.2
CONFIRMATION_MESSAGE = b'TCH-OK :done\n'


class KebaUDP:
    def __init__(self, host: str, port: int = 7090, logger: Optional[logging.Logger] = None):
        self.host = host
        self.port = port
        self.udp_socket = None
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("keba_udp")
    
    def connect(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", LOCAL_PORT))
        self.udp_socket.connect((self.host, self.port))
        self.udp_socket.settimeout(None)
        self.connection_buildup()
        return self

    def __del__(self):
        if self.udp_socket is not None:
            self.udp_socket.close()

    def connection_buildup(self):
        self.get_command_response("i")
        self.get_report(1)
        self.get_report(2)
        self.get_report(3)

    def get_command_response(self, command: str, ):
        self.logger.info(f"sent command: {command}")
        ready = select.select([self.udp_socket], [], [], 0.0)
        if ready[0]:
            resp, _ = self.udp_socket.recvfrom(MAX_RESPONSE_SIZE)
            self.logger.warning(f"found unexpected data in read socket. Dump {resp}")
        self.udp_socket.send(command.encode("utf-8"))
        ready = select.select([self.udp_socket], [], [], RESPONSE_TIMEOUT)
        if ready[0]:
            resp, addr = self.udp_socket.recvfrom(MAX_RESPONSE_SIZE)
            return resp
        else:
            self.logger.error(f"did not receive response for command {command} within {RESPONSE_TIMEOUT} seconds")
            return None

    def get_report(self, n: int, retries=10):
        assert n in (1, 2, 3) or n >= 100, f"Invalid report {n} must be one of (1,2,3)"
        try:
            report = json.loads(self.get_command_response(f"report {n}"))
            return report
        except json.JSONDecodeError:
            if retries > 0:
                self.logger.warning("retrying get report, could not decode response")
                return self.get_report(n, retries-1)
            else:
                raise

    def set_currtime(self, current: int, delay: Optional[int] = None, retries=10):
        if delay is None:
            delay = 0
        current = int(float(current))
        delay = int(delay)
        assert 6000 <= current <= 63000 or current == 0, f"Current value must lie between 6000 mA and 63000 mA"
        assert 0 <= delay <= 860400, f"Delay must be between 0 and 860400 seconds."
        resp = self.get_command_response(f"currtime {current} {delay}")
        if resp != CONFIRMATION_MESSAGE:
            if retries > 0:
                self.logger.warning("retrying currtime command, due to invalid response.")
                return self.set_currtime(current, delay, retries-1)
            else:
                raise AssertionError(f"unexpected response {resp}. Reached maximum number of retries.")
        else:
            self.logger.info("currtime command accepted.")


