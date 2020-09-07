import pyshark
import concurrent.futures

count = 0
def process_pkt(packet):
	global count
	count += 1
	if hasattr(packet['wlan'], 'ta'):
		print(packet['wlan'].ta)

t = 20
print('capturing wifi communications...')

capture = pyshark.LiveCapture(interface='wlan1')

try:
	capture.apply_on_packets(process_pkt,timeout=t)
except concurrent.futures._base.TimeoutError as e:
        print('total packets sniffed: {}'.format(count))


