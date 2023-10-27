#!/bin/sh

set -eu

STANZA_DIR="$(pwd)/.deps/stanza"
mkdir -p "${STANZA_DIR}"

# Download archive from lbstanza.org and unpack
wget "https://github.com/StanzaOrg/lbstanza/releases/download/0.18.52/lstanza_0_18_52.zip" \
    -O stanza.zip
unzip stanza.zip -d "${STANZA_DIR}"
rm -rf stanza.zip

# Create .stanza in the newly-unpacked Stanza dir
cat > "${STANZA_DIR}/.stanza" <<EOF
install-dir = "${STANZA_DIR}"
platform = linux
EOF

# Create Stanza env file for next step
cat > "$(pwd)/stanza.env" <<EOF
export PATH="${STANZA_DIR}:\$PATH"
export STANZA_CONFIG="${STANZA_DIR}"
EOF
