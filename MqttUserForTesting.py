#Filename : TLCRS232WithMqtt.py
#Version  :	1.0.0 
#Description : Python Program to control TLC Controller using MQTT messages
#Date : Dec 2022
#Author : Meimurugan Krishna

#***********************************************************************************#
#*************** Import Libraries **************************************************#
#***********************************************************************************#
import time
from threading import Thread
from paho.mqtt import client as mqtt_client
from TLC import *

#***********************************************************************************#
#*************** File Constants ****************************************************#
#***********************************************************************************#
BROKER = 'broker.emqx.io'
#BROKER = '192.168.1.145'
BROKER_PORT = 1883
TOPIC = "python/mqtttest"
MeritInitTopic = "/Merit/Controls/"
MeritInitiate = "Initiate"
MeritTerminate = "Terminate"
MeritDataPostTopic = "/Merit/Post/"
CLIENT_ID = f'python-mqtt-1001'
USERNAME = 'emqx1'
PASSWORD = 'public1'
MeritReqTopic = "/Merit/Req/"

#***********************************************************************************#
#*************** File Variables ****************************************************#
#***********************************************************************************#

#***********************************************************************************#
#******************************* Functions *****************************************#
#***********************************************************************************#
#********************************************************************************************#
#Description : function to connect mqtt client
#Arguments : Mqtt Client id, Username, Password, Broker, BrokerPortMqttClient, MqttTopic
#Return : mqtt client
#********************************************************************************************#
def Merit_ConnectMqtt(clientId, UserName, Password, Broker, BrokerPort):
    def Merit_OnConnect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(clientId)
    client.username_pw_set(UserName, Password)
    client.on_connect = Merit_OnConnect
    client.connect(Broker, BrokerPort)
    return client
	
#********************************************************************************************#
#Description : function to publich the mqtt topic
#Arguments : MqttClient, MqttTopic, MqttMessage
#Return : None
#********************************************************************************************#
def Merit_Publish(client, topic, message):
	result = client.publish(topic, message)		
	# result: [0, 1]
	status = result[0]
	if status == 0:
		print(f"Send `{message}` to topic `{topic}`")
	else:
		print(f"Failed to send message to topic {topic}")

#********************************************************************************************#
#Description : function to subscribe the mqtt topic
#Arguments : MqttClient, MqttTopic
#Return : None
#********************************************************************************************#	
def Merit_Subscribe(client: mqtt_client, topic):
	def Merit_OnMessage(client, userdata, msg):
		print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic!")
	client.subscribe(topic)
	client.on_message = Merit_OnMessage

#********************************************************************************************#
#Description : function to start the mqtt process
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_MqttStart():
	client = Merit_ConnectMqtt(CLIENT_ID, USERNAME, PASSWORD, BROKER, BROKER_PORT)
	client.loop_start()
	#Merit_Subscribe(client,MeritInitTopic)
	Merit_Subscribe(client, MeritDataPostTopic)
	#Merit_Publish(client,MeritInitTopic,"Initiate")
	Merit_Publish(client,MeritInitTopic,MeritTerminate)
	#Merit_Publish(client,MeritReqTopic, 1)
	print("Initiated")
	#time.sleep(4)
	
	#Merit_Publish(client,MeritReqTopic, 1)
	while(True):
		#Merit_Publish(client,MeritInitTopic,MeritInitiate)
		#Merit_Publish(client,MeritReqTopic, 1)
		time.sleep(1.5)

def Merit_RS232Start():
	MeritPort = Merit_FindPort()
	if  MeritPort != "":
		x = threading.Thread(target = Merit_SerialWriteQueuefn, args=(), daemon = True)
		x.start()
		while(1):
			Merit_SerialWeigh()
			time.sleep(0.001)
		
	else:
		print("Cannot find TLC port")	
	
#********************************************************************************************#  
#Description : Entry point of this program
#Notes : To make sure that don't allow this script to import as module in another file (if imported then __name__ will be file name)
#********************************************************************************************#
if __name__=="__main__": #To run as a standalone script
	t1 = Thread(target = Merit_MqttStart, daemon = True)
	#t2 = Thread(target = Merit_RS232Start, daemon = True)

	# start the threads
	t1.start()
	#t2.start()
	while(1):
		time.sleep(0.001)
		