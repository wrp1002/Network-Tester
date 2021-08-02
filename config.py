import os
import json
from datetime import datetime

script_path = os.path.dirname(os.path.realpath(__file__))
config_name = "config.json"
full_config = os.path.join(script_path, config_name)


def ProcessMacros(data):
	macros = data.get('macros', {})
	print("Processing macros:")
	for search, replace in macros.items():
		print(f"'{search}' --> '{replace}'")
	print()

	devices = json.dumps(data.get('devices', []))
	for search, replace in macros.items():
		devices = devices.replace(search, replace)
	data['devices'] = json.loads(devices)
	return data

def SaveDefaultConfig():
	with open(full_config, 'w') as config:
		data = {
			"devices": [
				{
					"name": "Internet",
					"commands": [
						{
							"cmd": "ping -W 3 -c 1 8.8.8.8",
							"regex": ".*time(=|<).*"
						}
					],
					"enabled": True
				}
			]
		}
		config.write(json.dumps(data, indent=4))

def LoadConfig():
	print("Loading config...")
	if not os.path.exists(full_config):
		print("Config not found. Creating now...")
		SaveDefaultConfig()
		return "retry"

	try:
		with open(full_config, 'r') as config:
			data = config.read()
			data = json.loads(data)
			data = ProcessMacros(data)
			return data
	except Exception as e:
		print("Error reading file:", str(e))
		return None


def SaveConfig(data):
	with open(full_config, 'w') as config:
		config.write(json.dumps(data, indent=4))


def LoadJSONFile(file_name):
	if not file_name:
		return {}

	print("Loading previous output...")
	if not os.path.exists(file_name):
		print("File not found")
		return {}

	try:
		with open(file_name, 'r') as file:
			data = file.read()
			data = json.loads(data)
			return data
	except Exception as e:
		print("Error reading file:", str(e))
		return {}


def WriteOutput(output_file, devices):
	results = {}
	for device in devices:
		if not device.enabled:
			continue

		results[device.name] = {
			"success": device.was_successful,
			"total_commands": device.cmd_len,
			"successful_commands": device.successful_count,
			"status": device.status,
		}

	with open(os.path.join(script_path, output_file), 'w+') as file:
		file.write(json.dumps(results, indent=4))

def WriteSiriOutput(siri_output_file, devices, show_time):
	partially_failed = []
	fully_failed = []
	for device in devices:
		if not device.enabled:
			continue

		if not device.was_successful:
			if device.fully_failed:
				fully_failed.append(device.name)
			else:
				partially_failed.append(device.name)


	output = "Okay. "
	if show_time:
		time = datetime.now()
		output += f"From {time.strftime('%-I:%M %p')}. "

	if partially_failed or fully_failed:
		output += ', '.join(partially_failed)
		index = output.rfind(',')
		if index != -1:
			output = output[:index+1] + " and" + output[index+1:]
		output += " partially failed.. "

		output += ', '.join(fully_failed)
		if len(fully_failed) > 1:
			index = output.rfind(',')
			output = output[:index+1] + " and" + output[index+1:]
			output += " are not responding"
		else:
			output += " is not responding"
	else:
		output += random.choice(good_responses)

	with open(os.path.join(script_path, siri_output_file), 'w+') as file:
		file.write(output)
