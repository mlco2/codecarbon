def line_chart(data, x, y, text=None):
    if not text:
        text = y

    chart = {
            "data": [
                {
                    "x": data[x],
                    "y": data[y],
                    "type": "lines",
                    "hovertemplate": "%{y:.5f}<extra></extra>",
                },
            ],
            "layout": {
                "title": {
                    "text": text,
                    "x": .05,
                    "xanchor": "left",
                },
                "xaxis": {"fixedrange": True},
                "yaxis": {"fixedrange": True},
                "colorway": ["#17B897"],
            },
        }
    return chart
