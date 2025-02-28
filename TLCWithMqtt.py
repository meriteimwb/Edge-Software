#Filename : TLCWithMqtt.py
#Version  :	1.2.3
#Description : Python Program to control Track Logic Controller(RS232) using Mqtt 
#Date : Dec 2022
#Author : Meimurugan Krishna

#***********************************************************************************#
#*************** Import Libraries **************************************************#
#***********************************************************************************#
import serial
from serial.tools import list_ports
import time
import numpy as np
from datetime import datetime
from queue import PriorityQueue
import threading
from threading import Thread
from paho.mqtt import client as mqtt_client
import json
import logging
import requests
import datetime
import socket

#***********************************************************************************#
#*************** File Constants ****************************************************#
#***********************************************************************************#
#MERIT Serial Communication(RS232) Parameters
MERIT_SERIAL_BAUD_RATE				= 19200
MERIT_SERIAL_PARITY					= 'N'
MERIT_SERIAL_DATABITS				= 8
MERIT_SERIAL_STOPBITS				= 1
MERIT_SERIAL_TIMEOUT				= 0.5
MERIT_SERIAL_INTER_CHAR_TIMEOUT		= 0.05
MERIT_SERIAL_MAX_BYTES_TO_RECEIVE	= 150
MERIT_QUERY_DELAY					= 0.001
MERIT_DEFAULT_QUERY_DELAY   = 0.25

#PACKET BYTE ORDER
MERIT_HEADER_ID_POSITION			= 0x00
MERIT_RTU_ID_POSITION				= 0x01
MERIT_QUERY_LEN_POSITION			= 0x02
MERIT_COMMAND_ID_POSITION			= 0x04

#PACKET BYTES
MERIT_START_BYTE 					= 0x7E
MERIT_RTUID_BYTE 					= 0x01
MERIT_LENGTH_OF_QUERY_LENGTH		= 0x02
MERIT_ADDITIONAL_BYTE				= 0x10

#READ COMMANDS
MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD	= 0x04
MERIT_DIGITAL_INPUT_STATUS_READ_CMD		= 0x0A
MERIT_VERSION_OF_CODE_READ_CMD 			= 0x50
MERIT_CODE_RELAESE_DATE_READ_CMD 		= 0x51
MERIT_WB_ID_READ_CMD					= 0x53
MERIT_AXLE_1TO50_WEIGHT_READ_CMD		= 0x82
MERIT_AXLE_51TO100_WEIGHT_READ_CMD		= 0x83
MERIT_AXLE_101TO150_WEIGHT_READ_CMD		= 0x84
MERIT_AXLE_151TO200_WEIGHT_READ_CMD		= 0x85
MERIT_AXLE_201TO250_WEIGHT_READ_CMD		= 0x86
MERIT_AXLE_251TO300_WEIGHT_READ_CMD		= 0x87
MERIT_AXLE_301TO350_WEIGHT_READ_CMD		= 0x88
MERIT_AXLE_351TO400_WEIGHT_READ_CMD		= 0x89
MERIT_AXLE_401TO450_WEIGHT_READ_CMD		= 0x8A
MERIT_AXLE_451TO500_WEIGHT_READ_CMD		= 0x8B

#WRITE COMMANDS
MERIT_SCOREBOARD_AVAIL_WRITE_CMD		= 0x54
MERIT_WAGON_WEIGHT_WRITE_CMD			= 0x5A
MERIT_OUTPUT_STATUS_WRITE_CMD			= 0x1E
MERIT_OUTPUT_STATUS_RESET_WRITE_CMD		= 0x49
MERIT_INPUT_STATUS_WRITE_CMD			= 0x1F
MERIT_TERMINATE_WRITE_CMD				= 0x5B
MERIT_INIT_AND_AXLE_ELIMINATE_WRITE_CMD	= 0x5D

#CRC16 Table
CRC16_TABLE = [
	0x00000, 0x01189, 0x02312, 0x0329B, 0x04624, 0x057AD, 0x06536, 0x074BF, 0x08C48, 0x09DC1, 0x0AF5A, 0x0BED3, 0x0CA6C, 0x0DBE5, 0x0E97E, 0x0F8F7,
	0x01081, 0x00108, 0x03393, 0x0221A, 0x056A5, 0x0472C, 0x075B7, 0x0643E, 0x09CC9, 0x08D40, 0x0BFDB, 0x0AE52, 0x0DAED, 0x0CB64, 0x0F9FF, 0x0E876,
	0x02102, 0x0308B, 0x00210, 0x01399, 0x06726, 0x076AF, 0x04434, 0x055BD, 0x0AD4A, 0x0BCC3, 0x08E58, 0x09FD1, 0x0EB6E, 0x0FAE7, 0x0C87C, 0x0D9F5, 
	0x03183, 0x0200A, 0x01291, 0x00318, 0x077A7, 0x0662E, 0x054B5, 0x0453C, 0x0BDCB, 0x0AC42, 0x09ED9, 0x08F50, 0x0FBEF, 0x0EA66, 0x0D8FD, 0x0C974,
	0x04204, 0x0538D, 0x06116, 0x0709F, 0x00420, 0x015A9, 0x02732, 0x036BB, 0x0CE4C, 0x0DFC5, 0x0ED5E, 0x0FCD7, 0x08868, 0x099E1, 0x0AB7A, 0x0BAF3, 
	0x05285, 0x0430C, 0x07197, 0x0601E, 0x014A1, 0x00528, 0x037B3, 0x0263A, 0x0DECD, 0x0CF44, 0x0FDDF, 0x0EC56, 0x098E9, 0x08960, 0x0BBFB, 0x0AA72, 
	0x06306, 0x0728F, 0x04014, 0x0519D, 0x02522, 0x034AB, 0x00630, 0x017B9, 0x0EF4E, 0x0FEC7, 0x0CC5C, 0x0DDD5, 0x0A96A, 0x0B8E3, 0x08A78, 0x09BF1,
	0x07387, 0x0620E, 0x05095, 0x0411C, 0x035A3, 0x0242A, 0x016B1, 0x00738, 0x0FFCF, 0x0EE46, 0x0DCDD, 0x0CD54, 0x0B9EB, 0x0A862, 0x09AF9, 0x08B70, 
	0x08408, 0x09581, 0x0A71A, 0x0B693, 0x0C22C, 0x0D3A5, 0x0E13E, 0x0F0B7, 0x00840, 0x019C9, 0x02B52, 0x03ADB, 0x04E64, 0x05FED, 0x06D76, 0x07CFF, 
	0x09489, 0x08500, 0x0B79B, 0x0A612, 0x0D2AD, 0x0C324, 0x0F1BF, 0x0E036, 0x018C1, 0x00948, 0x03BD3, 0x02A5A, 0x05EE5, 0x04F6C, 0x07DF7, 0x06C7E,
	0x0A50A, 0x0B483, 0x08618, 0x09791, 0x0E32E, 0x0F2A7, 0x0C03C, 0x0D1B5, 0x02942, 0x038CB, 0x00A50, 0x01BD9, 0x06F66, 0x07EEF, 0x04C74, 0x05DFD, 
	0x0B58B, 0x0A402, 0x09699, 0x08710, 0x0F3AF, 0x0E226, 0x0D0BD, 0x0C134, 0x039C3, 0x0284A, 0x01AD1, 0x00B58, 0x07FE7, 0x06E6E, 0x05CF5, 0x04D7C, 
	0x0C60C, 0x0D785, 0x0E51E, 0x0F497, 0x08028, 0x091A1, 0x0A33A, 0x0B2B3, 0x04A44, 0x05BCD, 0x06956, 0x078DF, 0x00C60, 0x01DE9, 0x02F72, 0x03EFB, 
	0x0D68D, 0x0C704, 0x0F59F, 0x0E416, 0x090A9, 0x08120, 0x0B3BB, 0x0A232, 0x05AC5, 0x04B4C, 0x079D7, 0x0685E, 0x01CE1, 0x00D68, 0x03FF3, 0x02E7A, 
	0x0E70E, 0X0F687, 0x0C41C, 0x0D595, 0x0A12A, 0X0B0A3, 0x08238, 0x093B1, 0x06B46, 0x07ACF, 0x04854, 0x059DD, 0x02D62, 0x03CEB, 0x00E70, 0x01FF9, 
	0x0F78F, 0x0E606, 0x0D49D, 0x0C514, 0x0B1AB, 0x0A022, 0x092B9, 0x08330, 0x07BC7, 0x06A4E, 0x058D5, 0x0495C, 0x03DE3, 0x02C6A, 0x01EF1, 0x00F78
]

#Command 90 Byte Position Description
COMMAND90RES_COMMAND_POSITION		=	0
COMMAND90RES_SIGN_OF_WEIGHT			=	1
COMMAND90RES_WEIGHT_LSB				=	2
COMMAND90RES_WEIGHT_MID				=	3
COMMAND90RES_WEIGHT_MSB				=	4
COMMAND90RES_DIRECTION				=	5
COMMAND90RES_MESSAGE				=	6
COMMAND90RES_WAGONS_WEIGHED			=	7	#8,9 Ignore
COMMAND90RES_LASTAXLE_LSB			=	10
COMMAND90RES_LASTAXLE_MSB			=	11
COMMAND90RES_SPEED_TLPAIR1_LSB		=	12
COMMAND90RES_SPEED_TLPAIR1_MSB		=	13
COMMAND90RES_SPEED_TLPAIR2_LSB		=	14
COMMAND90RES_SPEED_TLPAIR2_MSB		=	15
COMMAND90RES_SPEED_FROM_WEIGH_LSB	=	16
COMMAND90RES_SPEED_FROM_WEIGH_MSB	=	17
COMMAND90RES_AXLECOUNT_PAIR1_LSB	=	18
COMMAND90RES_AXLECOUNT_PAIR1_MSB	=	19
COMMAND90RES_AXLECOUNT_PAIR2_LSB	=	20
COMMAND90RES_AXLECOUNT_PAIR2_MSB	=	21
COMMAND90RES_AXLECOUNT_PAIR3_LSB	=	22
COMMAND90RES_AXLECOUNT_PAIR3_MSB	=	23
COMMAND90RES_AXLECOUNT_PAIR4_LSB	=	24
COMMAND90RES_AXLECOUNT_PAIR4_MSB	=	25
COMMAND90RES_AXLE_WEIGHED_LSB		=	26
COMMAND90RES_AXLE_WEIGHED_MSB		=	27	#28,29 Axle weights ignore
COMMAND90RES_AXLE_INGNORED_LSB		=	28
COMMAND90RES_AXLE_INGNORED_MSB		=	29
COMMAND90RES_WAGON_SERIAL_NUMBER	=	30
COMMAND90RES_WAGON_TYPE				=	31
COMMAND90RES_WAGON_WEIGHT_LSB		=	32
COMMAND90RES_WAGON_WEIGHT_MID		=	33
COMMAND90RES_WAGON_WEIGHT_MSB		=	34
COMMAND90RES_AXLE1WEIGHT_LSB		=	35
COMMAND90RES_AXLE1WEIGHT_MSB		=	36
COMMAND90RES_AXLE2WEIGHT_LSB		=	37
COMMAND90RES_AXLE2WEIGHT_MSB		=	38
COMMAND90RES_AXLE3WEIGHT_LSB		=	39
COMMAND90RES_AXLE3WEIGHT_MSB		=	40
COMMAND90RES_AXLE4WEIGHT_LSB		=	41
COMMAND90RES_AXLE4WEIGHT_MSB		=	42
COMMAND90RES_WAGON_SPEED_LSB		=	43
COMMAND90RES_WAGON_SPEED_MSB		=	44

