"""
Strumenti di diagnostica per testare la connessione client-server.
"""
import asyncio
import argparse
import sys
import socketio

async def test_connection(host='localhost', port=8013, eio_version=4):
    """
    Testa la connessione al server J2DX.
    """
    url = f'http://{host}:{port}'
    print(f"Tentativo di connessione a {url} con EIO={eio_version}")
    
    if eio_version == 3:
        # Client Socket.IO v3
        sio = socketio.AsyncClient(engineio_logger=True)
    else:
        # Client Socket.IO v4/v5 (moderno)
        sio = socketio.AsyncClient(engineio_logger=True)
    
    @sio.event
    async def connect():
        print("✓ Connessione stabilita!")
        await sio.emit('xbox')
        print("✓ Richiesta controller Xbox inviata")
        
        # Test input standard
        await sio.emit('input', {'key': 'a-button', 'value': True})
        print("✓ Test pressione pulsante A")
        await asyncio.sleep(0.5)
        
        await sio.emit('input', {'key': 'a-button', 'value': False})
        print("✓ Test rilascio pulsante A")
        await asyncio.sleep(0.5)
        
        # Test input analogico
        await sio.emit('input', {'key': 'left-stick-X', 'value': 0.5})
        print("✓ Test movimento stick")
        await asyncio.sleep(0.5)
        
        await sio.emit('input', {'key': 'left-stick-X', 'value': 0})
        print("✓ Test movimento stick a riposo")
        
        print("Test completato con successo!")
        await sio.disconnect()
    
    @sio.event
    async def connect_error(data):
        print(f"✗ Errore di connessione: {data}")
    
    try:
        # Usa l'EIO version specificata
        if eio_version == 3:
            await sio.connect(url, transports=['websocket'], engineio_path='socket.io')
        else:
            await sio.connect(url, transports=['websocket'])
        await asyncio.sleep(5)  # Aspetta il completamento dei test
    except Exception as e:
        print(f"✗ Errore: {e}")
    finally:
        if sio.connected:
            await sio.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Test di connessione a J2DX')
    parser.add_argument('--host', default='localhost', help='Host del server J2DX')
    parser.add_argument('--port', type=int, default=8013, help='Porta del server J2DX')
    parser.add_argument('--eio', type=int, choices=[3, 4], default=4, 
                      help='Versione Engine.IO da usare (3 o 4)')
    
    args = parser.parse_args()
    asyncio.run(test_connection(args.host, args.port, args.eio))

if __name__ == "__main__":
    main()
