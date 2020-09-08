import pyshark
import concurrent.futures
import configparser
import os
import time

config = configparser.RawConfigParser()
config.read(r'config')

operation_mode = config['default']['operation_mode']
timeout = int(config['default']['timeout'])
interface = config['default']['interface']

print(f"running in {operation_mode} mode...")

# put wifi card into monitor mode
print("putting wifi in monitor mode...")
os.system(f'sudo ifconfig {interface} down')
os.system(f'sudo iwconfig {interface} mode monitor')
os.system(f'sudo ifconfig {interface} up')

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
capture = pyshark.LiveCapture(interface=interface)
capture.set_debug()
start = time.time()
for packet in capture.sniff_continuously():
    process_pkt(packet)
    if time.time() - start > timeout:
        start = time.time()
        finalize()