#UNNAMED BITS
PIN_1	   =   0
PIN_2	   =   1
PIN_3	   =   2
PIN_4	   =   3
PIN_5	   =   4
PIN_6	   =   5
PIN_7	   =   6
PIN_8	   =   7
PIN_9	   =   8
PIN_10	  =   9
PIN_11	  =   10
PIN_12	  =   11
PIN_13	  =   12
PIN_14	  =   13
PIN_15	  =   14
PIN_16	  =   15


#Command Output Status Bits position
COMMAND4RES_SYSTEM_READY			=	0
COMMAND4RES_OVERSPEED_LAMP_RELAY	=	1
COMMAND4RES_ALARM_HOOTER			=	2
COMMAND4RES_SYSTEM_READY_LAMP		=	8
COMMAND4RES_OVERSPEED_LAMP			=	9
COMMAND4RES_ADVANCE_OVERSPEED_LAMP	=	10
COMMAND4RES_UNKNOWN_VECHILE			=	11
COMMAND4RES_AD_FAILURE				=	12

#Wagon Weigh Message Dict
OutputStatusDict = {
	COMMAND4RES_SYSTEM_READY : "SystemReady",
	COMMAND4RES_OVERSPEED_LAMP_RELAY : "OverSpeedLampRelay",
	COMMAND4RES_ALARM_HOOTER : "AlarmHooter",
	PIN_4   :   "pin4",
	PIN_5	:	"pin5",
	PIN_6	:	"pin6",
	PIN_7	:	"pin7",
	PIN_8	:	"pin8",
	COMMAND4RES_SYSTEM_READY_LAMP : "SystemReadyLamp",
	COMMAND4RES_OVERSPEED_LAMP : "OverSpeedLamp",
	COMMAND4RES_ADVANCE_OVERSPEED_LAMP : "AdvanceOverSpeedLamp",
	COMMAND4RES_UNKNOWN_VECHILE : "UnknownVehicle",
	COMMAND4RES_AD_FAILURE : "ADFailure",
	PIN_14	:	"pin14",
	PIN_15	:	"pin15",
	PIN_16	:	"pin16",
}

#Command Input Status Bits position
COMMAND10RES_TRACKSWITCH_1A			=	0
COMMAND10RES_TRACKSWITCH_1B			=	1
COMMAND10RES_TRACKSWITCH_2A			=	2
COMMAND10RES_TRACKSWITCH_2B			=	3
COMMAND10RES_TRACKSWITCH_3A			=	4
COMMAND10RES_TRACKSWITCH_3B			=	5
COMMAND10RES_TRACKSWITCH_4A			=	6
COMMAND10RES_TRACKSWITCH_4B			=	7
COMMAND10RES_START_WEIGH			=	8
COMMAND10RES_END_WEIGH				=	9
COMMAND10RES_AOS_IN_DIR_5A			=	10
COMMAND10RES_AOS_IN_DIR_5B			=	11
COMMAND10RES_AOS_OUT_DIR_6B			=	12
COMMAND10RES_AOS_OUT_DIR_6A			=	13

InputStatusDict = {
	COMMAND10RES_TRACKSWITCH_1A : "TrackSwitch1A",
	COMMAND10RES_TRACKSWITCH_1B : "TrackSwitch1B",
	COMMAND10RES_TRACKSWITCH_2A : "TrackSwitch2A",
	COMMAND10RES_TRACKSWITCH_2B : "TrackSwitch2B",
	COMMAND10RES_TRACKSWITCH_3A : "TrackSwitch3A",
	COMMAND10RES_TRACKSWITCH_3B : "TrackSwitch3B",
	COMMAND10RES_TRACKSWITCH_4A : "TrackSwitch4A",
	COMMAND10RES_TRACKSWITCH_4B : "TrackSwitch4B",
	COMMAND10RES_START_WEIGH : "StartWeigh",
	COMMAND10RES_END_WEIGH : "EndWeigh",
	COMMAND10RES_AOS_IN_DIR_5A : "Aos_In_Dir_5A",
	COMMAND10RES_AOS_IN_DIR_5B : "Aos_In_Dir_5B",
	COMMAND10RES_AOS_OUT_DIR_6B : "Aos_Out_Dir_6B",
	COMMAND10RES_AOS_OUT_DIR_6A : "Aos_Out_Dir_6A",
	PIN_15	:	"pin15",
	PIN_16	:	"pin16",
}

#Merit Serial Communication Errors
MERIT_READ_SUCCESS		=	0
MERIT_HEADER_MISMATCH	=	1
MERIT_RTUID_MISMATCH	=	2
MERIT_COMMAND_MISMATCH	=	3
MERIT_DATALEN_MISMATCH	=	4
MERIT_CHECKSUM_MISMATCH	=	5
MERIT_READ_TIMEOUT		=	6

MeritSerialRecvErrorDict = {
	MERIT_READ_SUCCESS		: "DataReadSuccess",
	MERIT_HEADER_MISMATCH   : "HeaderMismatch",
	MERIT_RTUID_MISMATCH	: "RTUIDMismatch",
	MERIT_COMMAND_MISMATCH  : "CommandMisMatch",
	MERIT_DATALEN_MISMATCH  : "LengthMisMatch",
	MERIT_CHECKSUM_MISMATCH : "CheckSumMismatch",
	MERIT_READ_TIMEOUT		: "SerialReadTimeout"
}

#Wagon Type Dict
TWO_AXLE_WAGON	=	2
FOUR_AXLE_WAGON =	4
THREE_AXLE_LOCO =	-3
FOUR_AXLE_LOCO  =	-4
WagonTypeDict = {
	TWO_AXLE_WAGON  : "2AxleWagon",
	FOUR_AXLE_WAGON : "4AxleWagon",
	THREE_AXLE_LOCO : "3AxleLoco",
	FOUR_AXLE_LOCO  : "4AxleLoco"
}

#Axle weight status Dict
AxleWeightDict = {
	-4 : "Initialised",
	-3 : "WeighingToBeDone"
}

#Wagon Weigh Message Dict
COMMAND90RES_MESSAGE_WEIGHINGOVER = 5 
COMMAND90RES_MESSAGE_LOCOSENSED   = 11 
UNKNOWN_VEHICLE = 8
WagonWeighMessageDict	= {
	0	:	"O NotDefined",
	1	:	"SystemReady",
	2	:	"DirectionIn",
	3	:	"DirectionOut",
	4	:	"TrainForward",
	COMMAND90RES_MESSAGE_WEIGHINGOVER	:	"WeighingOver",
	6	:	"TrainReversal",
	7	:	"Weighing",
	8	:	"UnknownVehicle",
	9	:	"2AxleWagon",
	10	:	"4AxleWagon",
	COMMAND90RES_MESSAGE_LOCOSENSED	:	"LocomotiveSensed",
	12	:	"NewVehicle",
	13	:	"EndOfWeighing",
	14	: 	"Checking Weighing System interface",
	15	:	"End Of Weighing",
	16	:	"SystemNotReadyForWeighing",
	17	:	"AbortWeighing",
	18	:	"18 NotDefined",
	19	:	"19 NotDefined",
	20	:	"NotValidExpectedTrackSwitch",
	21	:	"NewRake",
	22	:	"4AxleLocoSensed",
}			

#Wagon Weigh Command Description Dict
WagonWeighCommandDict = {
	COMMAND90RES_COMMAND_POSITION		:	"CommandId",
	COMMAND90RES_SIGN_OF_WEIGHT			:	"SignOfWeight",
	COMMAND90RES_WEIGHT_LSB				:	"WeightLSB",
	COMMAND90RES_WEIGHT_MID				:	"WeightMID",
	COMMAND90RES_WEIGHT_MSB				:	"WeightMSB",
	COMMAND90RES_DIRECTION				:	"Direction",
	COMMAND90RES_MESSAGE				:	WagonWeighMessageDict,
	COMMAND90RES_WAGONS_WEIGHED			:	"WagonsWeighed",	#8,9Ignore
	8									:	"Igonore",
	9									:	"Igonore",
	COMMAND90RES_LASTAXLE_LSB			:	"LastAxleLSB",
	COMMAND90RES_LASTAXLE_MSB			:	"LastAxleMSB",
	COMMAND90RES_SPEED_TLPAIR1_LSB		:	"SpeedTLPair1LSB",
	COMMAND90RES_SPEED_TLPAIR1_MSB		:	"SpeedTLPair1MSB",
	COMMAND90RES_SPEED_TLPAIR2_LSB		:	"SpeedTLPair2LSB",
	COMMAND90RES_SPEED_TLPAIR2_MSB		:	"SpeedTLPair2MSB",
	COMMAND90RES_SPEED_FROM_WEIGH_LSB	:	"SpeedFromWeighLSB",
	COMMAND90RES_SPEED_FROM_WEIGH_MSB	:	"SpeedFromWeighMSB",
	COMMAND90RES_AXLECOUNT_PAIR1_LSB	:	"AxleCountPair1LSB",
	COMMAND90RES_AXLECOUNT_PAIR1_MSB	:	"AxleCountPair1MSB",
	COMMAND90RES_AXLECOUNT_PAIR2_LSB	:	"AxleCountPair2LSB",
	COMMAND90RES_AXLECOUNT_PAIR2_MSB	:	"AxleCountPair2MSB",
	COMMAND90RES_AXLECOUNT_PAIR3_LSB	:	"AxleCountPair3LSB",
	COMMAND90RES_AXLECOUNT_PAIR3_MSB	:	"AxleCountPair3MSB",
	COMMAND90RES_AXLECOUNT_PAIR4_LSB	:	"AxleCountPair4LSB",
	COMMAND90RES_AXLECOUNT_PAIR4_MSB	:	"AxleCountPair4MSB",
	COMMAND90RES_AXLE_WEIGHED_LSB		:	"AxleWeightLSB",
	COMMAND90RES_AXLE_WEIGHED_MSB		:	"AxleWeightMSB",	#28,29 Axle weights ignore	
	COMMAND90RES_AXLE_INGNORED_LSB		:	"AxleIgnoreLSB",
	COMMAND90RES_AXLE_INGNORED_MSB		:	"AxleIgnoreMSB",
	COMMAND90RES_WAGON_SERIAL_NUMBER	:	"WagonSerialNumber",
	COMMAND90RES_WAGON_TYPE				:	"WagonType",
	COMMAND90RES_WAGON_WEIGHT_LSB		:	"WagonWeightLSB",
	COMMAND90RES_WAGON_WEIGHT_MID		:	"WagonWeightMID",
	COMMAND90RES_WAGON_WEIGHT_MSB		:	"WagonWeightMSB",
	COMMAND90RES_AXLE1WEIGHT_LSB		:	"Axle1WeightLSB",
	COMMAND90RES_AXLE1WEIGHT_MSB		:	"Axle1WeightMSB",
	COMMAND90RES_AXLE2WEIGHT_LSB		:	"Axle2WeightLSB",
	COMMAND90RES_AXLE2WEIGHT_MSB		:	"Axle2WeightMSB",
	COMMAND90RES_AXLE3WEIGHT_LSB		:	"Axle3WeightLSB",
	COMMAND90RES_AXLE3WEIGHT_MSB		:	"Axle3WeightMSB",
	COMMAND90RES_AXLE4WEIGHT_LSB		:	"Axle4WeightLSB",
	COMMAND90RES_AXLE4WEIGHT_MSB		:	"Axle4WeightMSB",
	COMMAND90RES_WAGON_SPEED_LSB		:	"SpeedOfWagonLSB",
	COMMAND90RES_WAGON_SPEED_MSB		:	"SpeedOfWagonMSB",	
}

