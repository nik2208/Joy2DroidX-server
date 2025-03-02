print("Starting J2DX...")

import os
import sys
import logging
import platform
import socket
import asyncio
from argparse import ArgumentParser
import qrcode
# Import FastAPI and updated socketio imports
import socketio
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

# Import compatibility wrapper
from j2dx.compatibility_wrapper import CompatibilityWrapper

def get_logger(debug):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    wsgi_logger = logging.getLogger('uvicorn')
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
    
    # Create FastAPI app
    app = FastAPI(title="Joy2DroidX Server")
    
    # Add CORS middleware with broader settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup Socket.IO with more permissive CORS settings
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins="*",  # Allow all origins with string instead of list
        logger=args.debug,
        engineio_logger=args.debug,
        ping_interval=25000,
        ping_timeout=60000,
    )
    
    # Create Socket.IO application with FastAPI integration
    socket_app = socketio.ASGIApp(sio, app)
    
    # Create compatibility wrapper
    compat = CompatibilityWrapper(sio)
    
    # Define event handlers directly with the Socket.IO server
    @sio.event
    async def connect(sid, environ):
        try:
            client_addr = environ.get('REMOTE_ADDR', 'unknown')
            headers = environ.get('asgi.scope', {}).get('headers', [])
            
            # Try to get forwarded IP if behind proxy
            for name, value in headers:
                if name == b'x-forwarded-for':
                    client_addr = value.decode('utf-8').split(',')[0].strip()
                    break
                    
            CLIENTS[sid] = client_addr
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
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

    # Handler for Xbox controller request
    @sio.event
    async def xbox(sid, *args):
        if sid not in DEVICES:
            DEVICES[sid] = X360Device(sid, CLIENTS.get(sid, 'unknown'))
        logger.info(f'Xbox 360 controller created for {CLIENTS.get(sid, "unknown")}')

    # Handler for PS4/DS4 controller request
    @sio.event
    async def ds4(sid, *args):
        if sid not in DEVICES:
            DEVICES[sid] = DS4Device(sid, CLIENTS.get(sid, 'unknown'))
        logger.info(f'DualShock 4 controller created for {CLIENTS.get(sid, "unknown")}')

    # Handler for input events
    @sio.event
    async def input(sid, data):
        if sid in DEVICES:
            try:
                # Handle both object and separate parameters formats
                if isinstance(data, dict) and 'key' in data and 'value' in data:
                    key = data['key']
                    value = data['value']
                    
                    # Enhanced debug logging
                    input_type = "Button" if isinstance(value, bool) else "Analog"
                    logger.info(f"[INCOMING] {input_type} Input from {CLIENTS.get(sid, 'unknown')}: {key}={value}")
                    print(f"[RECEIVED] Input: {key}={value} from {CLIENTS.get(sid, 'unknown')}")
                    
                    DEVICES[sid].send(key, value)
                else:
                    logger.warning(f"Received invalid input format: {data}")
                    print(f"[ERROR] Invalid input format received: {data}")
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print(f"[ERROR] Processing input: {e}")

    # HTTP routes for fallback mechanism
    @app.get("/status")
    async def status():
        return {"status": "ok", "clients": len(CLIENTS)}
    
    @app.post("/message")
    async def message(data: dict):
        try:
            event = data.get("event")
            payload = data.get("data", {})
            
            if event == "xbox":
                # Create a temporary session ID for HTTP clients
                sid = f"http-{len(CLIENTS) + 1}"
                CLIENTS[sid] = "http-client"
                DEVICES[sid] = X360Device(sid, "http-client")
                return {"status": "ok", "controller": "xbox"}
            
            elif event == "ds4":
                # Create a temporary session ID for HTTP clients
                sid = f"http-{len(CLIENTS) + 1}"
                CLIENTS[sid] = "http-client"
                DEVICES[sid] = DS4Device(sid, "http-client")
                return {"status": "ok", "controller": "ds4"}
                
            elif event == "input" and isinstance(payload, dict):
                # Find an HTTP client to send input to
                http_sids = [sid for sid in DEVICES if sid.startswith("http-")]
                if http_sids:
                    sid = http_sids[0]
                    DEVICES[sid].send(payload.get("key"), payload.get("value"))
                    return {"status": "ok"}
                else:
                    return {"status": "error", "message": "No HTTP client device found"}
            
            elif event == "ping":
                return {"status": "ok", "pong": True}
                
            return {"status": "error", "message": "Unknown event"}
        except Exception as e:
            logger.error(f"Error handling HTTP message: {e}")
            return {"status": "error", "message": str(e)}

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
        
        # Run the Uvicorn server with the FastAPI app
        config = uvicorn.Config(
            app=socket_app, 
            host=host, 
            port=args.port,
            log_level="debug" if args.debug else "info",
        )
        server = uvicorn.Server(config)
        loop = asyncio.get_event_loop()
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