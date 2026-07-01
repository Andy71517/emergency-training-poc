# API Layer

This layer is the front door of the backend.

It owns the health endpoint and the WebSocket session endpoint. It checks message shape, turns errors into client-friendly responses, and sends state updates back.

It does not own scenario rules. That stays in the engine and validation layers.