#Digital Output status byte desc
CURRENT_OUTPUT_STATUS_LSB			=	1
CURRENT_OUTPUT_STATUS_MSB			=	2
ACTUAL_OUTPUT_STATUS_LSB			=	3
ACTUAL_OUTPUT_STATUS_MSB			=	4

#Digital input status byte desc
CURRENT_INPUT_STATUS_LSB			=	1
CURRENT_INPUT_STATUS_MSB			=	2
ACTUAL_INPUT_STATUS_LSB				=	3
ACTUAL_INPUT_STATUS_MSB				=	4

#Wagon Weigh
SERIAL_NUMBER_OF_WAGON				=	0
TEST_WAGON							=	0
RESOULUTION_LSB						=	20
RESOULUTION_MSB						=	0
WAGON_DATA_VALUE_DIVIDER			=	10
WAGON_WEIGH_COMMAND_PAYLOAD_SIZE	=	4
WAGON_PAYLOAD_LENGTH				=	45
WAGON_EMPTY_SCAN_LENGTH				=	30

WAGON_DATA_PRIORITY					=	1
WAGON_EMPTY_SCAN_PRIORITY			=	2

#command list 
MERIT_TLC_FWVER_LIST = [0x7E,0x01,0x01,0x00,0x50,0xa9,0x60]
MERIT_TLC_FWVER_RELEASEDATE_LIST = [0x7E,0x01,0x01,0x00,0x51,0x20,0x71]

MERIT_STATUS_PAYLOAD_SIZE	   = 2
MERIT_STATUS_HIGH_PERMANENT	 = 0x10
MERIT_STATUS_HIGH_PULSE		 = 0x40
MERIT_STATUS_LOW_PERMANENT	  = 0x20
MERIT_STATUS_LOW_PULSE		  = 0x80
NEGATIVE_WEIGHT_OFFSET	   = 16777216
MAX_RETRY_COUNT = 10

#***********************************************************************************#
#*************** File Variables ****************************************************#
#***********************************************************************************#
m_TLCSerialPort = None				#Serial Object Handle
m_TLCSerialCommandWriteQueue = PriorityQueue(maxsize = 0)
m_WeighmentInitFlag = 0
MqttConnectFlag	= False
m_WagonCount			=	0
m_CurrentWeighmentWagonNumber		=	1
m_PreviousWeighmentWagonNumber		=	0
m_MqttPostCurrentWagonNumber	=	0
m_MqttPostWeighmentInitFlag	=	False
m_TLCMonitorInitFlag = False
m_MeritWagonDetailsDict = {}
m_WagonWeightDataParseDict = {}
m_LocoCount = 0
m_LocoFlag = False
m_TLCStatusFlag = False
m_AXLETOELIMINATE = 0

#BROKER = 'broker.emqx.io'
#BROKER = '192.168.1.145'
BROKER = '10.60.200.209'
#BROKER = '65.0.94.47'
BROKER_PORT = 80
CLIENT_ID = f'python-mqtt-123'
USERNAME = 'emqx2'
PASSWORD = 'public2'
m_HostWGID = 'MBMAGH01'

m_TLCFirmwareVersion = "" 
m_TLCFirmwareReleaseDate = ""
m_TLCPyCodeVersion = "TLC_V1.2.3"
m_TLCPyCodeReleaseDate = "28th October 2023"
m_VersionPostURL = 'http://10.60.200.209:443/version/'
#m_VersionPostURL = 'http://65.0.94.47:443/version/'
m_PostSuccessCode = 200

m_TLCMqttClient = None
m_MqttInitiate = "Initiate"
m_MqttTerminate = "Terminate"
m_MqttReset = "RESET"
m_SB = "SCOREBOARD"
m_SerialCommFailureCount = 0
m_SerialCommErrorFlag = False
m_NoPostFlag = True
m_TLCStatusControlFlag = False

'''
m_MqttWeighmentPostTopic = "/Merit/MBCGL 01/Weighment/"
m_MqttTLCInitTopic = "/Merit/MBCGL 01/COMMAND/"
m_MqttTLCStatusTopic = "/Merit/MBCGL 01/Status/"
m_MqttTLCInputStatusPostTopic = "/Merit/MBCGL 01/InputStatus/"
m_MqttTLCOutputStatusPostTopic = "/Merit/MBCGL 01/OutputStatus/"
m_MqttWagonRequestTopic = "/Merit/Req/"
m_MqttWeightStatusTopic = "/Merit/MBCGL 01/WeightStatus/"
m_MqttStatusControlTopic = "/Merit/MBCGL 01/Status/Control/"
'''
#Mqtt Topics
m_MqttWeighmentPostTopic = "/Merit/MBMAGH01/Weighment/"
m_MqttTLCInitTopic = "/Merit/MBMAGH01/COMMAND/"
m_MqttTLCStatusTopic = "/Merit/MBMAGH01/Status/"
m_MqttTLCInputStatusPostTopic = "/Merit/MBMAGH01/InputStatus/"
m_MqttTLCOutputStatusPostTopic = "/Merit/MBMAGH01/OutputStatus/"
m_MqttWagonRequestTopic = "/Merit/MBMAGH01/Weighment/sendFrom/"
m_MqttWeightStatusTopic = "/Merit/MBMAGH01/WeightStatus/"
m_MqttStatusControlTopic = "/Merit/MBMAGH01/Status/Control/"
m_MqttMeritScoreBoardAvailablityTopic = "/Merit/MBMAGH01/ScoreBoard/" 
m_ErrorStatusTopic = "/Merit/MBMAGH01/ErrorStatus/" 

