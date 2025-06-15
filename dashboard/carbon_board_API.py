from layout.app import app, serve_layout
from layout.callbacks import *  # noqa

server = app.server
app.layout = serve_layout

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, dev_tools_silence_routes_logging=False)
