#!/bin/bash
set -Eeuxo pipefail
PS4='>>> '
TOP="${PWD}"

# This script is designed to be run from a Concourse Task with the following env vars

USAGE="STANZA_CONFIG=/path $0"

# Required env var inputs
echo "     STANZA_CONFIG:" "${STANZA_CONFIG:?Usage: ${USAGE}}"          # directory where .stanza config file is stored, as in normal stanza behavior
echo "CONAN_USER_LOGIN_ARTIFACTORY:" "${CONAN_USER_LOGIN_ARTIFACTORY:?Error: user login required}"
echo "  CONAN_PASSWORD_ARTIFACTORY:" "${CONAN_PASSWORD_ARTIFACTORY:?Error: password required}"

# Defaulted env var inputs - can override if necessary
echo "              REPODIR:" "${REPODIR:=slm}"
echo "       CREATE_ARCHIVE:" "${CREATE_ARCHIVE:=false}"
echo "       CREATE_PACKAGE:" "${CREATE_PACKAGE:=false}"
echo "   SLM_BUILD_PLATFORM:" "${SLM_BUILD_PLATFORM:=$(uname -s)}"  # linux|macos|windows
echo "                  VER:" "${VER:=$(git -C ${REPODIR} describe --tags --abbrev=0)}"

# special case - if STANZA_CONFIG starts with "./", then replace it with the full path
[[ ${STANZA_CONFIG::2} == "./" ]] && STANZA_CONFIG=${PWD}/${STANZA_CONFIG:2}

PLATFORM_DESC="unknown"
case "$SLM_BUILD_PLATFORM" in
    Linux* | linux* | ubuntu*)
        SLM_BUILD_PLATFORM=linux
        STANZA_PLATFORMCHAR="l"
        PLATFORM_DESC="$(grep ^ID= /etc/os-release | cut -f2 -d=)-$(grep ^VERSION_CODENAME= /etc/os-release | cut -f2 -d=)"
    ;;
    Darwin | mac* | os-x)
        SLM_BUILD_PLATFORM=os-x
        STANZA_PLATFORMCHAR=""
        PLATFORM_DESC="macos-unknown"
        case "$(sw_vers -productVersion)" in
            13.*)
                PLATFORM_DESC="macos-ventura"
            ;;
            12.*)
                PLATFORM_DESC="macos-monterey"
            ;;
            11.*)
                PLATFORM_DESC="macos-bigsur"
            ;;
            10.15.*)
                PLATFORM_DESC="macos-catalina"
            ;;
            10.14.*)
                PLATFORM_DESC="macos-mojave"
            ;;
            10.13.*)
                PLATFORM_DESC="macos-highsierra"
            ;;
            10.12.*)
                PLATFORM_DESC="macos-sierra"
            ;;
        esac
    ;;
    MINGW* | win*)
        SLM_BUILD_PLATFORM=windows
        STANZA_PLATFORMCHAR="w"
        PLATFORM_DESC="windows-unknown"
        case "$(uname -s)" in
            MINGW64*)
                PLATFORM_DESC="windows-mingw64"
            ;;
        esac
    ;;
    *)
        printf "\n\n*** ERROR: unknown build platform \"${SLM_BUILD_PLATFORM}\"\n\n\n" && exit -2
    ;;
esac


cd "${REPODIR}"
echo "Building slm version ${VER} in ${PWD}"

# call the script to build slm
ci/build.sh
# verify that expected output file exists
ls slm

# create conan package
export SLM_ROOT_DIR=$PWD
CH=${CONAN_HOME:-$HOME/.conan2}
[ ! -e "${CH}/profiles/default" ] && conan profile detect
conan create .

# upload conan package
conan remote add artifactory  "http://44.226.24.141:8081/artifactory/api/conan/conan-local"
conan remote login artifactory jitx
conan upload -r artifactory --force slm/${VER}

if [ "$CREATE_PACKAGE" == "true" ] ; then
  #VERU=${VER//./_}  # convert dots to underscores
  STANZA_EXT=""
  [[ "${STANZA_PLATFORMCHAR}" == "w" ]] && STANZA_EXT=".exe"

  FILES="slm \
         LICENSE \
         README.md"

  mkdir -p ziptmp/build
  cp -r ${FILES} ziptmp/

  cd ziptmp

  zip -r ../slm-${PLATFORM_DESC}_${VER}.zip *
fi

# if [ "$CREATE_ARCHIVE" == "true" ] ; then
#   zip -r -9 -q slm-build-${PLATFORM}-${VER}.zip \
#      .conan \
#      .stanza \
#      CMakeUserPresets.json \
#      build
# fi