m_MeritPort = ""
m_WagonStartTime = ""
LOG_FILE_NAME	=	'./MeritLogs.log'
logging.basicConfig(filename= LOG_FILE_NAME, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Creating an object
m_TLCLogger = logging.getLogger()
# Setting the threshold of logger to DEBUG
m_TLCLogger.setLevel(logging.DEBUG)	
		
#***********************************************************************************#
#******************************* Functions *****************************************#
#***********************************************************************************#
#********************************************************************************************#	
#********************************************************************************************#
#Description : Function to find the TLC Port
#Arguments : None
#Return : TLC Portname
#********************************************************************************************#
def Merit_FindTLCPort():
	global m_TLCSerialPort
	comPortsList = list_ports.comports()
	portname = ""
	for comport in comPortsList:
		try:
			m_TLCSerialPort = serial.Serial(
				port = comport.name, baudrate = MERIT_SERIAL_BAUD_RATE, bytesize = MERIT_SERIAL_DATABITS, parity = MERIT_SERIAL_PARITY, 
				stopbits = MERIT_SERIAL_STOPBITS, timeout = MERIT_SERIAL_TIMEOUT, interCharTimeout = MERIT_SERIAL_INTER_CHAR_TIMEOUT)
			result = m_TLCSerialPort.write(MERIT_TLC_FWVER_LIST)
			data = m_TLCSerialPort.readline()
			if(data):
				portname = comport.name
				logging.info("TLC COM Port Found. Port : " + str(portname))
				print("TLC COM Port Found. Port : " + str(portname))
				break
			else:
				print("No Response from Port : " + str(comport.name))
				logging.error("No Response from Port : " + str(comport.name))
				data = m_TLCSerialPort.close()
		except serial.SerialException as e:
			logging.error(str(e))   
		except Exception as ex:
			logging.error(str(ex))
			pass	
	return portname

#********************************************************************************************#
#Description : function to write wagon weighment read command & read input and output status over the TLC
#Arguments : None
#Return : None
#********************************************************************************************#
def Merit_TLCMonitor():
	global m_TLCMonitorInitFlag
	global m_TLCStatusFlag
	if(m_TLCMonitorInitFlag == True):
		m_TLCStatusFlag = False
		Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [0,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, WAGON_EMPTY_SCAN_PRIORITY)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
		Merit_WriteCommand(MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD, [], 0, WAGON_EMPTY_SCAN_PRIORITY)		
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
		Merit_WriteCommand(MERIT_DIGITAL_INPUT_STATUS_READ_CMD, [], 0, WAGON_EMPTY_SCAN_PRIORITY)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	else:
		Merit_Status(WAGON_EMPTY_SCAN_PRIORITY)

#********************************************************************************************#
#Description : function to initiate variables
#Arguments : None
#Return : None
#********************************************************************************************#
def Merit_VariableInit():
	global m_SerialCommFailureCount
	global m_WagonCount
	global m_CurrentWeighmentWagonNumber	
	global m_PreviousWeighmentWagonNumber	
	global m_MqttPostCurrentWagonNumber
	global m_MqttPostWeighmentInitFlag
	global m_WeighmentInitFlag
	#global m_TLCMonitorInitFlag
	#global MqttConnectFlag	= False
	global m_MeritWagonDetailsDict
	global m_WagonWeightDataParseDict
	global m_LocoCount 
	global m_LocoFlag
	global m_TLCStatusFlag 
	global m_AXLETOELIMINATE
	global m_MeritPort
	global m_WagonStartTime
	global m_TLCSerialCommandWriteQueue
	global m_SerialCommErrorFlag
	global m_TLCStatusControlFlag
	
	m_TLCSerialCommandWriteQueue.queue.clear()
	m_WagonCount			=	0
	m_CurrentWeighmentWagonNumber		=	1
	m_PreviousWeighmentWagonNumber		=	0
	m_MqttPostCurrentWagonNumber	=	0
	m_MqttPostWeighmentInitFlag	=	False
	m_WeighmentInitFlag = 0
	m_MeritWagonDetailsDict = {}
	m_WagonWeightDataParseDict = {}
	m_LocoCount = 0
	m_LocoFlag = False
	m_TLCStatusFlag = False
	m_MeritPort = ""
	m_WagonStartTime = ""
	m_SerialCommFailureCount = 0
	m_SerialCommErrorFlag = False
	m_TLCStatusControlFlag = False
	
#********************************************************************************************#
#Description : function to initiate the TLC Weighment Process
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_Init():
	global m_TLCSerialCommandWriteQueue
	global m_TLCMonitorInitFlag
	global m_NoPostFlag
	
	with m_TLCSerialCommandWriteQueue.mutex:
		logging.info(str("******************** QUEUE CLEARED **********************\n"))
		m_TLCSerialCommandWriteQueue.queue.clear()
	logging.info("MERIT Init Command Send to TLC Controller")
	time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	Merit_WriteCommand(MERIT_INIT_AND_AXLE_ELIMINATE_WRITE_CMD, [m_AXLETOELIMINATE], 1, WAGON_DATA_PRIORITY)
	time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	Merit_VariableInit()
	m_TLCMonitorInitFlag = True
	m_NoPostFlag = False
	
#********************************************************************************************#
#Description : function to Terminate the TLC Weighment Process
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_Terminate():
	global m_TLCSerialCommandWriteQueue
	global m_TLCMonitorInitFlag
	global m_NoPostFlag
	
	with m_TLCSerialCommandWriteQueue.mutex:
		logging.info(str("******************** QUEUE CLEARED **********************\n"))
		m_TLCSerialCommandWriteQueue.queue.clear()	
	logging.info("MERIT Terminate Command Send to TLC Controller")
	time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	Merit_WriteCommand(MERIT_TERMINATE_WRITE_CMD, [], 0, WAGON_DATA_PRIORITY)
	time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	Merit_VariableInit()
	m_TLCMonitorInitFlag = False
	m_NoPostFlag = True	
	
#********************************************************************************************#
#Description : Function to write TLC Read command over Serial Port
#Arguments : Command, Queue Priority
#Return : None
#********************************************************************************************#		
def Merit_ReadCommand(Command, QueuePriority):
	global m_TLCSerialCommandWriteQueue
	ReadSortQueue = []
	InputReadCommandList = []
	InputReadCommandList.append(MERIT_START_BYTE)
	InputReadCommandList.append(MERIT_RTUID_BYTE)
	InputReadCommandList.append(0x01)
	InputReadCommandList.append(0x00)
	InputReadCommandList.append(Command)
	InputCheckSum = Merit_ChecksumForList(InputReadCommandList)
	InputReadCommandList.append(InputCheckSum & 0xff)
	InputReadCommandList.append(InputCheckSum >> 8)
	ReadSortQueue.append(datetime.datetime.now())
	ReadSortQueue.append(InputReadCommandList)
	m_TLCSerialCommandWriteQueue.put((QueuePriority, ReadSortQueue))

#********************************************************************************************#
#Description : Function to write TLC Write command over Serial port 
#Arguments : Command , Payload and length of payload, Queue Priority
#Return : None
#********************************************************************************************#	
def Merit_WriteCommand(Command, Payload, Length, QueuePriority):
	global m_TLCSerialCommandWriteQueue
	WriteSortQueue = []
	InputWriteCommandList = []
	InputWriteCommandList.append(MERIT_START_BYTE)
	InputWriteCommandList.append(MERIT_RTUID_BYTE)
	InputWriteCommandList.append(Length + 1)	#command + payload 
	InputWriteCommandList.append(0x00)
	InputWriteCommandList.append(Command)
	InputWriteCommandList = InputWriteCommandList + Payload
	InputCheckSum = Merit_ChecksumForList(InputWriteCommandList)
	InputWriteCommandList.append(InputCheckSum & 0xff)
	InputWriteCommandList.append(InputCheckSum >> 8)
	WriteSortQueue.append(datetime.datetime.now())
	WriteSortQueue.append(InputWriteCommandList)
	m_TLCSerialCommandWriteQueue.put((QueuePriority, WriteSortQueue))	
	
#********************************************************************************************#
#Description : Function to remove stuff byte(0x10) from the list
#Arguments : Input List
#Return : List after removing stuff byte
#********************************************************************************************#
def Merit_RemoveStuffBytes(InputList):
	newList = []
	Index = 0

	while Index < len(InputList):
		if(Index == len(InputList) - 1):
			newList.append(InputList[Index])
			break
		if (InputList[Index] == MERIT_ADDITIONAL_BYTE):
			checkItem = InputList[Index + 1]
			if(checkItem == MERIT_ADDITIONAL_BYTE or checkItem == MERIT_START_BYTE):
				newList.append(checkItem)
				Index = Index + 1
		else:
			newList.append(InputList[Index])
		Index = Index + 1
	return newList

#********************************************************************************************#
#Description : Function to add stuff byte (0x10) to the list if there is 0x10 or 0x7E byte
#Arguments : input list
#Return :  List after adding Stuff byte
#********************************************************************************************#
def Merit_AddStuffBytes(InputList):
	newList = [MERIT_START_BYTE]
	for index, elem in enumerate(InputList[1:]):
		if (elem == MERIT_START_BYTE) or (elem == MERIT_ADDITIONAL_BYTE):
			newList.append(MERIT_ADDITIONAL_BYTE)
			newList.append(elem)
		else:
			newList.append(elem)
	return newList	
	
#********************************************************************************************#
#Description : Function to calculate checksum for command list checksum and element from crc16 table
#Arguments : CSum - command list CheckSum, Element - List Element
#Return : CheckSum 
#********************************************************************************************#
def Merit_GetCheckSum(Csum, Element):
	index = ((Csum ^ Element) & 0x00ff)
	NewCSum = ((Csum & 0xff00) >> 8) ^ CRC16_TABLE[index]
	return NewCSum
	
#********************************************************************************************#
#Description : Function to calculate checksum for list
#Arguments : Input List to calculate checksum
#Return : CheckSum for the input list
#********************************************************************************************#	
def Merit_ChecksumForList(InputList):
	CheckSum = 0 
	for Element in InputList:
		CheckSum = Merit_GetCheckSum(CheckSum, Element)	
	return CheckSum

#********************************************************************************************#
#Description : Function to write TLC commands over Serial Port via queue
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_SerialWriterQueue():
	global m_TLCSerialPort
	global m_TLCSerialCommandWriteQueue
	global m_SerialCommFailureCount
	global m_SerialCommErrorFlag
	global m_TLCMqttClient
	global m_ErrorStatusTopic
	
	ErrorMsgDict = {}
	ErrorMsgDict["ErrorMessage"] = "SerialCommuncationFailed"
	
	while(1):
		while(not m_TLCSerialCommandWriteQueue.empty()):
			try:
				m_SerialCommFailureCount = 0
				data = list(m_TLCSerialCommandWriteQueue.get())
				InputReadCommandList = data[1][1]
				Command = InputReadCommandList[MERIT_COMMAND_ID_POSITION]
				for i in range(MAX_RETRY_COUNT):
					try:
						print("Command to send : " + str(Command))
						logging.info("Command to send : " + str(Command))
						result = m_TLCSerialPort.write(Merit_AddStuffBytes(InputReadCommandList))
						#print("Send Bytes From Queue", Merit_AddStuffBytes(InputReadCommandList))
						logging.info("Serial Command Packet : " + str(Merit_AddStuffBytes(InputReadCommandList)))
						if(Merit_SerialRead100ms(Command) == False):
							m_SerialCommFailureCount = m_SerialCommFailureCount + 1;
							if(m_SerialCommFailureCount >= MAX_RETRY_COUNT):
								#Merit_Publish(m_TLCMqttClient, m_ErrorStatusTopic, json.dumps(m_WagonWeightDataParseDict))
								m_TLCMqttClient.publish(m_ErrorStatusTopic, json.dumps(m_WagonWeightDataParseDict))
								m_SerialCommErrorFlag = True
								time.sleep(1)
							else:
								continue
						m_SerialCommFailureCount = 0
						break
					except serial.SerialException as e:
						m_SerialCommFailureCount = m_SerialCommFailureCount + 1;
						logging.error(str(e))
						if(m_SerialCommFailureCount >= MAX_RETRY_COUNT):
							m_TLCMqttClient.publish(m_ErrorStatusTopic, json.dumps(m_WagonWeightDataParseDict))
							m_SerialCommErrorFlag = True
							time.sleep(1)
						else:
							continue
				
			except Exception as ex:
				logging.error(str(ex))
			time.sleep(0.01)
		time.sleep(0.001)
		
#********************************************************************************************#
#Description : Function to get tlc firmware version and Release date over serial port
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_SerialWriterVersionRequesAndDate(): 
	try:
		Merit_WriteCommand(MERIT_VERSION_OF_CODE_READ_CMD, [], 0, WAGON_DATA_PRIORITY)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
		Merit_WriteCommand(MERIT_CODE_RELAESE_DATE_READ_CMD, [], 0, WAGON_DATA_PRIORITY)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	except Exception as ex:
		logging.error(str(ex))
	
#********************************************************************************************#
#Description : function to read the serial port for given command 
#Arguments : Command to read
#Return : None
#********************************************************************************************#		
def Merit_SerialRead100ms(Command):
	global m_TLCSerialPort
	LengthOfQuery = 0
	dataAfterDublicateList = []
	ReceiveSuccessFlag = MERIT_READ_TIMEOUT
	StartTime = datetime.datetime.now()
	EndTime = 0
	Status = True
	
	try:
		if(True):
			try:
				ReceiveSuccessFlag = MERIT_READ_TIMEOUT
				data = m_TLCSerialPort.read(MERIT_SERIAL_MAX_BYTES_TO_RECEIVE)
				EndTime = (datetime.datetime.now() - StartTime).total_seconds()
				logging.info("******** Time Taken To Read : " + str(EndTime) + " **************")
					
				logging.info("Data Read : " + str(list(data)) + "Length : " + str(len(list(data))))
				if(len(list(data)) > 0):
					dataAfterDublicateList = Merit_RemoveStuffBytes(data)
					if(dataAfterDublicateList[MERIT_HEADER_ID_POSITION] == MERIT_START_BYTE):
						if(dataAfterDublicateList[MERIT_RTU_ID_POSITION] == MERIT_RTUID_BYTE):
							LengthOfQuery = (dataAfterDublicateList[MERIT_QUERY_LEN_POSITION] + (dataAfterDublicateList[MERIT_QUERY_LEN_POSITION + 1] << 8)) 
							if(dataAfterDublicateList[MERIT_COMMAND_ID_POSITION] == Command):
								if(len(dataAfterDublicateList) == (MERIT_COMMAND_ID_POSITION + LengthOfQuery + 2 )):
									GivenchecksumList = dataAfterDublicateList[(LengthOfQuery + MERIT_COMMAND_ID_POSITION) : ] 
									Givenchecksum = GivenchecksumList[0] | (GivenchecksumList[1] << 8)
									DataCheckSum = Merit_ChecksumForList(dataAfterDublicateList[ : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
									if(Givenchecksum == DataCheckSum):
										listToStr = ' '.join([chr(elem) for elem in dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION + 1) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)]])
										#print("Rec Data in String : ", listToStr)
										ReceiveSuccessFlag = MERIT_READ_SUCCESS
										if(Command == MERIT_WAGON_WEIGHT_WRITE_CMD):
											Merit_WeighmentResponseParse(dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION ) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
										if(Command == MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD):
											Merit_DigitalOutputStatusParse(dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION ) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
										if(Command == MERIT_DIGITAL_INPUT_STATUS_READ_CMD):
											Merit_DigitalInputStatusParse(dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION ) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
										if(Command == MERIT_INIT_AND_AXLE_ELIMINATE_WRITE_CMD):
											logging.info("MERIT TLC INITIATED SUCCESSFULLY")
										if(Command == MERIT_TERMINATE_WRITE_CMD):
											logging.info("MERIT TLC TERMINATED SUCCESSFULLY")
										if(Command == MERIT_VERSION_OF_CODE_READ_CMD):
											Merit_VersionReqParse(dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION ) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
										if(Command == MERIT_CODE_RELAESE_DATE_READ_CMD):
											Merit_VersionReleaseDataReqParse(dataAfterDublicateList[ (MERIT_COMMAND_ID_POSITION ) : (LengthOfQuery + MERIT_COMMAND_ID_POSITION)])
										if(Command == MERIT_OUTPUT_STATUS_WRITE_CMD):   
											logging.info("Output Status Control Command Initiated")
										if(Command == MERIT_OUTPUT_STATUS_RESET_WRITE_CMD):
											logging.info("Output Status Reset Command Initiated")
										if(Command == MERIT_SCOREBOARD_AVAIL_WRITE_CMD):
											logging.info("Merit ScoreBoard Avail Command Written")	
									else:
										ReceiveSuccessFlag = MERIT_CHECKSUM_MISMATCH
								else:
									ReceiveSuccessFlag = MERIT_DATALEN_MISMATCH
							else:
								ReceiveSuccessFlag = MERIT_COMMAND_MISMATCH
						else:
							ReceiveSuccessFlag = MERIT_RTUID_MISMATCH
					else:
						ReceiveSuccessFlag = MERIT_HEADER_MISMATCH
				else:
					ReceiveSuccessFlag = MERIT_READ_TIMEOUT
					
				if(ReceiveSuccessFlag != MERIT_READ_SUCCESS):
					#Status = False
					logging.error("******************** Error While Read : " + str(MeritSerialRecvErrorDict[ReceiveSuccessFlag]) + "********************")
				logging.info(str("**********************************************************\n") + str("\n\n"))	
			except serial.SerialException as e:
				logging.error(str(e)) 
				Status = False
					#Publish		 
	except Exception as ex:
		logging.error("******************** Exception : , data : " + str(ex) + str(dataAfterDublicateList) + " *******************************")
		Status = False
	return Status	
		
