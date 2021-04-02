from device import Device

import requests
import sys
import os
import json
import time
import threading
import argparse
import random

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

script_path = os.path.dirname(os.path.realpath(__file__))
config_name = "config.json"
full_config = os.path.join(script_path, config_name)
args = {}
good_responses = [
	"Everything looks good",
	"Everyone is responding",
	"No problems found",
	"Looks good"
]

def SaveDefaultConfig():

	with open(full_config, 'w') as config:
		data = {
			"devices": [
				{
					"name": "example_device",
					"cmd": "GET",
					"cmd_args": "192.168.4.10",
					"regex": r"success",
				}
			]
		}
		config.write(json.dumps(data, indent=4))

def LoadConfig():
	if not args.siri:
		print("Loading config...")
	if not os.path.exists(full_config):
		print("Config not found. Creating now...")
		SaveDefaultConfig()
		return "retry"

	try:
		with open(full_config, 'r') as config:
			data = config.read()
			return json.loads(data)
	except Exception as e:
		print("Error reading file:", str(e))
		return None

def TestDevices(devices):
	threads = []
	for device in devices:
		if not args.siri:
			print("Testing " + device.name + " with " + device.cmd.upper() + "... ")
		#device.Test()
		thread = threading.Thread(target=device.Test)
		thread.start()
		threads.append(thread)

	for thread in threads:
		thread.join()

def main():
	global args
	parser = argparse.ArgumentParser("Check availability of devices on the network")
	parser.add_argument('--siri', action="store_true")
	args = parser.parse_args()

	data = LoadConfig()
	if not args.siri:
		print(data)

	if not data:
		return
	if data == "retry":
		main()

	devices = []
	for d in data.get('devices', []):
		device = Device(d)
		devices.extend(device.GetAllDevices())

	if not args.siri:
		print()

	TestDevices(devices)

	if not args.siri:
		print()

	if not args.siri:
		for device in devices:
			if not device.parent:
				device.PrintResults()
				print()

	if args.siri:
		offline = []
		for device in devices:
			offline += device.GetAllOffline()

		offline = list(set(offline))
		output = "Okay. "
		if offline:
			output += ', '.join(offline)
			if len(offline) > 1:
				index = output.rfind(',')
				output = output[:index+1] + " and" + output[index+1:]
				output += " are not responding"
			else:
				output += " is not responding"
		else:
			output += random.choice(good_responses)

		print(output)

if __name__=="__main__":
	main()
