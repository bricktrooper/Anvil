import os
import json
import subprocess
import log

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

# ===================== CONFIG ===================== #

def load_config(path):
	if not os.path.exists(path):
		log.error(f"Cannot find config file '{path}'")
		return ERROR
	file = open(path, "r")
	config = json.load(file)
	file.close()
	log.info(f"Loaded build config from '{path}'")
	return config

def verify_config(config):
	for field in CONFIG_FIELDS.keys():
		if field not in config.keys():
			log.error(f"'{field}' not found in build configuration")
			return ERROR

	for field in config.keys():
		if field not in CONFIG_FIELDS.keys():
			log.warning(f"Ignoring unknown field '{field}' in build configuration")
			continue

		actual_type = type(config[field])
		expected_type = CONFIG_FIELDS[field]

		if actual_type != expected_type:
			log.error(f"Incorrect type '{actual_type}' for '{field}' ({expected_type})")
			return ERROR

		if actual_type == list:
			for item in config[field]:
				if type(item) != str:
					log.error(f"'{field}' must only contain strings")
					return ERROR

	if config['ART'] == "":
		log.error(f"'ART' was not specified")
		return ERROR
	if config['EXE'] == "":
		log.error(f"'EXE' was not specified")
		return ERROR
	if config['CC'] == "":
		log.error(f"'CC' was not specified")
		return ERROR
	if len(config['SRC']) == 0:
		log.error(f"'SRC' was not specified")
		return ERROR

	return SUCCESS

# ===================== DEPENDENCIES ===================== #

def discover_source_files(path):
	if not os.path.isdir(path):
		log.error(f"Source path '{path}' is not a directory'")
		return ERROR

	log.debug(f"Searching '{path}/' for source files")
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
			log.debug(f"Discovered source file '{file}'")

	return sources

def discover_directories(path):
	directories = []
	if not os.path.isdir(path):
		log.error(f"Source path '{path}' is not a directory'")
		return ERROR

	log.debug(f"Discovered directory '{path}/'")
	directories.append(path)

	log.debug(f"Searching '{path}/' for directories")
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
		log.error(f"Failed to generate dependencies for '{source}'")
		return ERROR
	return output

def out_of_date(object, dependencies):
	if not os.path.exists(object):
		log.debug(f"'{object}' has never been compiled")
		return True
	last_compiled = os.stat(object).st_mtime
	for dependency in dependencies:
		last_modified = os.stat(dependency).st_mtime
		if last_compiled < last_modified:
			log.debug(f"'{object}' is out of date")
			return True

# ===================== BUILD ===================== #

def compile(object, source, config, includes):
	CC = config['CC']
	CCFLAGS = " ".join(config['CCFLAGS'])
	INC = " ".join(includes)

	command = f"{CC} {CCFLAGS} {INC} -o {object} -c {source}"
	log.debug(command)
	try:
		output = subprocess.check_output(command, shell = True, text = True)
	except subprocess.CalledProcessError as exception:
		log.error(f"CC {source}")
		return ERROR

	log.success(f"CC {source}")
	return SUCCESS

def link(objects):
	#LDFLAGS = " ".join(config['LDFLAGS'])
	#LDLIBS = " ".join(config['LDLIBS'])
	pass

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

	artifacts = config['ART']

	if not os.path.exists(artifacts):
		os.mkdir(artifacts)
	for directory in directories:
		directory = f"{artifacts}/{directory}"
		if not os.path.exists(directory):
			os.mkdir(directory)

	includes = []
	for directory in directories:
		includes.append(f"-I {directory}")

	dependencies = {}
	for source in sources:
		output = generate_dependencies(config, source, includes)
		if output == ERROR:
			return ERROR
		output = output.split()

		object = source.replace(".c", ".o")
		object = f"{artifacts}/{object}"
		dependency_list = []
		for dependency in output[1:]:
			if dependency == "\\":
				continue
			dependency_list.append(dependency)

		dependencies.update({object: dependency_list})

	for object in dependencies.keys():
		if out_of_date(object, dependencies[object]):
			source = object.replace(f"{artifacts}/", "").replace(".o", ".c")
			print(source)
			compile(object, source, config, includes)

	return SUCCESS

log.suppress(log.Level.DEBUG)
exit(main())
