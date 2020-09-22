import logging
from keba_udp import KebaUDP

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    keba = KebaUDP("192.168.178.55", 7090)
    keba.connect()
    print(keba.get_report(1))
    print(keba.get_report(2))
    print(keba.get_report(3))
    print(keba.get_report(100))
