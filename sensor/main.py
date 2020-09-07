import pyshark
import concurrent.futures
import configparser

config = configparser.RawConfigParser()
config.read(r'config')

operation_mode = config['default']['operation_mode']
timeout = config['default']['timeout']

print(f"running in {operation_mode} mode...")

unique_mac_addresses = set()


def finalize():
    if operation_mode == 'debug':
        print('total packets sniffed: {}'.format(len(unique_mac_addresses)))
        unique_mac_addresses.clear()
    if operation_mode == 'offline':
        print('offline')
    if operation_mode == 'online':
        print('online')


def process_mac(mac_address):
    unique_mac_addresses.add(mac_address)


def process_pkt(packet):
    if hasattr(packet['wlan'], 'ta'):
        process_mac(packet['wlan'].ta)


print('capturing wifi communications...')
capture = pyshark.LiveCapture(interface='wlan1')

try:
    while True:
        capture.apply_on_packets(process_pkt, timeout=timeout)
except concurrent.futures._base.TimeoutError as e:

