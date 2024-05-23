#!/bin/sh

set -eu

SLM_STANZA_DIR="$(pwd)/.deps/stanza"
mkdir -p "${SLM_STANZA_DIR}"

# Download archive from lbstanza.org and unpack
wget "https://github.com/StanzaOrg/lbstanza/releases/download/0.18.52/lstanza_0_18_52.zip" \
    -O stanza.zip
unzip stanza.zip -d "${SLM_STANZA_DIR}"
rm -rf stanza.zip

# Create .stanza in the newly-unpacked Stanza dir
cat > "${SLM_STANZA_DIR}/.stanza" <<EOF
install-dir = "${SLM_STANZA_DIR}"
platform = linux
EOF

# Create Stanza env file for next step
cat > "$(pwd)/stanza.env" <<EOF
export PATH="${SLM_STANZA_DIR}:\$PATH"
export STANZA_CONFIG="${SLM_STANZA_DIR}"
EOF
