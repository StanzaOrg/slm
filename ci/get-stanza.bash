#!/usr/bin/env bash


set -eu

STANZA_INSTALL_DIR="$1"

STANZA_ZIP=""

cat > "${HOME}/.stanza" <<EOF
install-dir = "${STANZA_INSTALL_DIR}"
platform = linux
EOF

ln -s "${STANZA_INSTALL_DIR}/stanza" /usr/bin/stanza
