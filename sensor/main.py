import pyshark
import paho.mqtt.client as mqtt
import configparser
import os
import time

config = configparser.RawConfigParser()
config.read(r'config')

operation_mode = config['default']['operation_mode']
timeout = int(config['default']['timeout'])
interface = config['default']['interface']
sensor_id = config['default']['sensor_id']
mqtt_url = config['default']['mqtt_broker_url']
mqtt_port = int(config['default']['mqtt_broker_port'])

print(f"Running in {operation_mode} mode...")

# put wifi card into monitor mode
print("Putting wifi in monitor mode...")
os.system(f'sudo ifconfig {interface} down')
os.system(f'sudo iwconfig {interface} mode monitor')
os.system(f'sudo ifconfig {interface} up')


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


if operation_mode == 'online':
    # init MQTT
    mqttc = mqtt.Client(client_id=sensor_id)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    # connect to broker
    mqttc.connect(mqtt_url, mqtt_port, 60)
    mqttc.loop_start()

unique_mac_addresses = set()


def finalize():
    if operation_mode == 'debug':
        print('total packets sniffed: {}'.format(len(unique_mac_addresses)))
        unique_mac_addresses.clear()
    if operation_mode == 'offline':
        print('offline mode not implemented')
    if operation_mode == 'online':
        mqttc.publish(f'/{sensor_id}/wifi', str(len(unique_mac_addresses)))
        unique_mac_addresses.clear()


def process_mac(mac_address):
    unique_mac_addresses.add(mac_address)


def process_pkt(packet):
    if hasattr(packet['wlan'], 'ta'):
        process_mac(packet['wlan'].ta)


print('Capturing wifi communications...')
capture = pyshark.LiveCapture(interface=interface)

if operation_mode == 'debug':
    capture.set_debug()

start = time.time()
for packet in capture.sniff_continuously():
    process_pkt(packet)
    if time.time() - start > timeout:
        start = time.time()
        finalize()
