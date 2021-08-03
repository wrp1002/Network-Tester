import requests
import os
import time
import threading
import argparse
from device import Device
import config

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

script_path = os.path.dirname(os.path.realpath(__file__))
args = {}


def TestDevices(devices):
	use_threads = args.multithreaded
	full_output = args.full_output
	show_failed_only = args.show_failed

	threads = []
	for device in devices:
		if not device.enabled:
			#print("Skipping", device.name)
			continue

		print(f"Testing {device.name}... ")

		if use_threads:
			thread = threading.Thread(target=device.Test)
			thread.start()
			threads.append(thread)
		else:
			device.Test(False)
			device.PrintResults(full_output)
			print()

	if use_threads:
		for thread in threads:
			thread.join()

		print()
		for device in devices:
			if not device.enabled:
				continue
			if show_failed_only and device.was_successful:
				continue

			device.PrintResults(full_output)

def CheckDevicesForChange(devices):
	for device in devices:
		device.CheckForChange()

def SetAllDevicesEnabled(data, enabled):
	for i in range(len(data['devices'])):
			data['devices'][i]["enabled"] = enabled
	config.SaveConfig(data)
	print(f"{'Enabled' if enabled else 'Disabled'} all devices")


def main():
	global args
	parser = argparse.ArgumentParser("Check availability of devices on the network")
	parser.add_argument('--output',									help="file to output JSON results to")
	parser.add_argument('--prev',									help="file to read previous JSON output from")
	parser.add_argument('--siri',									help="file to output Siri response to")
	parser.add_argument('--time', 			action="store_true",	help="include current time in Siri output")
	parser.add_argument('--multithreaded',	action="store_true", 	help="use threads for tests (Recommended)")
	parser.add_argument('--inky', 			action="store_true", 	help="output results to INKY PHAT")
	parser.add_argument('--disable_all',	action="store_true",	help="disable all devices in the config file")
	parser.add_argument('--enable_all',  	action="store_true",	help="enable all devices in the config file")
	parser.add_argument('--full_output', 	action="store_true",	help="show more output for results when running the test")
	parser.add_argument('--show_failed', 	action="store_true",	help="only print results for failed devices")
	parser.add_argument('--verbose',	 	action="store_true",	help="print more stuff")
	args = parser.parse_args()

	output_file = args.output
	prev_file = args.prev
	siri_output_file = args.siri
	inky = args.inky


	data = config.LoadConfig()

	if args.disable_all:
		SetAllDevicesEnabled(data, False)
		return
	if args.enable_all:
		SetAllDevicesEnabled(data, True)
		return

	prev_output = config.LoadJSONFile(prev_file)

	if not data:
		return
	if data == "retry":
		main()

	devices = []

	for d in data.get('devices', []):
		device_name = d.get('name', '')
		prev_results = prev_output.get(device_name, {})
		devices.append(Device(d, prev_results))


	print("Testing devices...")
	print()
	TestDevices(devices)

	if prev_file:
		CheckDevicesForChange(devices)

	if output_file:
		config.WriteOutput(output_file, devices)
	if siri_output_file:
		config.WriteSiriOutput(siri_output_file, devices, args.time)

	if inky:
		from inky.auto import auto
		from PIL import Image, ImageFont, ImageDraw
		from font_fredoka_one import FredokaOne

		inky_display = auto(verbose=True)
		inky_display.set_border(inky_display.BLACK)

		flip = False
		if flip:
			inky_display.h_flip = True
			inky_display.v_flip = True

		img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
		draw = ImageDraw.Draw(img)
		font = ImageFont.truetype(FredokaOne, 14)

		h = font.getsize("H")[1]
		x, y = (0, 0)
		max_w = max([font.getsize(device.inky_display_name)[0] for device in devices]) + 1

		if args.time:
			draw.text((x, y), f"{time.strftime('%-I:%M')}", inky_display.BLACK, font)
			y += h

		for device in devices:
			if not device.enabled:
				continue

			#x = (inky_display.WIDTH / 2) - (w / 2)
			#y = (inky_display.HEIGHT / 2) - (h / 2)
			if device.was_successful:
				draw.text((x, y), device.inky_display_name, inky_display.BLACK, font)
			else:
				draw.text((x, y), device.inky_display_name, inky_display.RED, font)

			y += h
			if y + h > inky_display.HEIGHT:
				y = 0
				x += max_w


		inky_display.set_image(img)
		inky_display.show()



if __name__=="__main__":
	main()











