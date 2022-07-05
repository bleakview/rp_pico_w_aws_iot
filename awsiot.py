import machine
import network
from umqtt.simple import MQTTClient
import time
#WIFI parameters
#Access point name
ACCESS_POINT = "{access point name }"
#Access point password
PASSWORD = "{access point password}"

# AWS endpoint parameters.
# Should be different for each device can be anything
CLIENT_ID = "{client id}"
# You can get tihs address from AWS IoT->Settings -> Endpoint
# mothing like : {host id}.iot.{region}.amazonaws.com
AWS_ENDPOINT = b'{connection endpoint}'
#MQTT channel name for publishing
PUBLISH_CHANNEL='temperature'
#MQTT channel name for subscribing
SUBSCRIBED_CHANNEL='led'

def get_ssl_params():
    """ Get ssl parameters for MQTT"""
    # These keys must be in der format the keys
    # downloaded from AWS website is in pem format
    keyfile = '/certs/private.der'
    with open(keyfile, 'r') as f:
        key = f.read()
    certfile = "/certs/certificate.der"
    with open(certfile, 'r') as f:
        cert = f.read()    
    ssl_params = {'key': key,'cert': cert, 'server_side': False}
    return ssl_params

def mqtt_callback(topic, msg):
    """ Callback function for received messages"""
    print("received data:")
    print("topic: %s message: %s" %(topic, msg))
    if topic==b'led':
        # on pico w in is connected to wireless chip so led code must adept to it
        led = machine.Pin("LED", machine.Pin.OUT)
        if msg==b'on':
            led.on()
        elif msg==b'off':
            led.off()
        else:
            print("i dont know what to do with %s" % msg)
          
  
def check_wifi(wlan):
    """Wait for connection"""
    while not wlan.isconnected():
        time.sleep_ms(500)
        print(".")
        wlan.connect( ACCESS_POINT, PASSWORD )
    if not wlan.isconnected():
        print("not connected")
    if wlan.isconnected():
        print("connected")
        
def read_internal_temp_sensor():
    """Read internal temperature sensor of RPi Pico W"""
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

# Setup WiFi connection.
wlan = network.WLAN( network.STA_IF )
wlan.active( True )



check_wifi(wlan)
ssl_params=get_ssl_params()

# Connect to MQTT broker.
mqtt = MQTTClient( CLIENT_ID, AWS_ENDPOINT, port = 8883, keepalive = 10000, ssl = True, ssl_params = ssl_params )
mqtt.set_callback(mqtt_callback)
mqtt.connect()
# Subscribe to our led channel for led commands
# you will only receive messages from subscribed channels
mqtt.subscribe(SUBSCRIBED_CHANNEL)

# Send 10 messages to test publish messages
print("Sending messages...")
for i in range(10):
    #get temperature
    temperature=read_internal_temp_sensor()
    # Publish temperature to temperature channel it's in JSON format
    # so that AWS will not give Message format error
    print('{"temp":%s}'% temperature)
    mqtt.publish( topic = PUBLISH_CHANNEL, msg = b'{"temp":%s}'% temperature , qos = 0 )
    time.sleep_ms(2000)
print("done sending messages waiting for messages...")
while True:
    #Check for messages from MQTT
    mqtt.check_msg()
    time.sleep(1)

