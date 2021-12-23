#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import pathlib
import websockets
import logging

from vosk import BatchRecognizer, GpuInit


async def recognize(websocket, path):
    global args
    global loop
    global pool
    global rec
    global client_cnt

    uid = client_cnt
    client_cnt += 1

    logging.info('Connection %d from %s', uid, websocket.remote_address);

    while True:

        message = await websocket.recv()

        if message == '{"eof" : 1}':
            rec.FinishStream(uid)
            break

        if isinstance(message, str) and 'config' in message:
            continue

        rec.AcceptWaveform(uid, message)

        while rec.GetPendingChunks(uid) > 0:
            await asyncio.sleep(0.1)

        res = rec.Result(uid)
        if len(res) == 0:
            await websocket.send('{ "partial" : "" }')
        else:
            await websocket.send(res)

    while rec.GetPendingChunks(uid) > 0:
        await asyncio.sleep(0.1)

    res = rec.Result(uid)
    await websocket.send(res)

def start():

    global rec
    global args
    global loop
    global client_cnt

    # Enable loging if needed
    #
    # logger = logging.getLogger('websockets')
    # logger.setLevel(logging.INFO)
    # logger.addHandler(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO)

    args = type('', (), {})()

    args.interface = os.environ.get('VOSK_SERVER_INTERFACE', '0.0.0.0')
    args.port = int(os.environ.get('VOSK_SERVER_PORT', 2700))

    GpuInit()

    rec = BatchRecognizer()

    client_cnt = 0

    loop = asyncio.get_event_loop()

    start_server = websockets.serve(
        recognize, args.interface, args.port)

    logging.info("Listening on %s:%d", args.interface, args.port)
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == '__main__':
    start()
