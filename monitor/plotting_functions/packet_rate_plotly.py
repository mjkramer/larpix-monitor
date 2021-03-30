import matplotlib.pyplot as plt
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
from pytz import timezone

cols = plotly.colors.DEFAULT_PLOTLY_COLORS

class PacketRatePlotly(object):
    packet_type_labels = {
        0:'data',
        1:'test',
        2:'write',
        3:'read',
        4:'timestamp',
        5:'message',
        6:'sync',
        7:'trigger'
    }
    
    n_files = 0

    def __call__(self, filename, fh, fig=None):
        
        timestamp_packet_mask = fh['packets']['packet_type'] == 4
        timestamp_idcs = np.argwhere(timestamp_packet_mask).flatten()
        message_groups = np.split(fh['packets']['timestamp'], timestamp_idcs)
        if timestamp_idcs[0] != 0:
            message_groups[0][0] = message_groups[1][0]
        unixtime = np.concatenate([np.full(len(grp), grp[0]) for grp in message_groups if len(grp)], axis=0)
        start = min(unixtime)+1
        end = max(unixtime)
        if start >= end: # not more than 1 full second of data
            start = min(unixtime)
            end = max(unixtime)+1
        unixtimes = np.arange(start, end)
        packet_type_mask = [fh['packets']['packet_type'] == packet_type for packet_type in range(8)]
        larpix_packet_mask = packet_type_mask[0] | packet_type_mask[1] | packet_type_mask[2] | packet_type_mask[3]
        parity_error_mask = fh['packets'][larpix_packet_mask]['valid_parity'] == 0

        packet_count = np.histogram(unixtime, bins=unixtimes)[0]
        larpix_packet_count = np.histogram(unixtime[larpix_packet_mask], bins=unixtimes)[0]
        packet_type_count = [np.histogram(unixtime[packet_type_mask[packet_type]], bins=unixtimes)[0] for packet_type in range(8)]
        parity_error_count = np.histogram(unixtime[larpix_packet_mask][parity_error_mask], bins=unixtimes)[0]

        unixtimes = [datetime.datetime.fromtimestamp(ts, timezone('Europe/Zurich')) for ts in unixtimes]

        if fig is None:
            # do stuff to make new plot
            fig = go.Figure()
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
        
        if len(unixtimes[:-2]):
            mean_time = unixtimes[:-2][len(unixtimes[:-2])//2]
            fig.add_scatter(x=[mean_time], y=[np.mean(packet_count[:-1])], mode='lines+markers',
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[np.max(packet_count[:-1])-np.mean(packet_count[:-1])],
                                arrayminus=[np.mean(packet_count[:-1])-np.min(packet_count[:-1])]),
                            name='total', line=dict(width=2, color='black'), row=1, col=1, showlegend=self.n_files==0)

        for packet_type in range(8):
            
            packet_count_type = packet_type_count[packet_type][:-1]
            
            if not len(packet_count_type):
                continue
                
            max_packet_count = np.max(packet_count_type)
            min_packet_count = np.min(packet_count_type)
            mean_packet_count = np.mean(packet_count_type)
            
            packet_count_clip = (packet_type_count[packet_type] / np.clip(packet_count, 1, np.inf))[:-1]
            max_packet_count_clip = np.max(packet_count_clip)
            min_packet_count_clip = np.min(packet_count_clip)
            mean_packet_count_clip = np.mean(packet_count_clip)

            fig.add_scatter(x=[mean_time], y=[mean_packet_count],
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_packet_count-mean_packet_count],
                                arrayminus=[mean_packet_count-min_packet_count]),
                            mode='lines+markers', line=dict(width=2, color=cols[packet_type]),
                            connectgaps=True,
                            name=self.packet_type_labels[packet_type], row=1, col=1, showlegend=self.n_files==0)
            
            fig.add_scatter(x=[mean_time], y=[mean_packet_count_clip],
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_packet_count_clip-mean_packet_count_clip],
                                arrayminus=[mean_packet_count_clip-min_packet_count_clip]),
                            connectgaps=True,
                            mode='lines+markers', line=dict(width=2, color=cols[packet_type]), name=self.packet_type_labels[packet_type], 
                            showlegend=False, row=2, col=1)
            
        larpix_count = (parity_error_count / np.clip(larpix_packet_count, 1, np.inf))[:-1]
        
        if len(larpix_count):
            max_larpix_count = np.max(larpix_count)
            min_larpix_count = np.min(larpix_count)
            mean_larpix_count = np.mean(larpix_count)

            fig.add_scatter(x=[mean_time], y=[mean_larpix_count],
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_larpix_count-mean_larpix_count],
                                arrayminus=[mean_larpix_count-min_larpix_count]), 
                            connectgaps=True,
                            mode='lines+markers', showlegend=self.n_files==0, line=dict(width=2, color='gray'), 
                            name='Parity errors', row=3, col=1)

        fig.update_yaxes(type="log") 
        fig.update_yaxes(title='Rate [Hz]', row=1,col=1)
        fig.update_yaxes(title='Fraction', row=2,col=1)
        fig.update_yaxes(title='Fraction', row=3,col=1)
        fig.update_layout(height=600,width=900,margin=dict(t=20))

        self.n_files+=1

        return fig
