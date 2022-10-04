import plotly.graph_objects as go
import plotly.io as pio

darkgreen = "#024758"
vividgreen = "#c9fb37"
color3 = "#226a7a"
titleColor = "#d8d8d8"

pio.templates["CodeCarbonTemplate"] = go.layout.Template(
    # layout
    # ------------------------------------------------------------------
    layout={
        "font": {"color": "white"},
        "paper_bgcolor": "#024758",
        "plot_bgcolor": "#024758",
        "title": {
            "font": {"family": "Verdana, Geneva, Sans-serif", "color": "#d8d8d8"}
        },
        "colorway": [
            "#c9fb37",
            "#36c9fb",
            "#fb36c9",
            "#fb6836",
            "#6836fb",
            "#cb36fb",
            "#67fb36",
        ],
    },
    data={
        "pie": [
            go.Pie(
                marker={"colors": ["#c9fb37", "#226a7a"]},
                title_position="bottom center",
                textinfo="none",
                hole=0.8,
                hoverinfo="skip",
                showlegend=False,
            )
        ],
    },
)
