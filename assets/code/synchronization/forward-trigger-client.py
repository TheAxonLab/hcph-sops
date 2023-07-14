# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2023 The Axon Lab <theaxonlab@gmail.com>
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
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
import socket

LISTEN = 2023


def send_message(addr, message):
    """
    Send a message to the specified address.

    Parameters:
        addr (tuple[str, int]): The address to connect to, specified as a tuple of (host, port).
        message (bytes): The message to send as bytes.

    Raises:
        OSError: If there is an error in the socket operation.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(addr)
        client_socket.sendall(message)


def main():
    """
    Main entry point of the program.

    Connects to the server address and sends a message.
    """
    server_addr = ("localhost", LISTEN)
    message = b"\x02"
    send_message(server_addr, message)


if __name__ == "__main__":
    main()
