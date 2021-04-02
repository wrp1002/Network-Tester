import subprocess
import requests
import re
import time

def NoCmd(args):
	print("Uhhh no cmd?")
	return ""

def PingCmd(args):
	try:
		output = subprocess.check_output(['ping'] + args.split()).decode('utf-8')#.replace('\r', '').replace('\n', '')
		return output
	except Exception:
		return ""

def SSHCmd(args):
	try:
		output = subprocess.check_output(['ssh'] + args.split()).decode('utf-8')#.replace('\r', '').replace('\n', '')
		return output
	except Exception:
		return ""

def GetCmd(args):
	try:
		res = str(requests.get(args, verify=False).status_code)
		return res
	except Exception:
		return ""

class Device:
	def __init__(self, device_dict):
		self.name = device_dict.get('name')
		self.full_cmd = device_dict.get('cmd')
		self.cmd = self.full_cmd.split(' ')[0]
		self.args = " ".join(self.full_cmd.split(' ')[1:])
		self.regex = device_dict.get('regex')
		self.func = NoCmd
		self.tries = 3
		self.last_test_success = False
		self.parent = None
		#print("New device! name:", self.name)

		if self.cmd.startswith('ping'):
			self.func = PingCmd
		elif self.cmd.startswith('ssh'):
			self.func = SSHCmd
		elif self.cmd.startswith('get'):
			self.func = GetCmd

		self.children = []
		for child_dict in device_dict.get('children', []):
			child = Device(child_dict)
			child.parent = self
			self.children += child.GetAllDevices()

	def GetAllDevices(self):
		return self.children + [self]

	def WasSuccessful(self, output):
		match = re.match(self.regex, output, re.DOTALL)
		return match is not None

	def Test(self):
		for i in range(self.tries):
			output = self.func(self.args)
			if self.WasSuccessful(output):
				self.last_test_success = True
				return True
			time.sleep(1 + i)

		self.last_test_success = False

		return False

	def PrintResults(self, indent=0):
		print(" "*indent + self.name + " " + self.cmd.upper() + ": " + ("Success" if self.last_test_success else "Fail"))
		for child in self.children:
			child.PrintResults(indent + 4)

	def HasChildren(self):
		return (len(self.children) > 0)

	def GetAllOffline(self):
		offline = []
		if not self.last_test_success:
			offline.append(self.name)

		for child in self.children:
			offline += child.GetAllOffline()

		return offline