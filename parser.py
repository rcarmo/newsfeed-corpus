""" Feed parser """

from asyncio import get_event_loop, set_event_loop_policy
from aiozmq.rpc import AttrHandler, serve_pipeline, method
from uvloop import EventLoopPolicy
from config import ITEM_SOCKET, log

class NotificationHandler(AttrHandler):

    @method
    def parse(self, arg):
        log.info("Received %s", arg)


async def server():
    log.info("Server starting")
    listener = await serve_pipeline(NotificationHandler(), bind=ITEM_SOCKET)
    await listener.wait_closed()


def main():
    set_event_loop_policy(EventLoopPolicy())
    loop = get_event_loop()
    loop.run_until_complete(server())

if __name__ == '__main__':
    main()
