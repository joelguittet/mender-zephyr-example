# @file      test_foo.py
# @brief     Foo test file
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

#import logging
from twister_harness import Shell
from twister_harness import DeviceAdapter

#logger = logging.getLogger(__name__)

def test_sample(dut: DeviceAdapter):
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    #dut.readlines_until('Mender client authenticated')
    #dut.readlines_until('No deployment available')

def test_sample(dut: DeviceAdapter):
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    #dut.readlines_until('Mender client authenticated')
    #dut.readlines_until('No deployment available')
