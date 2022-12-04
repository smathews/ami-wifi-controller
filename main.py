import picoweb
import network
import logger
import os
import json

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

playlist = []

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
    playlist.append(data["song"])

    yield from picoweb.start_response(resp)
    yield from resp.awrite(json.dumps({"success": "true", "playlist": playlist}))

def parse_req_json(req):
    size = int(req.headers[b"Content-Length"])
    data = yield from req.reader.readexactly(size)
    obj = json.loads(data)
    return obj

# Send our logger in, ulogger is the default (its dependencies are too large for rpico)
app.run(log=logger, debug=True, host="0.0.0.0", port=80)
