from layout.app import app
from layout.callbacks import *  # noqa

server = app.server

if __name__ == "__main__":
    app.run_server(
        debug=True, use_reloader=True, dev_tools_silence_routes_logging=False
    )