#********************************************************************************************#
#Description : Function to parse the wagon weight command response
#Arguments : WagonWeighData list
#Return : None
#********************************************************************************************#
def Merit_WeighmentResponseParse(WagonWeighDataList):
	global m_WeighmentInitFlag
	global m_CurrentWeighmentWagonNumber
	global m_PreviousWeighmentWagonNumber
	global m_MqttPostCurrentWagonNumber
	global m_WagonCount 
	global m_MqttPostWeighmentInitFlag
	global m_LocoCount
	global m_LocoFlag
	global m_MeritWagonDetailsDict
	global UNKNOWN_VEHICLE
	global m_TLCMqttClient
	global m_WagonWeightDataParseDict
	global m_WagonStartTime
	global m_TLCStatusFlag
	
	
	AXLEWeightList = []
	AxleWeighOverFalg = True
	DefaultWeightDict = {}
	
	try:
		if(m_TLCStatusFlag == False):
			if((m_CurrentWeighmentWagonNumber == m_PreviousWeighmentWagonNumber ) and len(WagonWeighDataList) >= WAGON_PAYLOAD_LENGTH) :
				WagonSerialNumber = WagonWeighDataList[COMMAND90RES_WAGON_SERIAL_NUMBER]
				logging.info("Current Wagon to weighment " +  str(m_CurrentWeighmentWagonNumber) + " Received WagonSerialNumber : " + str( WagonSerialNumber))
				if(not( WagonWeighDataList[COMMAND90RES_MESSAGE] == UNKNOWN_VEHICLE)):
					if(WagonSerialNumber == m_CurrentWeighmentWagonNumber):
						logging.info("Message : ---------------- " + str(WagonWeighDataList[COMMAND90RES_MESSAGE]) + " ----------------------------")
						int(np.array(WagonWeighDataList[COMMAND90RES_WAGON_TYPE]).astype(np.int8))
						logging.info("Wagon Response Packet " + str(WagonWeighDataList) )
						WagonType = int(np.array(WagonWeighDataList[COMMAND90RES_WAGON_TYPE]).astype(np.int8))		 
						
						
						if((WagonType == THREE_AXLE_LOCO) or (WagonType == FOUR_AXLE_LOCO)):
							m_LocoCount = m_LocoCount + 1	
						else:
							AXLEWeightList.insert(0, int(np.array((WagonWeighDataList[COMMAND90RES_AXLE1WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE1WEIGHT_LSB]).astype(np.int16)))
							AXLEWeightList.insert(1, int(np.array((WagonWeighDataList[COMMAND90RES_AXLE2WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE2WEIGHT_LSB]).astype(np.int16)))
							AXLEWeightList.insert(2, int(np.array((WagonWeighDataList[COMMAND90RES_AXLE3WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE3WEIGHT_LSB]).astype(np.int16)))
							AXLEWeightList.insert(3, int(np.array((WagonWeighDataList[COMMAND90RES_AXLE4WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE4WEIGHT_LSB]).astype(np.int16)))
							for i in range(WagonType):
								if((AXLEWeightList[i] == -3) or (AXLEWeightList[i] == -4)):
									AxleWeighOverFalg = False
						
						logging.info("Current Wagon : " +  str(m_CurrentWeighmentWagonNumber) + ", AXLEWeightList : " + str(AXLEWeightList))
						m_WagonWeightDataParseDict = Merit_WagonWeightDataParse(WagonWeighDataList)
						if(AxleWeighOverFalg == True):
							m_WagonWeightDataParseDict["StartTime"] = m_WagonStartTime
							m_WagonWeightDataParseDict["EndTime"] = str(datetime.datetime.now())
							m_WagonWeightDataParseDict["WE"] = True
						if((AxleWeighOverFalg == False) or ((WagonType == THREE_AXLE_LOCO) or (WagonType == FOUR_AXLE_LOCO))):
							Merit_Publish(m_TLCMqttClient, m_MqttWeighmentPostTopic, json.dumps(m_WagonWeightDataParseDict))
							#Status
							Merit_WriteCommand(MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD, [], 0, WAGON_DATA_PRIORITY)		
							time.sleep(MERIT_QUERY_DELAY)
							Merit_WriteCommand(MERIT_DIGITAL_INPUT_STATUS_READ_CMD, [], 0, WAGON_DATA_PRIORITY)
							time.sleep(MERIT_QUERY_DELAY)
						 
						if(AxleWeighOverFalg == True):
							m_WeighmentInitFlag = 1
							if((WagonType != THREE_AXLE_LOCO) and (WagonType != FOUR_AXLE_LOCO)):
								m_MeritWagonDetailsDict[WagonSerialNumber - m_LocoCount] =  json.dumps(m_WagonWeightDataParseDict)
								if(m_MqttPostWeighmentInitFlag == False):
									m_MqttPostWeighmentInitFlag = True
									m_MqttPostCurrentWagonNumber = WagonSerialNumber - m_LocoCount	
							logging.info(str("*********\n") + str("Read Done : Serial Number") + str(m_CurrentWeighmentWagonNumber) )
							m_CurrentWeighmentWagonNumber = m_CurrentWeighmentWagonNumber + 1
							m_PreviousWeighmentWagonNumber = m_PreviousWeighmentWagonNumber + 1	
							#Status
							Merit_WriteCommand(MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD, [], 0, WAGON_DATA_PRIORITY)		
							time.sleep(MERIT_QUERY_DELAY)
							Merit_WriteCommand(MERIT_DIGITAL_INPUT_STATUS_READ_CMD, [], 0, WAGON_DATA_PRIORITY)
							time.sleep(MERIT_QUERY_DELAY)
							logging.info(str("*********\n") +  str("Next Read Serial Number") + str(m_CurrentWeighmentWagonNumber) )
						else:
							time.sleep(MERIT_QUERY_DELAY)
							Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [m_CurrentWeighmentWagonNumber,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, WAGON_DATA_PRIORITY)
							return "READ AGAIN"
				else:
					logging.info("Message : ---------------- " + str(WagonWeighDataList[COMMAND90RES_MESSAGE]) + " ----------------------------")
					m_WagonWeightDataParseDict = Merit_WagonWeightDataParse(WagonWeighDataList)
					m_WagonWeightDataParseDict["StartTime"] = m_WagonStartTime
					m_WagonWeightDataParseDict["EndTime"] = str(datetime.datetime.now())
					Merit_Publish(m_TLCMqttClient, m_MqttWeighmentPostTopic, json.dumps(m_WagonWeightDataParseDict))
					logging.info("Unknown Vechile Message : " + str(json.dumps(m_WagonWeightDataParseDict)))
					Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [m_CurrentWeighmentWagonNumber,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, WAGON_DATA_PRIORITY)
					return "READ AGAIN"
			
			m_WagonCount = WagonWeighDataList[COMMAND90RES_WAGONS_WEIGHED]
			logging.info("WagonCount : " + str(m_WagonCount))
			if((m_WagonCount > m_PreviousWeighmentWagonNumber) and (m_WeighmentInitFlag == 0) ):
				with m_TLCSerialCommandWriteQueue.mutex:
					m_TLCSerialCommandWriteQueue.queue.clear()
				time.sleep(MERIT_QUERY_DELAY)
				m_WagonStartTime = str(datetime.datetime.now())
				Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [m_CurrentWeighmentWagonNumber,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, WAGON_DATA_PRIORITY)		
				if(m_PreviousWeighmentWagonNumber == 0):
					m_PreviousWeighmentWagonNumber = m_PreviousWeighmentWagonNumber + 1		
			elif((m_WagonCount >= m_CurrentWeighmentWagonNumber) and (m_CurrentWeighmentWagonNumber == m_PreviousWeighmentWagonNumber) ):
				time.sleep(MERIT_QUERY_DELAY)
				m_WagonStartTime = str(datetime.datetime.now())
				Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [m_CurrentWeighmentWagonNumber,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, WAGON_DATA_PRIORITY)
			else:
				m_WagonWeightDataParseDict = Merit_ContinuousWeighmentPostData(WagonWeighDataList)
				Merit_Publish(m_TLCMqttClient, m_MqttWeighmentPostTopic, json.dumps(m_WagonWeightDataParseDict))
		else:
			WagonCount = WagonWeighDataList[COMMAND90RES_WAGONS_WEIGHED]
			DefaultWeightDict = Merit_DefaultWeightParse(WagonWeighDataList, WagonCount)
			Merit_Publish(m_TLCMqttClient, m_MqttWeightStatusTopic, json.dumps(DefaultWeightDict))
			
	except Exception as ex:
		logging.error("Exception While weight Rec: " + str(ex))

#********************************************************************************************#
#Description : Function to parse the Default weight
#Arguments : WagonWeighData list
#Return : Wagon Weighment Dictionary
#********************************************************************************************#
def Merit_DefaultWeightParse(WagonWeighDataList, WagonCount):
	WagonDict = {}
	
	WagonDict["SignOfWeight"] = ""
	WagonDict["Weight"] = "WL.Mode"
	
	if(WagonCount == 0):
		SignOfWeight = chr(WagonWeighDataList[COMMAND90RES_SIGN_OF_WEIGHT])
		Weight  = (WagonWeighDataList[COMMAND90RES_WEIGHT_MSB] << 16) + (WagonWeighDataList[COMMAND90RES_WEIGHT_MID] << 8) + WagonWeighDataList[COMMAND90RES_WEIGHT_LSB]
		WagonDict["SignOfWeight"] = SignOfWeight
		if(SignOfWeight == "+"):
			Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
			WagonDict["Weight"] = Weight
		elif(SignOfWeight == "-"):
			Weight = NEGATIVE_WEIGHT_OFFSET - Weight;
			Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
			WagonDict["Weight"] = Weight	
		print("Weight On Status Control Page : ", Weight)
	return WagonDict

#********************************************************************************************#
#Description : Function to parse the weighment response details
#Arguments : WagonWeighData list
#Return : Weighment Dictionary
#********************************************************************************************#
def Merit_ContinuousWeighmentPostData(WagonWeighDataList):
	WagonDict = {}
	
	SignOfWeight = chr(WagonWeighDataList[COMMAND90RES_SIGN_OF_WEIGHT])
	Weight  = (WagonWeighDataList[COMMAND90RES_WEIGHT_MSB] << 16) + (WagonWeighDataList[COMMAND90RES_WEIGHT_MID] << 8) + WagonWeighDataList[COMMAND90RES_WEIGHT_LSB]
	LastAxle = (WagonWeighDataList[COMMAND90RES_LASTAXLE_MSB] << 8) + WagonWeighDataList[COMMAND90RES_LASTAXLE_LSB]
	SpeedTLPair1 = (WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR1_MSB] << 8) + WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR1_LSB]
	SpeedTLPair1 = SpeedTLPair1 / WAGON_DATA_VALUE_DIVIDER
	SpeedTLPair2 = (WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR2_MSB] << 8) + WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR2_LSB]
	SpeedTLPair2 = SpeedTLPair2 / WAGON_DATA_VALUE_DIVIDER
	SpeedFromWeigh = (WagonWeighDataList[COMMAND90RES_SPEED_FROM_WEIGH_MSB] << 8)+ WagonWeighDataList[COMMAND90RES_SPEED_FROM_WEIGH_LSB]
	SpeedFromWeigh = SpeedFromWeigh / WAGON_DATA_VALUE_DIVIDER
	AxleCountPair1 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR1_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR1_LSB]
	AxleCountPair2 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR2_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR2_LSB]
	AxleCountPair3 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR3_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR3_LSB]
	AxleCountPair4 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR4_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR4_LSB]
	AxleWeight	   = (WagonWeighDataList[COMMAND90RES_AXLE_WEIGHED_MSB] << 8) +WagonWeighDataList[ COMMAND90RES_AXLE_WEIGHED_LSB]
	AxleIgnore 	   = (WagonWeighDataList[COMMAND90RES_AXLE_INGNORED_MSB] << 8) +WagonWeighDataList[ COMMAND90RES_AXLE_INGNORED_LSB]
	WagonDict["SignOfWeight"] = SignOfWeight
	WagonDict["Weight"] = Weight
	if(SignOfWeight == "+"):
		Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
		WagonDict["Weight"] = Weight
	elif(SignOfWeight == "-"):
		Weight = NEGATIVE_WEIGHT_OFFSET - Weight;
		Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
		WagonDict["Weight"] = Weight	
	
	WagonDict["Message"] = WagonWeighCommandDict[COMMAND90RES_MESSAGE][WagonWeighDataList[COMMAND90RES_MESSAGE]]
	WagonDict["Direction"] = WagonWeighDataList[COMMAND90RES_DIRECTION]
	WagonDict["WagonsWeighed"] = WagonWeighDataList[COMMAND90RES_WAGONS_WEIGHED]
	WagonDict["LastAxle"] = LastAxle
	WagonDict["SpeedTLPair1"] = SpeedTLPair1
	WagonDict["SpeedTLPair2"] = SpeedTLPair2
	WagonDict["SpeedFromWeigh"] = SpeedFromWeigh
	WagonDict["AxleCountPair1"] = AxleCountPair1
	WagonDict["AxleCountPair2"] = AxleCountPair2
	WagonDict["AxleCountPair3"] = AxleCountPair3
	WagonDict["AxleCountPair4"] = AxleCountPair4
	WagonDict["AxleWeight"] = AxleWeight
	WagonDict["AxleIgnore"] = AxleIgnore
	return WagonDict
		
