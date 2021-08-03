import subprocess
import requests
import re
import time
import threading

verbose = False

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
		res = str(requests.get(args, verify=False, timeout=3).status_code)
		return res
	except Exception:
		return ""

class Command:
	def __init__(self, cmd_dict):
		self.full_cmd = cmd_dict.get('cmd', '')
		self.name = cmd_dict.get('name', self.full_cmd.split(' ')[0].capitalize())
		self.regex = cmd_dict.get('regex', '')
		self.func = NoCmd
		self.tries = 1
		self.was_successful = False

		try:
			self.cmd = self.full_cmd.split(' ')[0]
			self.args = " ".join(self.full_cmd.split(' ')[1:])
		except Exception as e:
			print(f"{self.name} error: {e}")
			return

		if self.cmd.startswith('ping'):
			self.func = PingCmd
		elif self.cmd.startswith('ssh'):
			self.func = SSHCmd
		elif self.cmd.startswith('get'):
			self.func = GetCmd

	def CheckOutput(self, output):
		match = re.match(self.regex, output, re.DOTALL)
		return match is not None

	def Run(self):
		self.was_successful = False
		for i in range(self.tries):
			output = self.func(self.args)
			if self.CheckOutput(output):
				self.was_successful = True
				break
			time.sleep(1 + i)


class Device:
	def __init__(self, device_dict, prev_results={}):
		self.name = device_dict.get('name')
		self.nickname = device_dict.get('short_name', self.name[:5])
		self.enabled = device_dict.get('enabled', False)
		self.execution_time = -1
		self.commands = [
			Command(cmd_dict)
			for cmd_dict in device_dict.get('commands', [])
		]
		self.onChange = device_dict.get('onChange', [])
		self.prev_results = prev_results

		#print("New device! name:", self.name, "commands:", len(self.commands))

	@property
	def cmd_len(self):
		return len(self.commands)

	@property
	def successful_count(self):
		return sum([cmd.was_successful for cmd in self.commands])

	@property
	def was_successful(self):
		return self.cmd_len == self.successful_count

	@property
	def fully_failed(self):
		return self.successful_count == 0

	@property
	def inky_display_name(self):
		if self.was_successful:
			return self.nickname
		else:
			return f"{self.nickname} {self.successful_count}/{self.cmd_len}"

	@property
	def status(self):
		if self.was_successful:
			return "success"
		if self.fully_failed:
			return "fail"
		else:
			return "partial fail"

	@property
	def prev_status(self):
		return self.prev_results.get('status')

	@property
	def status_changed(self):
		prev_status = self.prev_status
		if prev_status is None:
			return False

		return self.status != prev_status

	def Test(self, use_threads=True):
		start_time = time.time()
		if use_threads:
			threads = []
			for cmd in self.commands:
				thread = threading.Thread(target=cmd.Run)
				thread.start()
				threads.append(thread)

			for thread in threads:
				thread.join()

		else:
			for cmd in self.commands:
				cmd.Run()
		self.execution_time = time.time() - start_time

	def CheckForChange(self):
		if self.status_changed:
			for cmd in self.onChange:
				cmd_dict = {
					"cmd": cmd.replace("<DEVICE_NAME>", self.name).replace("<PREV_STATUS>", self.prev_status).replace("<STATUS>", self.status),
					"regex": "",
				}
				cmd = Command(cmd_dict)
				cmd.Run()

	def PrintResults(self, full_output):
		print(f"{self.name}{(' ('+self.nickname+')') if full_output else ''}: {self.successful_count}/{self.cmd_len}")
		if full_output:
			for cmd in self.commands:
				print(f"\t{cmd.name}: {'Success' if cmd.was_successful else 'Fail'}")
			print(f"\tExecution time: {round(self.execution_time, 2)} seconds")
		print()
