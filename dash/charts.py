def build_emission_chart(data):
    chart = {
            "data": [
                {
                    "x": data["timestamp"],
                    "y": data["emissions"],
                    "type": "lines",
                    "hovertemplate": "%{y:.5f}<extra></extra>",
                },
            ],
            "layout": {
                "title": {
                    "text": "Emissions",
                    "x": .05,
                    "xanchor": "left",
                },
                "xaxis": {"fixedrange": True},
                "yaxis": {"fixedrange": True},
                "colorway": ["#17B897"],
            },
        }
    return chart


def build_consumed_chart(data):
    chart = {
        "data": [
            {
                "x": data["timestamp"],
                "y": data["energy_consumed"],
                "type": "lines",
                "hovertemplate": "%{y:.5f}<extra></extra>",            },
        ],
        "layout": {
            "title": {
                "text": "Energy consumed",
                "x": .05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#17B897"],
        },

    }
    return chart
