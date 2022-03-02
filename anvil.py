import os
import json
import subprocess
import log
import shutil

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
	"SRC": list
}

# ===================== UTIL ===================== #

def clean_path(path):
	if path.startswith("./"):
		return path.replace("./", "")
	return path

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

	for i in range(len(sources)):
		sources[i] = clean_path(sources[i])
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

	for i in range(len(directories)):
		directories[i] = clean_path(directories[i])
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

def objects_out_of_date(object, dependencies):
	if not os.path.exists(object):
		log.debug(f"'{object}' has never been compiled")
		return True
	last_compiled = os.stat(object).st_mtime
	for dependency in dependencies:
		last_modified = os.stat(dependency).st_mtime
		if last_compiled < last_modified:
			log.debug(f"'{object}' is out of date")
			return True

def binary_out_of_date(binary, objects):
	if not os.path.exists(binary):
		log.debug(f"'{binary}' has never been linked")
		return True
	last_compiled = os.stat(binary).st_mtime
	for object in objects:
		last_modified = os.stat(object).st_mtime
		if last_compiled < last_modified:
			log.debug(f"'{binary}' is out of date")
			return True

# ===================== BUILD ===================== #

def compile(object, source, config, includes):
	CC = config['CC']
	CCFLAGS = " ".join(config['CCFLAGS'])
	INC = " ".join(includes)
	OBJ = object
	SRC = source

	command = f"{CC} {CCFLAGS} {INC} -o {OBJ} -c {SRC}"
	log.debug(command)
	try:
		output = subprocess.check_output(command, shell = True, text = True)
	except subprocess.CalledProcessError as exception:
		log.error(f"CC  {SRC}")
		return ERROR

	log.success(f"CC  {SRC}")
	return SUCCESS

def link(objects, config, includes):
	CC = config['CC']
	EXE = f"{config['ART']}/{config['EXE']}"
	LDFLAGS = " ".join(config['LDFLAGS'])
	LDLIBS = " ".join(config['LDLIBS'])
	INC = " ".join(includes)
	objects = list(objects)
	OBJ = " ".join(objects)

	command = f"{CC} {LDFLAGS} {INC} {LDLIBS} -o {EXE} {OBJ}"
	log.debug(command)
	try:
		output = subprocess.check_output(command, shell = True, text = True)
	except subprocess.CalledProcessError as exception:
		log.error(f"LD  {OBJ}")
		return ERROR

	log.success(f"LD  {OBJ}")
	log.success(f"EXE {EXE}")
	return SUCCESS

# ===================== MAIN ===================== #

SUBCOMMANDS = ["make", "clean"]

def anvil(command):
	config = load_config(CONFIG_FILE_NAME)
	if config == ERROR or verify_config(config) == ERROR:
		return ERROR

	artifacts = config['ART']
	if command == "clean":
		if os.path.exists(artifacts):
			shutil.rmtree(artifacts)
			log.success(f"RM {clean_path(artifacts)}/")
		return SUCCESS

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

	if not os.path.exists(artifacts):
		os.mkdir(artifacts)
		log.success(f"MKDIR '{artifacts}'")
	for directory in directories:
		directory = f"{artifacts}/{directory}"
		if not os.path.exists(directory):
			log.note(directory)
			os.mkdir(directory)
			log.success(f"MKDIR '{directory}'")

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
		object = clean_path(object)
		object = f"{artifacts}/{object}"

		dependency_list = []
		for dependency in output[1:]:
			if dependency == "\\":
				continue
			dependency_list.append(dependency)

		dependencies.update({object: dependency_list})

	objects = dependencies.keys()
	relink = False
	for object in objects:
		if objects_out_of_date(object, dependencies[object]):
			source = object.replace(f"{artifacts}/", "").replace(".o", ".c")
			if compile(object, source, config, includes) == ERROR:
				return ERROR
			relink = True

	binary = config['EXE']
	if binary_out_of_date(f"{artifacts}/{binary}", objects):
		relink = True

	if relink:
		if link(objects, config, includes) == ERROR:
			return ERROR

	return SUCCESS

MAX_ARGC = 2
MIN_ARGC = 1

def main():
	argc = len(argv)
	if argc < MIN_ARGC or argc > MAX_ARGC:
		log.error("Incorrect arguments")
		return ERROR

	subcommand = "make"
	if argc > 1:
		subcommand = argv[1]
	if subcommand not in SUBCOMMANDS:
		log.error(f"Unknown subcommand '{subcommand}'")
		return ERROR

	log.suppress(log.Level.DEBUG)
	anvil(subcommand)

exit(main())
