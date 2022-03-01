import json
import os
import json

from sys import argv

# ===================== CONSTANTS ===================== #

ERROR = -1
SUCCESS = 0

CONFIG_FILE_NAME = "anvil.json"
CONFIG_FIELDS = {
	"ART": str,
	"EXE": str,
	"CC": str,
	"CCFLAGS": list,
	"LDFLAGS": list,
	"LDLIBS": list,
	"DIR": list
}

# ===================== LOGS ===================== #

RED     = "\033[0;31m"
GREEN   = "\033[0;32m"
YELLOW  = "\033[0;33m"
BLUE    = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN    = "\033[0;36m"
RESET   = "\033[0m"

def log_error(message):
	print(f"{RED}X{RESET} {message}")

def log_warning(message):
	print(f"{YELLOW}!{RESET} {message}")

def log_success(message):
	print(f"{GREEN}~{RESET} {message}")

def log_debug(message):
	print(f"{CYAN}#{RESET} {message}")

def log_info(message):
	print(f"{BLUE}>{RESET} {message}")

def log_note(message):
	print(f"{MAGENTA}@{RESET} {message}")

# ===================== CONFIG ===================== #

def load_config(path):
	if not os.path.exists(path):
		log_error(f"Cannot find configuration file '{path}'")
		return ERROR
	file = open(path, "r")
	config = json.load(file)
	file.close()
	log_success(f"Loaded build configuration from '{path}'")
	return config

def verify_config(config):
	for field in CONFIG_FIELDS.keys():
		if field not in config.keys():
			log_error(f"Configuration field '{field}' does not exist")
			return ERROR

	for field in config.keys():
		if field not in CONFIG_FIELDS.keys():
			log_warning(f"Ignoring unknown configuration field '{field}'")
		elif type(config[field]) != CONFIG_FIELDS[field]:
			log_error(f"Incorrect type '{type(config[field])}' for configuration field '{field}' ({CONFIG_FIELDS[field]})")
			return ERROR

	return SUCCESS

# ===================== MAIN ===================== #

def main():
	config = load_config(CONFIG_FILE_NAME)
	if config == ERROR:
		return ERROR
	print(config)

	if verify_config(config) == ERROR:
		return ERROR

	return SUCCESS

exit(main())
