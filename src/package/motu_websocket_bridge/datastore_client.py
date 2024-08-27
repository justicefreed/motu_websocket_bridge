import aiohttp
import asyncio
import random
import logging
import json
from typing import Optional, Callable, Any

logger: logging.Logger = logging.getLogger(__name__)

class DatastoreClient:
    """
    A web client for the AVB datastore. When running, continuously
    polls for updates using the long-polling technique described in the
    AVB API documentation (See https://cdn-data.motu.com/downloads/audio/AVB/docs/MOTU%20AVB%20Web%20API.pdf)

    Allows updating of the datastore using the send method.
    """
    def __init__(self, avb_url: str, client_id: Optional[int], path: str="") -> None:
        self.path: str = path
        self.avb_url: str = avb_url
        self.client_id: int = client_id if client_id is not None else random.randint(0, pow(2, 32)-1)
        self.enabled: bool = False
        logger.info(f"{self.client_id}: Initialised new client for path: '{self.path}'")

    def stop(self):
        """
        sets self.enabled to False to stop polling at the next iteration.
        """
        logger.info(f"{self.client_id}: Disabling loop, which will stop at next iteration.")
        self.enabled = False

    @property
    def datastore_url(self) -> str:
        if self.path != "":
            return f"{self.avb_url}/datastore/{self.path}?client={self.client_id}"
        else:
            return f"{self.avb_url}/datastore?client={self.client_id}"
        
    async def send(self, message):
        """
        Sends an update to the AVB server with the given message.
        """
        async with aiohttp.ClientSession() as session:
            logger.info(f"{self.client_id}: sending update to {self.datastore_url}")
            async with session.patch(self.datastore_url, data={ "json": json.dumps(message)}) as response:
                if response.status != 200:
                    logger.warn("Error in update")

    async def run(self, write_message_callback: Callable[[Any], asyncio.Future[None]]) -> None:
        """
        Continuously polls for updates until self.enabled is set to False.
        """
        self.enabled = True
        etag = -1
        
        while self.enabled:
            headers = {
                "If-None-Match": str(etag)
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                logger.info(f"{self.client_id}: reading from {self.datastore_url}")
                async with session.get(self.datastore_url) as response:
                    etag = int(response.headers["ETag"])
                    if response.status == 304:
                        logger.info(f"{self.client_id}: nothing to update")
                    else:
                        logger.info(f"{self.client_id}: sending update")
                        res = await response.json()
                        write_message_callback(res)

        logger.info(f"{self.client_id}: Stopping")

async def main():
    client = DatastoreClient("http://localhost:8888")
    await client.run()


if __name__ == '__main__':
    asyncio.run(main())