#********************************************************************************************#
#Description : Function to parse the wagon weight response details
#Arguments : WagonWeighData list
#Return : Wagon Weighment Dictionary
#********************************************************************************************#
def Merit_WagonWeightDataParse(WagonWeighDataList):
	global m_CurrentWeighmentWagonNumber
	global m_PreviousWeighmentWagonNumber
	global m_LocoCount
	global m_LocoFlag
	
	WagonDict = {}
	JsonRespString = ""
	
	WagonSerialNumber = WagonWeighDataList[COMMAND90RES_WAGON_SERIAL_NUMBER]
	WagonType	= int(np.array(WagonWeighDataList[COMMAND90RES_WAGON_TYPE]).astype(np.int8))		
	WagonWeight = (WagonWeighDataList[COMMAND90RES_WAGON_WEIGHT_MSB] << 16) + (WagonWeighDataList[COMMAND90RES_WAGON_WEIGHT_MID] << 8) + WagonWeighDataList[COMMAND90RES_WAGON_WEIGHT_LSB]
	WagonWeight	= WagonWeight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
	Axle1Weight = ((WagonWeighDataList[COMMAND90RES_AXLE1WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE1WEIGHT_LSB]) / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
	Axle2Weight = ((WagonWeighDataList[COMMAND90RES_AXLE2WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE2WEIGHT_LSB]) / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
	Axle3Weight = ((WagonWeighDataList[COMMAND90RES_AXLE3WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE3WEIGHT_LSB]) / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
	Axle4Weight = ((WagonWeighDataList[COMMAND90RES_AXLE4WEIGHT_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLE4WEIGHT_LSB]) / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
	WagonSpeed 	= (WagonWeighDataList[COMMAND90RES_WAGON_SPEED_MSB] << 8) + WagonWeighDataList[COMMAND90RES_WAGON_SPEED_LSB]
	WagonSpeed	= WagonSpeed / WAGON_DATA_VALUE_DIVIDER	
	WagonDict["WagonSerialNumber"] = WagonSerialNumber - m_LocoCount
	if((WagonType == THREE_AXLE_LOCO) or (WagonType == FOUR_AXLE_LOCO)):
		WagonDict["WagonSerialNumber"] = 0
	WagonDict["WagonType"] = WagonType
	WagonDict["WagonWeight"] = WagonWeight
	WagonDict["WagonSpeed"] = WagonSpeed
	WagonDict["Axle1Weight"] = Axle1Weight
	WagonDict["Axle2Weight"] = Axle2Weight
	WagonDict["Axle3Weight"] = Axle3Weight
	WagonDict["Axle4Weight"] = Axle4Weight
	SignOfWeight = chr(WagonWeighDataList[COMMAND90RES_SIGN_OF_WEIGHT])
	Weight  = (WagonWeighDataList[COMMAND90RES_WEIGHT_MSB] << 16) + (WagonWeighDataList[COMMAND90RES_WEIGHT_MID] << 8) + WagonWeighDataList[COMMAND90RES_WEIGHT_LSB]
	LastAxle = (WagonWeighDataList[COMMAND90RES_LASTAXLE_MSB] << 8) + WagonWeighDataList[COMMAND90RES_LASTAXLE_LSB]
	SpeedTLPair1 = (WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR1_MSB] << 8) + WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR1_LSB]
	SpeedTLPair1 = SpeedTLPair1 / WAGON_DATA_VALUE_DIVIDER
	SpeedTLPair2 = (WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR2_MSB] << 8) + WagonWeighDataList[COMMAND90RES_SPEED_TLPAIR2_LSB]
	SpeedTLPair2 = SpeedTLPair2 / WAGON_DATA_VALUE_DIVIDER
	SpeedFromWeigh = (WagonWeighDataList[COMMAND90RES_SPEED_FROM_WEIGH_MSB] << 8)+ WagonWeighDataList[COMMAND90RES_SPEED_FROM_WEIGH_LSB]
	SpeedFromWeigh = SpeedFromWeigh / WAGON_DATA_VALUE_DIVIDER
	AxleCountPair1 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR1_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR1_LSB]
	AxleCountPair2 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR2_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR2_LSB]
	AxleCountPair3 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR3_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR3_LSB]
	AxleCountPair4 = (WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR4_MSB] << 8) + WagonWeighDataList[COMMAND90RES_AXLECOUNT_PAIR4_LSB]
	AxleWeight	   = (WagonWeighDataList[COMMAND90RES_AXLE_WEIGHED_MSB] << 8) +WagonWeighDataList[ COMMAND90RES_AXLE_WEIGHED_LSB]
	AxleIgnore 	   = (WagonWeighDataList[COMMAND90RES_AXLE_INGNORED_MSB] << 8) +WagonWeighDataList[ COMMAND90RES_AXLE_INGNORED_LSB]
	WagonDict["SignOfWeight"] = SignOfWeight
	WagonDict["Weight"] = Weight
	if(SignOfWeight == "+"):
		Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
		WagonDict["Weight"] = Weight
	elif(SignOfWeight == "-"):
		Weight = NEGATIVE_WEIGHT_OFFSET - Weight;
		Weight = Weight / (WAGON_DATA_VALUE_DIVIDER * WAGON_DATA_VALUE_DIVIDER)
		WagonDict["Weight"] = Weight	
	
	WagonDict["Message"] = WagonWeighCommandDict[COMMAND90RES_MESSAGE][WagonWeighDataList[COMMAND90RES_MESSAGE]]
	WagonDict["Direction"] = WagonWeighDataList[COMMAND90RES_DIRECTION]
	WagonDict["WagonsWeighed"] = WagonWeighDataList[COMMAND90RES_WAGONS_WEIGHED]
	WagonDict["LastAxle"] = LastAxle
	WagonDict["SpeedTLPair1"] = SpeedTLPair1
	WagonDict["SpeedTLPair2"] = SpeedTLPair2
	WagonDict["SpeedFromWeigh"] = SpeedFromWeigh
	WagonDict["AxleCountPair1"] = AxleCountPair1
	WagonDict["AxleCountPair2"] = AxleCountPair2
	WagonDict["AxleCountPair3"] = AxleCountPair3
	WagonDict["AxleCountPair4"] = AxleCountPair4
	WagonDict["AxleWeight"] = AxleWeight
	WagonDict["AxleIgnore"] = AxleIgnore
	WagonDict["WE"] = False
	return WagonDict

#********************************************************************************************#
#Description : Function to read the input and output status of TLC
#Arguments : Priority of command 
#Return : None
#********************************************************************************************#	
def Merit_Status(Priority):
	global m_TLCStatusFlag 
	global m_NoPostFlag
	
	if(m_NoPostFlag == False):
		Merit_WriteCommand(MERIT_DIGITAL_OUTPUT_STATUS_READ_CMD, [], 0, Priority)		
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
		Merit_WriteCommand(MERIT_DIGITAL_INPUT_STATUS_READ_CMD, [], 0, Priority)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
		Merit_WriteCommand(MERIT_WAGON_WEIGHT_WRITE_CMD, [0,TEST_WAGON,RESOULUTION_LSB,RESOULUTION_MSB], WAGON_WEIGH_COMMAND_PAYLOAD_SIZE, Priority)
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)
	
#********************************************************************************************#
#Description : Function to parse the digital output status
#Arguments : DigitalOutputStatus DataList
#Return : None
#********************************************************************************************#
def Merit_DigitalOutputStatusParse(DigitalOutputStatusDataList):
	global m_TLCMqttClient
	global m_TLCStatusControlFlag
	OutputDict = {}
	JsonRespString = ""
	
	CurrentOutputStatus = (DigitalOutputStatusDataList[CURRENT_OUTPUT_STATUS_MSB] << 8) + DigitalOutputStatusDataList[CURRENT_OUTPUT_STATUS_LSB]
	ActualOutputStatus = int((DigitalOutputStatusDataList[ACTUAL_OUTPUT_STATUS_MSB] << 8) + DigitalOutputStatusDataList[ACTUAL_OUTPUT_STATUS_LSB])
	
	OutputStatus = ActualOutputStatus
	if (m_TLCStatusControlFlag == True):
		OutputStatus = CurrentOutputStatus
		
	OutputDict[OutputStatusDict[COMMAND4RES_SYSTEM_READY]] = int(OutputStatus) % 2
	OutputDict[OutputStatusDict[COMMAND4RES_OVERSPEED_LAMP_RELAY]] = (int(OutputStatus) >> COMMAND4RES_OVERSPEED_LAMP_RELAY) % 2
	OutputDict[OutputStatusDict[COMMAND4RES_ALARM_HOOTER]] = (int(OutputStatus) >> COMMAND4RES_ALARM_HOOTER) % 2	
	OutputDict[OutputStatusDict[PIN_4]] = (int(OutputStatus) >> PIN_4) % 2
	OutputDict[OutputStatusDict[PIN_5]] = (int(OutputStatus) >> PIN_5) % 2
	OutputDict[OutputStatusDict[PIN_6]] = (int(OutputStatus) >> PIN_6) % 2
	OutputDict[OutputStatusDict[PIN_7]] = (int(OutputStatus) >> PIN_7) % 2
	OutputDict[OutputStatusDict[PIN_8]] = (int(OutputStatus) >> PIN_8) % 2
	OutputDict[OutputStatusDict[COMMAND4RES_SYSTEM_READY_LAMP]] = (int(OutputStatus) >> COMMAND4RES_SYSTEM_READY_LAMP) % 2 
	OutputDict[OutputStatusDict[COMMAND4RES_OVERSPEED_LAMP]] = (int(OutputStatus) >> COMMAND4RES_OVERSPEED_LAMP) % 2
	OutputDict[OutputStatusDict[COMMAND4RES_ADVANCE_OVERSPEED_LAMP]] = (int(OutputStatus) >> COMMAND4RES_ADVANCE_OVERSPEED_LAMP) % 2
	OutputDict[OutputStatusDict[COMMAND4RES_UNKNOWN_VECHILE]] = (int(OutputStatus) >> COMMAND4RES_UNKNOWN_VECHILE) % 2 
	OutputDict[OutputStatusDict[COMMAND4RES_AD_FAILURE]] = (int(OutputStatus) >> COMMAND4RES_AD_FAILURE) % 2
	OutputDict[OutputStatusDict[PIN_14]] = (int(OutputStatus) >> PIN_14) % 2
	OutputDict[OutputStatusDict[PIN_15]] = (int(OutputStatus) >> PIN_15) % 2
	OutputDict[OutputStatusDict[PIN_16]] = (int(OutputStatus) >> PIN_16) % 2
	
	OutputDict["Message"] = ""
	JsonRespString = json.dumps(OutputDict)
	
	Merit_Publish(m_TLCMqttClient,m_MqttTLCOutputStatusPostTopic, JsonRespString)
	logging.info("CurrentOutputStatus : " + str(CurrentOutputStatus) + "ActualOutputStatus : " + str(int(ActualOutputStatus)))
	#print("CurrentOutputStatus : " + str(CurrentOutputStatus) + "ActualOutputStatus : " + str(int(ActualOutputStatus)))
	
