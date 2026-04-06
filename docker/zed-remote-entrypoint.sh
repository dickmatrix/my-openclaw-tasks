#!/usr/bin/env bash
set -euo pipefail

DEV_USER="${DEV_USER:-dev}"
DEV_UID="${DEV_UID:-1001}"
DEV_GID="${DEV_GID:-1001}"
AUTH_FILE="/etc/zed-remote/authorized_keys"

if ! getent group "$DEV_GID" >/dev/null 2>&1; then
  groupadd -g "$DEV_GID" "$DEV_USER"
fi

if ! id -u "$DEV_USER" >/dev/null 2>&1; then
  useradd -m -u "$DEV_UID" -g "$DEV_GID" -s /bin/bash "$DEV_USER"
fi

echo "$DEV_USER ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/90-zed-remote
chmod 440 /etc/sudoers.d/90-zed-remote

mkdir -p "/home/$DEV_USER/.ssh"
if [[ -f "$AUTH_FILE" ]]; then
  cp "$AUTH_FILE" "/home/$DEV_USER/.ssh/authorized_keys"
  chmod 600 "/home/$DEV_USER/.ssh/authorized_keys"
fi
chmod 700 "/home/$DEV_USER/.ssh"
chown -R "$DEV_UID:$DEV_GID" "/home/$DEV_USER/.ssh"

mkdir -p /run/sshd
exec /usr/sbin/sshd -D -e
