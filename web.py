""" Web server """

from datetime import datetime
from asyncio import set_event_loop_policy
from uvloop import EventLoopPolicy
from mako.template import Template
from sanic import Sanic
from sanic.exceptions import FileNotFound, NotFound
from sanic.response import json, text, html
from config import log, DEBUG, BIND_ADDRESS, HTTP_PORT

app = Sanic(__name__)
layout = Template(filename='views/layout.tpl')

@app.route('/')
async def homepage(req):
    """Main page"""
    return html(layout.render(timestr=datetime.now().strftime("%H:%M:%S.%f")))

@app.route('/test')
async def get_name(req):
    return text("test") 

app.static('/', './static')

if __name__ == '__main__':
    log.debug("Beginning run.")
    #set_event_loop_policy(EventLoopPolicy())
    app.run(host=BIND_ADDRESS, port=HTTP_PORT, debug=DEBUG)
