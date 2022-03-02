import os
import json
import subprocess

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

	if config['ART'] == "":
		log_error(f"'ART' was not specified")
		return ERROR
	if config['EXE'] == "":
		log_error(f"'EXE' was not specified")
		return ERROR
	if config['CC'] == "":
		log_error(f"'CC' was not specified")
		return ERROR
	if len(config['SRC']) == 0:
		log_error(f"'SRC' was not specified")
		return ERROR

	return SUCCESS

# ===================== DEPENDENCIES ===================== #

def discover_source_files(path):
	if not os.path.isdir(path):
		log_error(f"Source path '{path}' is not a directory'")
		return ERROR

	log_debug(f"Searching '{path}/' for source files")
	sources = []
	for file in os.listdir(path):
		file = f"{path}/{file}"
		if os.path.isdir(file):
			files = discover_source_files(file)
			if files == ERROR:
				return ERROR
			sources += files
		elif file.endswith(".c"):
			sources.append(file)
			log_success(f"Discovered source file '{file}'")

	return sources

#def discover_header_includes(source):
#	if not os.path.isfile(source):
#		log_error(f"Source '{source}' is not a file'")
#		return ERROR
#	file = open(source, "r")
#	code = file.read()
#	file.close()
#	lines = code.splitlines()

#	headers = []
#	for line in lines:
#		if "#include" in line:
#			header = line.split()[1]
#			# ignore system headers
#			if header.startswith("\"") and header.endswith("\""):
#				header = header.split("\"")[1]
#				headers.append(header)

#	return headers

#def locate_header(target, headers):
#	for header in headers:
#		if header.endswith(target):
#			log_success(f"Located header '{target}' at '{header}'")
#			return header
#	log_error(f"Failed to locate header '{header}'")
#	return ERROR

def discover_directories(path):
	directories = []
	if not os.path.isdir(path):
		log_error(f"Source path '{path}' is not a directory'")
		return ERROR

	log_success(f"Discovered directory '{path}/'")
	directories.append(path)

	log_debug(f"Searching '{path}/' for directories")
	for file in os.listdir(path):
		file = f"{path}/{file}"
		if os.path.isdir(file):
			paths = discover_directories(file)
			if paths == ERROR:
				return ERROR
			directories += paths

	return directories

def generate_dependencies(config, source, includes):
	CC = config['CC']
	CCFLAGS = " ".join(config['CCFLAGS'])
	INC = " ".join(includes)
	command = f"{CC} {CCFLAGS} {INC} -MM {source}"

	try:
		output = subprocess.check_output(command, shell = True, text = True)
	except subprocess.CalledProcessError as exception:
		log_error(f"Failed to generate dependencies for '{source}'")
		return ERROR

	return output

def out_of_date(object, dependencies):

	for dependency in dependencies:
		print(dependency)
		print(os.stat(dependency))

# ===================== MAIN ===================== #

def main():
	config = load_config(CONFIG_FILE_NAME)
	if config == ERROR or verify_config(config) == ERROR:
		return ERROR

	sources = []
	for path in config['SRC']:
		files = discover_source_files(path)
		if files == ERROR:
			return ERROR
		sources += files

	directories = []
	for path in config['SRC']:
		paths = discover_directories(path)
		if paths == ERROR:
			return ERROR
		directories += paths

	includes = []
	for directory in directories:
		includes.append(f"-I {directory}")

	dependencies = {}
	for source in sources:
		output = generate_dependencies(config, source, includes)
		if output == ERROR:
			return ERROR
		output = output.split()

		location = os.path.split(source)[0]
		object = f"{location}/{output[0]}"

		dependency_list = []
		for dependency in output[1:]:
			if dependency == "\\":
				continue
			dependency_list.append(dependency)

		dependencies.update({object: dependency_list})

	print(dependencies)

	#for object in dependencies:
		#out_of_date(object, dependencies[object])

	return SUCCESS

exit(main())
