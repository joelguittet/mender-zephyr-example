#!/bin/bash

device_id=$0
command=$1

# Start socat with explicit PTY links
socat -d -d pty,raw,echo=0,link=/tmp/mender_cli_pty1 pty,raw,echo=0,link=/tmp/mender_cli_pty2 &
SOCAT_PID=$!
sleep 1

# Start men der-cli terminal
mender-cli terminal ${device_id} < /tmp/mender_cli_pty1 | tee /tmp/mender.log &
sleep 5

# Print expected command to the terminal
printf "${command}\n" > /tmp/mender_cli_pty2
sleep 1

# Disconnect
printf "\x1d" > /tmp/mender_cli_pty2
sleep 1

# Stop socat
sudo kill -9 $SOCAT_PID