#********************************************************************************************#
#Description : Function to parse the digital input status
#Arguments : DigitalInputStatus	DataList
#Return : None
#********************************************************************************************#
def Merit_DigitalInputStatusParse(DigitalInputStatusDataList):
	global m_TLCMqttClient
	InputDict = {}
	JsonRespString = ""
	
	CurrentInputStatus = (DigitalInputStatusDataList[CURRENT_INPUT_STATUS_MSB] << 8) + DigitalInputStatusDataList[CURRENT_INPUT_STATUS_LSB]
	ActualInputStatus = int((DigitalInputStatusDataList[ACTUAL_INPUT_STATUS_MSB] << 8) + DigitalInputStatusDataList[ACTUAL_INPUT_STATUS_LSB])
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_1A]] = int(ActualInputStatus) % 2 
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_1B]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_1B) % 2
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_2A]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_2A) % 2
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_2B]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_2B) % 2 
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_3A]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_3A) % 2 
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_3B]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_3B) % 2 
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_4A]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_4A) % 2
	InputDict[InputStatusDict[COMMAND10RES_TRACKSWITCH_4B]] = (int(ActualInputStatus) >> COMMAND10RES_TRACKSWITCH_4B) % 2 
	InputDict[InputStatusDict[COMMAND10RES_START_WEIGH]] = (int(ActualInputStatus) >> COMMAND10RES_START_WEIGH) % 2 
	InputDict[InputStatusDict[COMMAND10RES_END_WEIGH]] = (int(ActualInputStatus) >> COMMAND10RES_END_WEIGH) % 2
	InputDict[InputStatusDict[COMMAND10RES_AOS_IN_DIR_5A]] = (int(ActualInputStatus) >> COMMAND10RES_AOS_IN_DIR_5A) % 2
	InputDict[InputStatusDict[COMMAND10RES_AOS_IN_DIR_5B]] = (int(ActualInputStatus) >> COMMAND10RES_AOS_IN_DIR_5B) % 2
	InputDict[InputStatusDict[COMMAND10RES_AOS_OUT_DIR_6B]] = (int(ActualInputStatus) >> COMMAND10RES_AOS_OUT_DIR_6B) % 2 
	InputDict[InputStatusDict[COMMAND10RES_AOS_OUT_DIR_6A]] = (int(ActualInputStatus) >> COMMAND10RES_AOS_OUT_DIR_6A) % 2 
	InputDict[InputStatusDict[PIN_15]] = (int(ActualInputStatus) >> PIN_15) % 2 
	InputDict[InputStatusDict[PIN_16]] = (int(ActualInputStatus) >> PIN_16) % 2 
	InputDict["Message"] = ""
	JsonRespString = json.dumps(InputDict)
	Merit_Publish(m_TLCMqttClient,m_MqttTLCInputStatusPostTopic, JsonRespString)
	logging.info("CurrentInputStatus : "  + str( CurrentInputStatus) + "ActualInputStatus : " + str(ActualInputStatus))
	
#********************************************************************************************#
#Description : Function to parse the TLC Firmware version from the list
#Arguments : DataList
#Return : None
#********************************************************************************************#	
def Merit_VersionReqParse(DataList):
	global m_TLCFirmwareVersion
	stringlist = ""
	for x in DataList[1:]:
		stringlist = stringlist + chr(x)
	m_TLCFirmwareVersion = stringlist
	logging.info("TLC Version: " + str(stringlist) + ", Version Number : " + stringlist[12:])
	
#********************************************************************************************#
#Description : Function to parse the TLC Fimrware version release date from list
#Arguments : DataList
#Return : None
#********************************************************************************************#	
def Merit_VersionReleaseDataReqParse(DataList): 
	global m_TLCFirmwareReleaseDate  
	stringlist = ""
	for x in DataList[1:]:
		stringlist = stringlist + chr(x)
	m_TLCFirmwareReleaseDate = stringlist
	logging.info("Version Release Date : " + stringlist)

#********************************************************************************************#
#Description : Function to clear the queue
#Arguments : None
#Return : None
#********************************************************************************************#
def Merit_ClearQueue():
	global m_TLCSerialCommandWriteQueue
	with m_TLCSerialCommandWriteQueue.mutex:
		logging.info(str("******************** QUEUE CLEARED **********************\n"))
		m_TLCSerialCommandWriteQueue.queue.clear()
		time.sleep(MERIT_DEFAULT_QUERY_DELAY)

#********************************************************************************************#
#Description : Function to control the output status
#Arguments : OutputControlPinNumber, OnStatus
#Return : None
#********************************************************************************************#
def Merit_OutputStatusControl(OutputControlPinNumber, OnStatus):
	if((OutputControlPinNumber <= PIN_16 + 1) and (OutputControlPinNumber > 0)):
		Merit_ClearQueue()
		if(OnStatus == 'true'):
			print("PIN "+ str(OutputControlPinNumber) + " ON")
			Merit_WriteCommand(MERIT_OUTPUT_STATUS_WRITE_CMD, [OutputControlPinNumber, MERIT_STATUS_HIGH_PULSE], MERIT_STATUS_PAYLOAD_SIZE, WAGON_DATA_PRIORITY)  
			time.sleep(MERIT_DEFAULT_QUERY_DELAY)
			logging.info("PIN "+ str(OutputControlPinNumber) + " ON")
		elif(OnStatus == 'false'):
			print("PIN "+ str(OutputControlPinNumber) + " OFF")
			Merit_WriteCommand(MERIT_OUTPUT_STATUS_WRITE_CMD, [OutputControlPinNumber, MERIT_STATUS_LOW_PULSE], MERIT_STATUS_PAYLOAD_SIZE, WAGON_DATA_PRIORITY) 
			time.sleep(MERIT_DEFAULT_QUERY_DELAY)
			logging.info("PIN "+ str(OutputControlPinNumber) + " OFF")
		
#********************************************************************************************#
#Description : Function to reset the output status
#Arguments : None
#Return : None
#********************************************************************************************# 
def Merit_OutputStatusReset():
	Merit_ClearQueue()
	Merit_WriteCommand(MERIT_OUTPUT_STATUS_RESET_WRITE_CMD, [], 0, WAGON_DATA_PRIORITY)  
	time.sleep(MERIT_DEFAULT_QUERY_DELAY)

#********************************************************************************************#
#Description : Function to write the Serial Port Printout And ScoreBoard Availablity
#Arguments : None
#Return : None
#********************************************************************************************# 
def Merit_ScoreBoardAvailablity(payloadString):
	global m_HostWGID  
	Merit_ClearQueue()
	SBArr = bytes(payloadString, 'utf-8')
	HostIdArr = bytes(m_HostWGID, 'utf-8')
	arraylength = len(SBArr) + len(HostIdArr)
	print("SB ID", (SBArr))
	Merit_WriteCommand(MERIT_SCOREBOARD_AVAIL_WRITE_CMD, [SBArr, HostIdArr], arraylength, WAGON_DATA_PRIORITY)  
	time.sleep(4 * MERIT_DEFAULT_QUERY_DELAY)

#********************************************************************************************#
#Description : Function to reset the output status
#Arguments : None
#Return : None
#********************************************************************************************# 
def Merit_GetWBID():
	global m_HostWGID   
	global m_MqttWeighmentPostTopic 
	global m_MqttTLCInitTopic 
	global m_MqttTLCStatusTopic 
	global m_MqttTLCInputStatusPostTopic 
	global m_MqttTLCOutputStatusPostTopic 
	global m_MqttWagonRequestTopic  
	global m_MqttWeightStatusTopic 
	global m_MqttStatusControlTopic 
	global m_MqttMeritScoreBoardAvailablityTopic
	global m_ErrorStatusTopic
	global CLIENT_ID
	
	CurrentTime = str(datetime.datetime.now())
	
	CLIENT_ID = "MBMAGH01" + CurrentTime
	
	m_HostWGID = str(socket.gethostname())
	#print("HostName : "+ str(socket.gethostname()))
	m_HostWGID = "MBMAGH01"
	m_MqttWeighmentPostTopic = "/Merit/" + m_HostWGID + "/Weighment/"
	m_MqttTLCInitTopic = "/Merit/" + m_HostWGID + "/COMMAND/"
	m_MqttTLCStatusTopic = "/Merit/" + m_HostWGID + "/Status/"
	m_MqttTLCInputStatusPostTopic = "/Merit/" + m_HostWGID + "/InputStatus/"
	m_MqttTLCOutputStatusPostTopic = "/Merit/" + m_HostWGID + "/OutputStatus/"
	m_MqttWagonRequestTopic = "/Merit/" + m_HostWGID + "/Weighment/sendFrom/"
	m_MqttWeightStatusTopic = "/Merit/" + m_HostWGID + "/WeightStatus/"
	m_MqttStatusControlTopic = "/Merit/" + m_HostWGID + "/Status/Control/"
	m_MqttMeritScoreBoardAvailablityTopic = "/Merit/" + m_HostWGID + "/ScoreBoard/"
	m_ErrorStatusTopic = "/Merit/" + m_HostWGID + "/ErrorStatus/"
	
#***********************************************************************************#
#******************************* MQTT Functions *****************************************#
#***********************************************************************************#
#********************************************************************************************#
#Description : function to start the mqtt process
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_MqttStart():
	global m_TLCMqttClient
	try:
		m_TLCMqttClient = Merit_ConnectMqtt(CLIENT_ID, USERNAME, PASSWORD, BROKER, BROKER_PORT)
	except Exception as ex:
		logging.error("Exception at mqtt connecting function : " + str(ex))
		print("Exception at mqtt connecting function : " + str(ex))
		
#********************************************************************************************#
#Description : function to connect mqtt client
#Arguments : Mqtt Client id, Username, Password, Broker, BrokerPort
#Return : mqtt client
#********************************************************************************************#		
def Merit_ConnectMqtt(clientId, UserName, Password, Broker, BrokerPort):
	#client = mqtt_client.Client(clientId)
	#client.username_pw_set(UserName, Password)
	client = mqtt_client.Client(clientId, transport = 'websockets')
	try:
		client.on_connect = Merit_OnConnect
		client.on_disconnect = Merit_OnDisConnect
		client.connect(Broker, BrokerPort)
		client.loop_start()
	except Exception as ex:
		logging.error("Exception while connecting mqtt :  " + str(ex))
		print("Exception while connecting mqtt :  "+ str(ex))
	return client

