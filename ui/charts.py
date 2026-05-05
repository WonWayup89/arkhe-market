import plotly.graph_objects as go

def arkhe_market_line_chart(values, title=""):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=list(values),
            mode="lines",
            line=dict(color="#FFB000", width=3),
            fill=None,
        )
    )
    fig.update_layout(
        title=title,
        plot_bgcolor="#141B24",
        paper_bgcolor="#141B24",
        font=dict(color="#E6EDF3"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False),
        title_font=dict(color="#FFC83D", size=18),
    )
    return fig
