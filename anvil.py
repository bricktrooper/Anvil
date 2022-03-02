import os
import json

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
	"SRC": list
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
		log_error(f"Cannot find config file '{path}'")
		return ERROR
	file = open(path, "r")
	config = json.load(file)
	file.close()
	log_success(f"Loaded build config from '{path}'")
	return config

def verify_config(config):
	for field in CONFIG_FIELDS.keys():
		if field not in config.keys():
			log_error(f"'{field}' not found in build configuration")
			return ERROR

	for field in config.keys():
		if field not in CONFIG_FIELDS.keys():
			log_warning(f"Ignoring unknown field '{field}' in build configuration")
			continue

		actual_type = type(config[field])
		expected_type = CONFIG_FIELDS[field]

		if actual_type != expected_type:
			log_error(f"Incorrect type '{actual_type}' for '{field}' ({expected_type})")
			return ERROR

		if actual_type == list:
			for item in config[field]:
				if type(item) != str:
					log_error(f"'{field}' must only contain strings")
					return ERROR

	return SUCCESS

# ===================== DEPENDENCIES ===================== #

def discover_source_files(path):
	sources = []
	if not os.path.isdir(path):
		log_error(f"Source path '{path}' is not a directory'")
		return ERROR

	log_debug(f"Searching '{path}/'")
	for file in os.listdir(path):
		file = f"{path}/{file}"

		if os.path.isdir(file):
			sources += discover_source_files(file)
		elif file.endswith(".c"):
			sources.append(file)
			log_debug(f"Discovered '{file}'")
	return sources

# ===================== MAIN ===================== #

def main():
	config = load_config(CONFIG_FILE_NAME)
	if config == ERROR or verify_config(config) == ERROR:
		return ERROR

	sources = []
	for path in config['SRC']:
		sources += discover_source_files(path)

	print(sources)

	return SUCCESS

exit(main())
