# Network-Tester

This script can be used to automatically test devices throughout your network and report which ones are unresponsive. It is useful to test smart home devices with. The script can output results to a JSON file, output Siri-friendly phrases, execute commands when the status of a device changes, and display results on an Inky pHat.

## Getting Started

This script requires python3 to be installed. Run `./tester.py -h` to see available arguments for the script.

## Crontab

A method of running the script automatically is to use crontab. Make a new cron job by running `crontab -e`

An example usage is `*/5 * * * * cd /home/pi/Documents/net-test && ./run.sh` to run the script every 5 minutes.

## Config

An example config:
```
{
    "macros": {
        "PING_ARGS": "-W 3 -c 1",
        "PING_SUCCESS": ".*time(=|<).*",
        "GET_SUCCESS": ".*200.*"
    },
    "devices": [
        {
            "name": "Internet Connection",
            "short_name": "WiFi",
            "enabled": true,
            "commands": [
                {
                    "cmd": "ping PING_ARGS 8.8.8.8",
                    "regex": "PING_SUCCESS"
                }
            ]
        },
        {
            "name": "Raspberry Pi 4",
            "short_name": "Pi4",
            "enabled": true,
            "commands": [
                {
                    "cmd": "ping PING_ARGS 10.0.0.12",
                    "regex": "PING_SUCCESS"
                },
                {
                    "name": "Raspberry Pi 4 mDNS",
                    "cmd": "ping PING_ARGS nextcloud.local",
                    "regex": "PING_SUCCESS"
                },
                {
                    "name": "Nextcloud Web",
                    "cmd": "get https://10.0.0.12",
                    "regex": "GET_SUCCESS"
                },
                {
                    "name": "Homebridge@1 Service",
                    "cmd": "ssh user@10.0.0.12 systemctl is-active homebridge@1",
                    "regex": ".*active.*"
                }
            ],
            "onChange": [
                "ssh root@192.168.4.96 springcuts -r Notif -p \"'<DEVICE_NAME>' status has changed from <PREV_STATUS> to <STATUS>\""
            ]
        }
    ]
}
```


### "macros"

Macros can be used to automatically fill in values throughout the config; they are useful for repetitive values in the config that you might want to change later. 

### "devices"

Each device is an object in the devices array. The name of the device should be unique. "short_name" is used only on the inky phat and is optional to include. "enabled" tells whether the device should be tested when the script is run. 

### "commands"

This is a list of commands that should be run to test a device. Possible commands for "cmd" are ping, get, and ssh. "regex" is a regular expression that is used to check the output of the command. An optional name can also be given to a command that will only be used in the script output. 

### "onChange"
This is a set of additional commands that are run when the device's status has changed since the last time the script was run. This can only be triggered if the previous ouput file is passed to the script by running `./tester.py --prev out.json` for example. These commands are handled a bit differently and have special macros: <DEVICE_NAME>, <PREV_STATUS>, and <STATUS> for now.


