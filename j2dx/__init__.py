print("Starting J2DX...")

import os
import sys
import logging
import platform
import socket
import asyncio
from argparse import ArgumentParser
import qrcode
# Importa AsyncServer invece di Server per usare il paradigma asincrono
from socketio import AsyncServer, ASGIApp
from uvicorn import Config, Server

if platform.system() == 'Linux':
    print("Linux system detected")
    from j2dx.nix.device import X360Device, DS4Device
    from j2dx.nix.setup import setup
    print("Linux modules imported")
elif platform.system() == 'Windows':
    print("Windows system detected")
    from j2dx.win.device import X360Device, DS4Device
    from j2dx.win.setup import setup
    print("Windows modules imported")

def get_logger(debug):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    wsgi_logger = logging.getLogger('eventlet.wsgi.server')
    wsgi_logger.setLevel(logging.INFO if debug else logging.ERROR)
    return (logging.getLogger('J2DX.server'), wsgi_logger)

def default_host():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('1.255.255.255', 1))
        IP = sock.getsockname()[0]
    except IndexError:
        IP = '127.0.0.1'
    finally:
        sock.close()
    return IP

def parse_args():
    print("Parsing arguments")
    parser = ArgumentParser()
    if platform.system() == 'Linux':
        parser.add_argument(
            'user',
            nargs='?',
            default=os.getenv('SUDO_USER'),
            help='Only used with --setup. User to configure for UInput access.'
        )
    parser.add_argument(
        '-s', '--setup',
        action='store_true',
        help='Setup system for virtual device creation.'
    )
    parser.add_argument(
        '-H', '--host',
        default=None,
        help='Hostname or IP address the server will listen on.'
    )
    parser.add_argument(
        '-p', '--port',
        type=int, default=8013,
        help='Port the server will listen on. Defaults to 8013.'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Print debug information.'
    )
    args = parser.parse_args()
    print(f"Arguments parsed: {args}")
    return args

def main():
    print("Entering main function")
    args = parse_args()
    logger, wsgi_logger = get_logger(args.debug)
    print(f"Args parsed: {args}")

    if args.setup:
        print("Setup mode detected")
        setup(args.user if platform.system() == 'Linux' else None)
        sys.exit(0)
        return

    print("Initializing server")
    CLIENTS = {}
    DEVICES = {}
    
    # Usa AsyncServer con configurazione moderna, ma senza modificare le versioni
    sio = AsyncServer(
        cors_allowed_origins=["*"],
        logger=args.debug,
        engineio_logger=args.debug,
        async_handlers=True,  # Importante per il supporto asincrono
        ping_interval=25000,
        ping_timeout=60000,
        max_http_buffer_size=10485760
    )

    # Usa gli handler asincroni moderni
    @sio.event
    async def connect(sid, environ):
        try:
            # Metodo moderno per ottenere l'indirizzo client
            scope = environ.get('asgi.scope', {})
            client_addr = scope.get('client', ['unknown', 0])[0]
            CLIENTS[sid] = client_addr
        except (KeyError, IndexError):
            CLIENTS[sid] = 'unknown'
        logger.info(f'Client connected from {CLIENTS[sid]}')
        logger.debug(f'Client {CLIENTS[sid]} sessionId: {sid}')

    @sio.event
    async def disconnect(sid):
        if sid in DEVICES:
            DEVICES[sid].close()
            del DEVICES[sid]
        if sid in CLIENTS:
            del CLIENTS[sid]
        logger.info(f'Client disconnected: {sid}')

    @sio.event
    async def xbox(sid):
        if sid not in DEVICES:
            DEVICES[sid] = X360Device(sid, CLIENTS[sid])
        logger.info(f'Xbox 360 controller created for {CLIENTS[sid]}')

    @sio.event
    async def ds4(sid):
        if sid not in DEVICES:
            DEVICES[sid] = DS4Device(sid, CLIENTS[sid])
        logger.info(f'DualShock 4 controller created for {CLIENTS[sid]}')

    @sio.event
    async def input(sid, data):
        if sid in DEVICES:
            DEVICES[sid].send(data['key'], data['value'])

    # Usa la configurazione ASGI moderna
    app = ASGIApp(
        socketio_server=sio,
        other_asgi_app=None,
        socketio_path='socket.io'
    )

    try:
        host = args.host or default_host()
        print(f"Starting server on {host}:{args.port}")
        logger.info(f'Listening on http://{host}:{args.port}/')
        
        qr = qrcode.QRCode()
        qr.add_data(f'j2dx://{host}:{args.port}/')
        if platform.system() == 'Windows':
            import colorama
            colorama.init()
        qr.print_ascii(tty=True)
        
        # Usa l'API moderna di uvicorn con configurazione esplicita
        config = Config(
            app=app,
            host=host,
            port=args.port,
            log_level="debug" if args.debug else "info",
            ws="websockets",
            workers=1,
            loop="auto",
            timeout_keep_alive=120,
            proxy_headers=True
        )
        
        server = Server(config)
        
        # Esegui il server in modo asincrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
        
    except PermissionError:
        sys.exit(
            f'Port {args.port} is not available. '
            f'Please specify a different port with -p option.'
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Running main")
    main()