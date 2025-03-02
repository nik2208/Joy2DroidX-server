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
        self._register_middleware()
        
    def _register_middleware(self):
        """
        Registra middleware per gestire diversi formati di messaggi.
        """
        @self.sio.on('connect')
        async def on_connect(sid, environ):
            logger.debug(f"Connection detected: {sid}")
            try:
                # Ottieni informazioni sulla versione del client
                query_string = ""
                if 'QUERY_STRING' in environ:
                    query_string = environ['QUERY_STRING']
                elif 'asgi.scope' in environ:
                    query_string = environ['asgi.scope'].get('query_string', b'').decode()
                
                if 'EIO=3' in query_string:
                    logger.info(f"Socket.IO v3 client detected: {sid}")
                elif 'EIO=4' in query_string:
                    logger.info(f"Socket.IO v4 client detected: {sid}")
                else:
                    logger.info(f"Unknown Socket.IO version, assuming v4: {sid}")
            except Exception as e:
                logger.error(f"Error detecting client version: {e}")
        
        # Intercept events before they're processed to standardize format
        @self.sio.event
        async def input(sid, *args, **kwargs):
            try:
                # Handle different input formats from different client versions
                if len(args) == 1 and isinstance(args[0], dict):
                    # Modern Socket.IO format (single object)
                    return {'key': args[0].get('key'), 'value': args[0].get('value')}
                elif len(args) >= 2:
                    # Legacy Socket.IO v3 format (multiple arguments)
                    return {'key': args[0], 'value': args[1]}
            except Exception as e:
                logger.error(f"Error normalizing input data: {e}")
                return {'error': str(e)}
    
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
