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
