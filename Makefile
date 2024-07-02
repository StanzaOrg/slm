
# this makefile uses bash commands
SHELL := /bin/bash
# inherit these variables from the environment, with defaults if unspecified in the environment
PYTHON ?= python
CONAN ?= conan
SED ?= sed
CONAN_HOME ?= $(shell pwd)/.conan2
CONAN_OPTS ?= -vtrace
CONAN_BUILD_PROFILE ?= default
CONAN_HOST_PROFILE ?= default
# execute all lines of a target in one shell
.ONESHELL:

.PHONY: all
all: build

.PHONY: build
build:
	@echo -e "\n*** Makefile: build: creating venv ***"
	if [ "$$VIRTUAL_ENV" == "" ] ; then
	    echo "creating python virtual environment in ./venv"
	    ${PYTHON} -m venv venv
	    source venv/bin/activate
	    pip install -r requirements.txt
	fi

	echo -e "\n*** Makefile: build: configuring conan ***"
	export CONAN_HOME="${CONAN_HOME}"  # copy from make env to bash env
	${CONAN} config install conan-config
	 #${CONAN} remote enable conancenter
	[ ! -e ".conan2/profiles/default" ] && ${CONAN} profile detect
	(cd conan_lbstanza_generator && ${CONAN} create .)

	 # get the current project name from the slm.toml file
	SLMPROJNAME=$$(${SED} -n -e '/^ *name *= *"*\([^"]*\).*/{s//\1/;p;q}' slm.toml)
	SLMPROJVER=$$(${SED} -n -e '/^ *version *= *"*\([^"]*\).*/{s//\1/;p;q}' slm.toml)

	 # build slm and link to dependency libs using stanza.proj fragments
	 # build only the current project, not any dependencies
	echo -e "\n*** Makefile: build: building \"$${SLMPROJNAME}/$${SLMPROJVER}\" ***"
	${CONAN} create \
	    -pr:b ${CONAN_BUILD_PROFILE} -pr:h ${CONAN_HOST_PROFILE} \
	    ${CONAN_OPTS} \
	    --build "$${SLMPROJNAME}/$${SLMPROJVER}" .

	 # copy executable from conan package dir to current dir for convenince
	CVER=$$(${CONAN} list -vnotice -c -f json "$${SLMPROJNAME}/$${SLMPROJVER}" | jq -r '."Local Cache" | keys | sort | last')
	CPKG=$$(${CONAN} list -c -f json $$CVER:* | jq -r '."Local Cache" | to_entries[0].value.revisions | to_entries[0].value.packages | keys_unsorted | first')
	PKGDIR=$$(${CONAN} cache path "$${CVER}:$${CPKG}")
	cp -a $${PKGDIR}/bin/$${SLMPROJNAME} .
	ls -l ./$${SLMPROJNAME}

.PHONY: upload
upload:
	@echo -e "\n*** Makefile: upload: activating venv ***"
	if [ "$$VIRTUAL_ENV" == "" ] ; then
	    echo -e "*** Makefile: upload: using python virtual environment in ./venv ***"
	    source venv/bin/activate
	fi

	echo -e "\n*** Makefile: upload: configuring conan ***"
	export CONAN_HOME="${CONAN_HOME}"  # copy from make env to bash env
	${CONAN} remote enable artifactory
	 # expects user in CONAN_LOGIN_USERNAME_ARTIFACTORY and password in CONAN_PASSWORD_ARTIFACTORY
	${CONAN} remote login artifactory

	 # get the current project name from the slm.toml file
	SLMPROJNAME=$$(${SED} -n -e '/^ *name *= *"*\([^"]*\).*/{s//\1/;p;q}' slm.toml)
	SLMPROJVER=$$(${SED} -n -e '/^ *version *= *"*\([^"]*\).*/{s//\1/;p;q}' slm.toml)

	echo -e "\n*** Makefile: upload: uploading \"$${SLMPROJNAME}/$${SLMPROJVER}\" ***"
	${CONAN} upload -r artifactory $${SLMPROJNAME}/$${SLMPROJVER}

	cd slm_builder/conan_lbstanza_generator
	${CONAN} create .
	 # get the generator name and version from the conanfile.py file
	PYSLMPROJNAME=$$(${SED} -n -e '/^ *name *= *"*\([^"]*\).*/{s//\1/;p;q}' conanfile.py)
	PYSLMPROJVER=$$(${SED} -n -e '/^ *version *= *"*\([^"]*\).*/{s//\1/;p;q}' conanfile.py)
	-e "\n*** Makefile: upload: uploading \"$${PYSLMPROJNAME}/$${PYSLMPROJVER}\" ***"
	${CONAN} upload -r artifactory $${PYSLMPROJNAME}/$${PYSLMPROJVER}

.PHONY: clean
clean:
	@CLEANCMD="rm -rf .conan2 .slm build venv"
	echo $$CLEANCMD && eval $$CLEANCMD
	[ "x$$VIRTUAL_ENV" != "x" ] && [ ! -e "$$VIRTUAL_ENV" ] && printf "Virtual environment directory has been cleaned.\nRun 'deactivate' to exit from the virtual environment.\n" || true
