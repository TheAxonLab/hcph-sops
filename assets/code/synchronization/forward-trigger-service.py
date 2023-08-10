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
"""A signal server listening to scanner trigger events (`s` key press) and psychopy events."""
from pathlib import Path
import serial
import asyncio
import logging

import janus
import keyboard


LISTEN = 2023
SERIAL_PORT = "/dev/ttyACM0"
LOG_FILE = Path.home() / "var" / "log" / "forward-trigger-service.log"

LOG_FILE.parent.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    level=logging.DEBUG,
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    async_q: janus.AsyncQueue[int],
) -> None:
    """
    Handle client connections.

    Read incoming data from the client and put it into the async queue.

    Parameters:
        reader (asyncio.StreamReader): The client's stream reader.
        async_q (janus.AsyncQueue[int]): The async queue for storing incoming signals.

    """
    while True:
        try:
            data = await reader.readexactly(1)
        except asyncio.exceptions.IncompleteReadError:
            await asyncio.sleep(0.1)  # Add a small delay to avoid busy waiting
            continue
        finally:
            writer.close()

        if data > b"\xff" or data < b"\x01":
            logging.warning(f"Received invalid signal <{data}>")
            continue

        # Disallow receiving 00000001 on the socket, replace with 10000001
        if data == b"\x01":
            data = b"\x81"
            logging.warning(
                "Trigger signal received through socket -- replaced with <\\x81>"
            )

        logging.info(f"Data received: <{data}>")
        await async_q.put(data)


async def start_server(host: str, port: int, async_q: janus.AsyncQueue[int]) -> None:
    """
    Start the server.

    Create a server that listens for client connections and handles them.

    Parameters:
        host (str): The server's host address.
        port (int): The server's port number.
        async_q (janus.AsyncQueue[int]): The async queue for storing incoming signals.

    """
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, async_q), host, port
    )
    addr = server.sockets[0].getsockname()
    logging.info(f"Server listening on {addr}")
    async with server:
        await server.serve_forever()


async def forward_signals(serial_port: str, async_q: janus.AsyncQueue[int]) -> None:
    """
    Forward incoming signals to the serial port.

    Read signals from the async queue and write them to the serial port.

    Parameters:
        serial_port (str): The serial port to forward the signals to.
        async_q (janus.AsyncQueue[int]): The async queue storing the signals.

    """
    with serial.Serial(serial_port) as ser:
        while True:
            signal = await async_q.get()
            ser.write(signal)
            async_q.task_done()
            logging.info(f"Forwarded <{signal}>")


def _trigger(sync_q: janus.SyncQueue[int]) -> None:
    """
    Trigger the signal sync queue.

    Put a signal into the sync queue.

    Parameters:
        sync_q (janus.SyncQueue[int]): The sync queue for triggering the signal.

    """
    sync_q.put(b"\x01")
    sync_q.join()
    logging.info("Scanner trigger received")


async def main() -> None:
    """
    Main function.

    Run the signal server and forward the signals to the serial port.

    """

    # Initiate a Queue that has synchronous and asynchronous endpoints.
    signal_queue: janus.Queue[int] = janus.Queue()

    # Attach an event listener to all `s` key presses.
    keyboard.on_press_key("s", lambda key: _trigger(signal_queue.sync_q))

    # Spin up socket listener and (asynchronously) queue up signals arriving from the socket
    await asyncio.gather(
        start_server("localhost", LISTEN, signal_queue.async_q),
        forward_signals(SERIAL_PORT, signal_queue.async_q),
    )


if __name__ == "__main__":
    asyncio.run(main())
