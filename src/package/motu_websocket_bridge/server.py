import asyncio
import tornado.web
import tornado.websocket
import logging
import json
import random
from typing import Union
from motu_websocket_bridge.datastore_client import DatastoreClient

logger: logging.Logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("motu_websocket_bridge.log"), logging.StreamHandler()],
)


class DatastoreHandler(tornado.websocket.WebSocketHandler):
    """
    Handles websocket connections for the AVB datastore.
    """
    def initialize(self, avb_server_url: str) -> None:
        super().initialize()
        self.avb_server_url = avb_server_url

    async def open(self, *args, **kwargs: str) -> None:
        """
        Called when the connection is opened by client. For example, in DevTools:

            var ws = new WebSocket("ws://localhost:8889/datastore");
            ws.onopen = function() {
                console.log("opened")
            };

            ws.onmessage = function (evt) {
                console.log(evt.data)
            };

        Sets up a DatastoreClient object and begins an asyncio loop to
        long-poll the AVB server. Any updates in the DatastoreClient will be passed
        down to the connected websocket client through the write_message method.

        Websocket clients can update the datastore by sending messages on the socket, e.g. in DevTools:

            ws.send(JSON.stringify({ "ext/ibankDisplayOrder": "2:1:0"}));            
        """
        path: str = args[0]
        self.client_id: int = random.randint(0, pow(2, 32)-1)

        logger.info(f"Client {self.client_id} Connected - creating a datastore loop.")

        self.client: DatastoreClient = DatastoreClient(
            self.avb_server_url, 
            client_id=self.client_id,
            path=path
        )
        self.datastore_loop: asyncio.Task = asyncio.create_task(
            self.client.run(self.write_message)
        )

    def check_origin(self, origin) -> bool:
        """
        Allow all clients (Bypass CORS checks)
        """
        return True

    def on_close(self) -> None:
        """
        Called when the websocket client closes the connection.
        Clean up the DatastoreClient by telling it to stop polling for updates.
        """
        logger.info(f"Client {self.client_id} Disconnected - stopping the datastore loop.")
        self.client.stop()

    async def on_message(self, message: Union[str, bytes]) -> None:
        """
        Handles incoming messages from the websocket client.
        
        When a client sends a message to update values, pass this on to the datastore client.

        e.g. in DevTools:

            ws.send(JSON.stringify({ "ext/ibankDisplayOrder": "2:1:0"}));    
        """
        logger.info(f"Client {self.client_id} sent a message: {message}")
        await self.client.send(json.loads(message), self.write_message)


def make_app(avb_server_url: str) -> tornado.web.Application:
    """
    Create the tornado application with the datastore handler.

    Future updates might include a "meters" handler.
    """
    return tornado.web.Application([
        (r"/datastore[/]*(.*)", DatastoreHandler, dict(avb_server_url=avb_server_url)),
    ])


async def main(avb_server_url:str, port:int=8889) -> None:
    """
    Create the tornado server.
    """
    app = make_app(avb_server_url)
    app.listen(port)
    logger.info(f"Server listening at http://localhost:{port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main("http://localhost:8888"))