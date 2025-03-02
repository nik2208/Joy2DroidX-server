"""
Compatibility wrapper per supportare client Socket.IO di versioni diverse.
"""
import logging
from socketio import AsyncServer

logger = logging.getLogger('J2DX.compatibility')

class CompatibilityWrapper:
    """
    Wrapper che garantisce la compatibilità tra versioni diverse di Socket.IO
    """
    
    def __init__(self, server: AsyncServer):
        """
        Inizializza il wrapper.
        """
        self.sio = server
        self._register_adapters()
        
    def _register_adapters(self):
        """
        Registra adattatori per gestire diversi formati di messaggi.
        """
        @self.sio.on('connect')
        async def on_connect(sid, environ):
            logger.debug(f"Connection detected: {sid}")
            try:
                # Verifica la versione del client
                query = environ.get('asgi.scope', {}).get('query_string', b'').decode()
                if 'EIO=3' in query:
                    logger.info(f"Socket.IO v3 client detected: {sid}")
                elif 'EIO=4' in query:
                    logger.info(f"Socket.IO v4 client detected: {sid}")
                else:
                    logger.info(f"Unknown Socket.IO version, assuming latest: {sid}")
            except Exception as e:
                logger.error(f"Error detecting client version: {e}")
    
    def register_handler(self, event, handler):
        """
        Registra un handler per un evento specifico.
        """
        @self.sio.on(event)
        async def wrapped_handler(sid, *args, **kwargs):
            try:
                # Normalizza i dati in base alla versione
                if len(args) == 1 and isinstance(args[0], dict):
                    # Formato moderno: singolo oggetto
                    return await handler(sid, args[0])
                elif len(args) > 0:
                    # Formato legacy v3: multipli argomenti
                    if event == 'input' and len(args) >= 2:
                        data = {'key': args[0], 'value': args[1]}
                        return await handler(sid, data)
                # Chiamata normale
                return await handler(sid, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {event} handler: {e}")
                return {'error': str(e)}