#********************************************************************************************#
#Description : Callback function for mqtt connect
#Arguments : Mqtt Client, userdata, flags, rc
#Return : None
#********************************************************************************************#
def Merit_OnConnect(client, userdata, flags, rc):
	global MqttConnectFlag
	try:
		if rc == 0:
			MqttConnectFlag = True
			logging.info("Connected to MQTT Broker!")
			print("Connected to MQTT Broker!")
		else:
			logging.error("Failed to connect, return code %d\n" + str(rc))	
			print("Failed to connect, return code %d\n" + str(rc))
	except Exception as ex:
		logging.error("Exception at Mqtt OnConnectMessage : " + str(ex))
		print("Exception at Mqtt OnConnectMessage : "+ str(ex))
		
#********************************************************************************************#
#Description : Callback function for mqtt disconnect
#Arguments : Mqtt Client, userdata, rc
#Return : None
#********************************************************************************************#
def Merit_OnDisConnect(client, userdata, rc):
	global MqttConnectFlag
	try:
		if rc == 0:
			MqttConnectFlag = False
			logging.info("DisConnected from MQTT Broker!")
			client.reconnect()
		logging.info("DisConnecting Clbk")
		print("DisConnecting Clbk")
		client.reconnect()
	except Exception as ex:
		logging.error("Exception at Mqtt OnDisConnectMessage : " + str(ex))
		print("Exception at Mqtt OnDisConnectMessage : "+ str(ex))
	
#********************************************************************************************#
#Description : function to publich the mqtt topic
#Arguments : MqttClient, MqttTopic, MqttMessage
#Return : None
#********************************************************************************************#
def Merit_Publish(client, topic, message):
	global m_SerialCommErrorFlag
	status = 0
	if(m_SerialCommErrorFlag == False):
		try:
			result = client.publish(topic, message)		
			status = result[0]
			if status == 0:
				logging.info(str(f"Send `{message}` to topic `{topic}`"))
			else:
				logging.error(str(f"Error!!!!!! : Failed to send `{message}` to topic {topic}, Status : `{status}` "))
		except Exception as ex:
			logging.error("Exception at Mqtt Publish : " + str(ex))
			print("Exception at Mqtt Publish : "+ str(ex))
	return status

#********************************************************************************************#
#Description : function to subscribe the mqtt topic
#Arguments : MqttClient, MqttTopic
#Return : None
#********************************************************************************************#	
def Merit_Subscribe(client: mqtt_client, topic):
	try:
		client.subscribe(topic)
		client.on_message = Merit_OnMessage
		logging.info(str(f"Topic {topic} is Subscribed"))	
		print(str(f"Topic {topic} is Subscribed"))
	except Exception as ex:
		logging.error("Exception at Mqtt Subscribe : " + str(ex))
		print("Exception at Mqtt Subscribe : "+ str(ex))

#********************************************************************************************#
#Description : Callback function for mqtt message from subscribed topic
#Arguments : Mqtt Client, userdata, message
#Return : None
#********************************************************************************************#
def Merit_OnMessage(client, userdata, msg):
	global m_MqttPostCurrentWagonNumber
	global m_TLCStatusFlag
	global m_LocoCount
	global m_AXLETOELIMINATE
	global m_MeritPort
	global m_SerialCommFailureCount
	global m_MqttReset
	global m_SB
	global m_NoPostFlag
	global m_TLCStatusControlFlag
	
	try:
		m_SerialCommFailureCount = 0
		Topic = msg.topic
		payload = msg.payload.decode()
		logging.info(str(f"Received Data from `{msg.topic}` topic!"))
		#Weighment Initiate Topic
		if(Topic == m_MqttTLCInitTopic):
			payloadList = payload.split(",")
			if(payloadList[0] == m_MqttInitiate):
				if(len(payloadList) >= MERIT_STATUS_PAYLOAD_SIZE):
					logging.info("AXLE TO BE ELIMINATED " + str(int(payloadList[1])))
					m_AXLETOELIMINATE = int(payloadList[1])
				else:
					m_AXLETOELIMINATE = 0
				Merit_Init()
				logging.info("InitiateReceived")
				m_NoPostFlag = False
				m_TLCStatusControlFlag = False
			elif(payload == m_MqttTerminate):
				Merit_ClearQueue()
				Merit_Terminate()
				logging.info("Terminate Received")
				m_NoPostFlag = True
		
		#Wagon Weighment for specific wagon Topic
		elif(Topic == m_MqttWagonRequestTopic):
			#m_NoPostFlag = False
			#print("Merit Req Wagon Serial Number" * 100)
			logging.info("Merit Req Wagon Serial Number" + str(payload))
			m_MqttPostCurrentWagonNumber = int(payload) 
		#Status Topic			
		elif(Topic == m_MqttTLCStatusTopic):
			if(payload == m_MqttInitiate):
				m_NoPostFlag = False
				logging.info("Status Initiate Topic Received")
				print("Status Initiate Topic Received")
				m_TLCStatusControlFlag = False
				m_TLCStatusFlag = True
			if(payload == m_MqttTerminate):
				logging.info("Status Terminate Topic Received")
				print("Status Terminate Topic Received")
				m_TLCStatusFlag = False
				m_NoPostFlag = True
				Merit_ClearQueue()
				m_TLCStatusFlag = False
				m_TLCStatusControlFlag = False
		#Status Control Topic		
		elif(Topic == m_MqttStatusControlTopic):   
			payloadList = payload.split(",")
			if(payloadList[0] == m_MqttReset):
				Merit_OutputStatusReset()
				m_TLCStatusFlag = True
				m_NoPostFlag = False
				m_TLCStatusControlFlag = False
			elif(payloadList[0] == m_SB):
				if(len(payloadList) >= MERIT_STATUS_PAYLOAD_SIZE):
					Merit_ScoreBoardAvailablity(payloadList[1]) 
			else:
				if(len(payloadList) >= MERIT_STATUS_PAYLOAD_SIZE):
					m_TLCStatusControlFlag = True
					m_NoPostFlag = False
					Merit_OutputStatusControl(int(payloadList[0]), payloadList[1])
			
	except Exception as ex:
		logging.error("Exception at Mqtt OnMessage : " + str(ex))
		print("Exception at Mqtt OnMessage : "+ str(ex))
		
#********************************************************************************************#
#Description : function to subscribe mqtt topics
#Arguments : None
#Return : None
#********************************************************************************************#		
def Merit_MqttSubscribeTopics():
	global m_TLCMqttClient
	try:
		Merit_Subscribe(m_TLCMqttClient, m_MqttTLCInitTopic)
		Merit_Subscribe(m_TLCMqttClient, m_MqttTLCStatusTopic)
		Merit_Subscribe(m_TLCMqttClient, m_MqttWagonRequestTopic)
		Merit_Subscribe(m_TLCMqttClient, m_MqttStatusControlTopic)
	except Exception as ex:
		logging.error("Exception at subscribing topics : " + str(ex))
		print("Exception at subscribing topics :  "+ str(ex))

#********************************************************************************************#
#Description : function to post the version number and release Date
#Arguments : None
#Return : success or fail(True/False)
#********************************************************************************************#		
def Merit_VersionPost():
	global m_TLCFirmwareReleaseDate
	global m_TLCFirmwareVersion
	global m_TLCPyCodeVersion
	global m_TLCPyCodeReleaseDate
	global m_VersionPostURL
	global m_HostWGID
	status = False
	
	VersionObj1 = {'TLC_FirmwareVersion' : m_TLCFirmwareVersion, 'TLC_FirmwareReleaseDate' : m_TLCFirmwareReleaseDate, 'TLC_PyCodeVersion' : m_TLCPyCodeVersion, 'TLC_PyCodeReleaseDate' : m_TLCPyCodeReleaseDate , 'wgid' : m_HostWGID}
	
	VersionObj = {'TLC_FirmwareVersion ' : m_TLCFirmwareVersion, 'TLC_FirmwareReleaseDate' : m_TLCFirmwareReleaseDate, 'TLC_PyCodeVersion ' : m_TLCPyCodeVersion, 'TLC_PyCodeReleaseDate' : m_TLCPyCodeReleaseDate, 'wgid' : m_HostWGID}
	try:
		res = requests.post(m_VersionPostURL, json = VersionObj)
		print("Post Req Response code : " + str(res.status_code))
		if(res.status_code == m_PostSuccessCode):
			status = True
	except Exception as ex:
		logging.error("Exception at http version post : " + str(ex))
		print("Exception at http version post : "+ str(ex))			   
	return status
		
#********************************************************************************************#
#Description : Function to publish Merit wagon weighment details to mqtt server
#Arguments : None
#Return : None
#********************************************************************************************#	
def Merit_MqttPublishWagonDetails():
	global m_TLCMqttClient
	global m_WagonCount 
	global m_MqttPostCurrentWagonNumber
	global m_MeritWagonDetailsDict
	global m_LocoCount
	
	while(1):
		LengthOfDict = len(m_MeritWagonDetailsDict)
		if(LengthOfDict > 0):
			while(((m_WagonCount - m_LocoCount) != 0) and (m_MqttPostCurrentWagonNumber <= (m_WagonCount - m_LocoCount))):
				if m_MqttPostCurrentWagonNumber in m_MeritWagonDetailsDict:
					if(Merit_Publish(m_TLCMqttClient, m_MqttWeighmentPostTopic, m_MeritWagonDetailsDict[int(m_MqttPostCurrentWagonNumber)]) == 0):
						m_MqttPostCurrentWagonNumber = m_MqttPostCurrentWagonNumber + 1
					time.sleep(0.05)
				time.sleep(0.01)
		time.sleep(0.001)	
	
#********************************************************************************************#  
#Description : Entry point of this program
#Notes : To make sure that don't allow this script to import as module in another file (if imported then __name__ will be file name)
#********************************************************************************************#
if __name__=="__main__": #To run as a standalone script

	Merit_GetWBID()
	MqttThread = Thread(target = Merit_MqttStart, daemon = True)
	MqttThread.start()
	while(MqttConnectFlag == False):		#Check the mqtt is connected to the broker
		time.sleep(1)
	Merit_MqttSubscribeTopics()				#Subscribe the mqtt topics
	while(True):
		m_MeritPort = Merit_FindTLCPort()   #Monitor TLC ComPort	
		if  m_MeritPort != "":
			m_NoPostFlag = True
			TLCThread = threading.Thread(target = Merit_SerialWriterQueue, args=(), daemon = True)
			TLCThread.start()
			while(True):
				if((m_TLCFirmwareReleaseDate == "") and (m_TLCFirmwareVersion == "")):
					Merit_SerialWriterVersionRequesAndDate()	#Get TLC firmware version and release date
				else:
					m_TLCSerialCommandWriteQueue.queue.clear()
					if(Merit_VersionPost() == True):	#Post TLC Firmware and Python Code Version
						MqttPublishThread = threading.Thread(target = Merit_MqttPublishWagonDetails, args=(), daemon = True)
						MqttPublishThread.start()
						while(True):
							if(m_SerialCommErrorFlag == False):
								Merit_TLCMonitor()  #Monitoring the TLC Functions based on Mqtt Commands
							else:
								m_TLCSerialCommandWriteQueue.queue.clear()
								m_MeritPort = Merit_FindTLCPort()
								if  m_MeritPort != "":
									m_MqttPostCurrentWagonNumber = 0
									m_SerialCommErrorFlag = False
								time.sleep(3)   
							
							time.sleep(0.001)
				time.sleep(1)
		else:
			logging.error(str("Cannot find TLC port"))
		time.sleep(3)						#3 Sec timeout for logging purpose
			