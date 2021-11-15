#!/bin/sh

cat > "${GITHUB_WORKSPACE}/.git-askpass" <<EOF
echo \$CI_TOKEN
EOF
chmod +x "${GITHUB_WORKSPACE}/.git-askpass"

cat > "${GITHUB_WORKSPACE}/.git-env" <<EOF
export GIT_ASKPASS="${GITHUB_WORKSPACE}/.git-askpass"
EOF
