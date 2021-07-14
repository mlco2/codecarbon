"""
Dash app launcher

Note:
    Although one could prefer using app within an overriding class, this
    practice is not recommended by a core writer of the Dash user guide.
    cf. @chriddyp: https://community.plotly.com/t/putting-a-dash-instance-inside-a-class/6097
"""
from settings import APP_TITLE, EXT_STYLESHEET
from settings import LABELS, FILTERS
from data_loader import load_data
from app import init_app, build_layout, build_callbacks

data = load_data()

# Build Dash app
app = init_app(APP_TITLE, EXT_STYLESHEET)
build_layout(app, data, LABELS)
build_callbacks(app, data, FILTERS, LABELS)

app.run_server(debug=True)
