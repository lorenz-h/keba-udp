import logging
from keba_udp import KebaUDP

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with KebaUDP("192.168.178.55", 7090) as keba:
        keba.set_currtime(6000, 0)
        print(keba.get_report(2))