#!/bin/bash
set -Eeuxo pipefail
PS4='>>> '
TOP="${PWD}"

# This script is designed to be run from a Concourse Task with the following env vars

USAGE="STANZA_CONFIG=/path $0"

# Required env var inputs
echo "     STANZA_CONFIG:" "${STANZA_CONFIG:?Usage: ${USAGE}}"          # directory where .stanza config file is stored, as in normal stanza behavior

# Defaulted env var inputs - can override if necessary
echo "              REPODIR:" "${REPODIR:=slm}"
echo "       CREATE_ARCHIVE:" "${CREATE_ARCHIVE:=false}"
echo "       CREATE_PACKAGE:" "${CREATE_PACKAGE:=false}"
echo "      SIGN_EXECUTABLE:" "${SIGN_EXECUTABLE:=false}"
echo "   SLM_BUILD_PLATFORM:" "${SLM_BUILD_PLATFORM:=$(uname -s)}"  # linux|macos|windows
echo "                  VER:" "${VER:=$(git -C ${REPODIR} describe --tags --abbrev=0)}"
echo "                 MAKE:" "${MAKE:=make}"  # override with gmake on mac

# special case - if STANZA_CONFIG starts with "./", then replace it with the full path
[[ ${STANZA_CONFIG::2} == "./" ]] && STANZA_CONFIG=${PWD}/${STANZA_CONFIG:2}
[[ ! -e "${STANZA_CONFIG}/include" ]] && echo "ERROR: this build script requires $STANZA_CONFIG/include to point to stanza include files" && exit -1
export STANZA_CONFIG

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

CONAN_OPTS="-vtrace"
if [ "$SIGN_EXECUTABLE" == "true" ] ; then
    CONAN_OPTS=" -o:h codesign=True ${CONAN_OPTS}"
fi
export CONAN_OPTS

${MAKE}

if [ "$CREATE_PACKAGE" == "true" ] ; then
  #VERU=${VER//./_}  # convert dots to underscores
  STANZA_EXT=""
  [[ "${STANZA_PLATFORMCHAR}" == "w" ]] && STANZA_EXT=".exe"

  # find the directory where conan put the packaged files
  # assume there is already a venv set up with conan installed
  [ -e venv/Scripts/activate ] && source venv/Scripts/activate || source venv/bin/activate
  export CONAN_HOME=$PWD/.conan2
  CVER=$(conan list -c -f json slm/* | jq -r '."Local Cache" | keys | .[]' | sort -V | tail -1)
  CPKG=$(conan list -c -f json $CVER:* | jq -r '."Local Cache" | to_entries[0].value.revisions | to_entries[0].value.packages | keys_unsorted | first')
  CPATH=$(conan cache path ${CVER}:${CPKG})

  FILES="$CPATH/bin/slm \
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
