import picoweb
import network
import logger
import os
import json
import uasyncio
from machine import Pin

class PlaylistManager:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self._lock = uasyncio.Lock()
        self._playlist = []

    async def __aenter__(self):
        await uasyncio.wait_for(self._lock.acquire(), timeout=self.timeout)
        return self._playlist
    
    async def __aexit__(self, *exc):
        self._lock.release()

leds = [Pin(0,Pin.OUT), Pin(1,Pin.OUT), Pin(2,Pin.OUT), Pin(3,Pin.OUT)]

collection = [
    {
        "artist": "Art of Noise",
        "color": "green",
        "side_a": "That's What You Think",
        "side_b": "To The Edit",
    },
    {
        "artist": "Art of Noise",
        "color": "pink",
        "side_a": "Paranoid",
        "side_b": "Peter Gunn",
    },
    {
        "artist": "LCD Soundsystem",
        "color": "blue",
        "side_a": "Us V Them",
        "side_b": "I Can Change",
    },
    {
        "artist": "Missing Persons",
        "color": "green",
        "side_a": "Nobody Walks in LA",
        "side_b": "US Drag",
    },
    {
        "artist": "The Police",
        "color": "pink",
        "side_a": "Synchronicity",
        "side_b": "Synchronicity II",
    },
]

playlist = PlaylistManager()

ap = network.WLAN(network.AP_IF)
ap.config(essid="foobar", password="foobarfoobar")
ap.active(True)

while ap.active() == False:
    pass

print(ap.ifconfig())

app = picoweb.WebApp("AMI Wifi Selector")

# Delete cached templates before loading the directory
# Needed during testing, maybe not for prod
for file in os.listdir("templates"):
    if file[-3:] == ".py":
        print("Deleteing template cache file: %s" % file)
        os.remove("templates/%s" % file)

# Override the template loader in pico, this is because it
# expects the templates to be in its lib directory, dumb
# app.template_loader = utemplate.source.Loader(None, "templates")
app.pkg = None

@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.render_template(resp, "titlestrips.tpl.html", (collection,))

@app.route("/add_song")
def add_song(req, resp):
    if req.method != "POST":
        yield from picoweb.start_response(resp, status="405")
        yield from resp.awrite("405 Method Not Allowed\r\n")
        return

    data = yield from parse_req_json(req)
    song = int(data["song"])
    uasyncio.create_task(add_to_playlist(song))

    yield from picoweb.start_response(resp)
    yield from resp.awrite(json.dumps({"success": "true"}))

async def add_to_playlist(song):
    async with playlist as play:
        play.insert(0,song)

async def apply_playlist():
    while True:
        async with playlist as play:
            if len(play) > 0:
                song = play.pop()
                print(song)
                pos = get_pos_nums(song)
                for p in pos:
                    leds[p].high()
                    await uasyncio.sleep(0.5)
                    leds[p].low()
                    await uasyncio.sleep(0.2)
        await uasyncio.sleep(2)

def parse_req_json(req):
    size = int(req.headers[b"Content-Length"])
    data = yield from req.reader.readexactly(size)
    obj = json.loads(data)
    return obj

def get_pos_nums(num):
    pos_num=[]
    while num != 0:
        pos_num.append(num%10)
        num=num//10
    pos_num.reverse()
    return pos_num

# Send our logger in, ulogger is the default (its dependencies are too large for rpico)
uasyncio.create_task(apply_playlist())
app.run(log=logger, debug=True, host="0.0.0.0", port=80)

