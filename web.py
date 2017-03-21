""" Web server """

from datetime import datetime
from asyncio import set_event_loop_policy
from uvloop import EventLoopPolicy
from mako.template import Template
from sanic import Sanic
from sanic.exceptions import FileNotFound, NotFound
from sanic.response import json, text, html
from multiprocessing import cpu_count
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

log.debug("Beginning run.")
app.run(host=BIND_ADDRESS, port=HTTP_PORT, workers=cpu_count(), debug=DEBUG)
