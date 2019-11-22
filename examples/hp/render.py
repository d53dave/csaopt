import plotly
import plotly.graph_objs as go
import networkx as nx
import math
import multiprocessing

from typing import List, Tuple

Chain = List[List[int]]


def render_plotly(chain: Chain, contacts: List[Tuple[int, int]], filename='') -> None:
    hp_len = len(chain)
    scale_factor = max(8, hp_len / 4)

    contact_edges = []
    for contact in contacts:
        print('Processing contact')
        coord1 = chain[contact[0]]
        coord2 = chain[contact[1]]
        contact_edges.append(
            go.Scatter(
                hoverinfo='none',
                x=[coord1[1], coord2[1]],
                y=[coord1[2], coord2[2]],
                line=dict(width=8, color='rgb(183,183,183,0.3)', dash='dot'),
            ))

    Xbe = [coord[1] for coord in chain]
    Ybe = [coord[2] for coord in chain]
    backbone_edges = go.Scatter(
        hoverinfo='none',
        x=Xbe,
        y=Ybe,
        line=dict(width=2 * scale_factor, color='black'),
    )

    Xn = [coord[1] for coord in chain]
    Yn = [coord[2] for coord in chain]
    # for idx, coord in enumerate(coords):
    # print('coord[{}][1] + coord[{}][2] = {}', idx, idx, coord[idx][1] + coord[idx][2])
    print(Xn)
    print(Yn)
    node_trace = go.Scatter(
        hoverinfo='none',
        x=Xn,
        y=Yn,
        text=['<b>{}</b>'.format(i) for i in range(len(chain))],
        textposition='middle center',
        textfont=dict(size=2 * scale_factor, color='rgb(160,160,160)'),
        line={},
        mode='markers+text',
        marker=dict(
            showscale=False,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            # colorscale='Blackbody',
            reversescale=True,
            color=[],
            line=dict(width=scale_factor, color='black'),
            size=8 * scale_factor,
        ))

    node_trace['marker']['color'] = list(map(lambda c: 'white' if c[0] == 1 else 'rgb(70,70,70)', chain))

    fig = go.Figure(
        data=[
            backbone_edges,
            *contact_edges,
            node_trace,
        ],
        layout=go.Layout(
            autosize=False,
            width=1000,
            height=1000,
            showlegend=False,
            xaxis=dict(showgrid=True, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=True, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1)))

    try:
        current_proc = multiprocessing.current_process()
        if filename == '':
            filename = 'hp_plot_' + str(current_proc.pid)
    except Exception:
        pass
    plotly.offline.plot(fig, filename=filename + '.html')
