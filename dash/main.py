"""
Dash app launcher

Note:
    Although one could prefer using app within an overriding class, this
    practice is not recommended by a core writer of the Dash user guide.
    cf. @chriddyp: https://community.plotly.com/t/putting-a-dash-instance-inside-a-class/6097
"""
from app import build_callbacks, build_layout, init_app
from data_loader import load_csv
from settings import APP_TITLE, EXT_STYLESHEET, FILTERS, LABELS

data = load_csv()

# Build Dash app
app = init_app(APP_TITLE, EXT_STYLESHEET)
build_layout(app, data, LABELS)
build_callbacks(app, data, FILTERS, LABELS)

app.run_server(debug=True)
