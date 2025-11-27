#!/bin/bash
# @file      mender-cli.sh
# @brief     mender-cli terminal wrapper
#
# Copyright joelguittet and mender-mcu-client contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

server=$1
device_id=$2
command=$3

# Start socat with explicit PTY links
socat -d -d pty,raw,echo=0,link=/tmp/mender_cli_pty1 pty,raw,echo=0,link=/tmp/mender_cli_pty2 &
SOCAT_PID=$!
sleep 1
echo "SOCAT DONE $SOCAT_PID"
# Start mender-cli terminal
mender-cli terminal $device_id --skip-verify --server $server < /tmp/mender_cli_pty1 > /tmp/mender_cli_pty1 &
sleep 10
echo "CLI DONE"
# Check if prompt is received
output=$(timeout 30s dd if=/tmp/mender_cli_pty2 iflag=nonblock status=none)
if [[ "$output" != *"\$"* ]]; then
    # Prompt not found, exit
    echo "PROMPT NOT FOUND in OUTPUT='$output'"
    # Stop socat
    kill -TERM $SOCAT_PID > /dev/null 2>&1
    exit 1
fi
echo "PROMPT FOUND in OUTPUT='$output'"
# Print expected command to the terminal
printf "$command\n" > /tmp/mender_cli_pty2
sleep 1
echo "COMMAND SENT"
# Disconnect
printf "\x1d" > /tmp/mender_cli_pty2
sleep 1
echo "DISCON"
# Read result
timeout 3s dd if=/tmp/mender_cli_pty2 iflag=nonblock status=none 2>/dev/null | tail -n +2
echo "FLUSH DONE"
# Stop socat
kill -TERM $SOCAT_PID > /dev/null 2>&1
echo "SOCAT END"
exit 0
