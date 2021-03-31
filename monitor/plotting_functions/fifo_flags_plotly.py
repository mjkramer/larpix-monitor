import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
from pytz import timezone

class FIFOFlagsPlotly(object):
    local_fifo_labels = {
        0:'local fifo 0%',
        1:'local fifo >50%',
        2:'local fifo 100%'
    }
    shared_fifo_labels = {
        0:'shared fifo 0%',
        1:'shared fifo >50%',
        2:'shared fifo 100%'
    }
    fifo_colors = {
        0: 'blue',
        1: 'orange',
        2: 'red'
    }
    n_files = 0
    def __call__(self, filename, fh, fig=None):
        timestamp_packet_mask = fh['packets']['packet_type'] == 4
        timestamp_idcs = np.argwhere(timestamp_packet_mask).flatten()
        message_groups = np.split(fh['packets']['timestamp'], timestamp_idcs)
        if timestamp_idcs[0] != 0:
            message_groups[0][0] = message_groups[1][0]
        unixtime = np.array([grp[0] for grp in message_groups for _ in range(0,len(grp))])
        start = min(unixtime)+1
        end = max(unixtime)
        if start >= end: # not more than 1 full second of data
            start = min(unixtime)
            end = max(unixtime)+1
        unixtimes = np.arange(start, end)

        packet_type_mask = [fh['packets']['packet_type'] == packet_type for packet_type in range(8)]
        shared_fifo_mask = [fh['packets'][packet_type_mask[0]]['shared_fifo'] == full for full in range(3)]
        local_fifo_mask = [fh['packets'][packet_type_mask[0]]['local_fifo'] == full for full in range(3)]

        packet_count = np.histogram(unixtime[packet_type_mask[0]], bins=unixtimes)[0]
        shared_fifo_count = [np.histogram(unixtime[packet_type_mask[0]][shared_fifo_mask[full]], bins=unixtimes)[0] for full in range(3)]
        local_fifo_count = [np.histogram(unixtime[packet_type_mask[0]][local_fifo_mask[full]], bins=unixtimes)[0] for full in range(3)]

        unixtimes = [datetime.datetime.fromtimestamp(ts, timezone('Europe/Zurich')) for ts in unixtimes]

        if fig is None:
            fig = go.Figure()
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        
        if not len(unixtimes[:-2]):
            return fig
        
        mean_time = unixtimes[:-2][len(unixtimes[:-2])//2]
    
        for full in range(3):
            
            if not len(shared_fifo_count[full][:-1]) or not len(local_fifo_count[full][:-1]):
                continue

            mean_shared_fifo_count = np.mean(shared_fifo_count[full][:-1])
            min_shared_fifo_count = np.min(shared_fifo_count[full][:-1])
            max_shared_fifo_count = np.max(shared_fifo_count[full][:-1])

            mean_local_fifo_count = np.mean(local_fifo_count[full][:-1])
            min_local_fifo_count = np.min(local_fifo_count[full][:-1])
            max_local_fifo_count = np.max(local_fifo_count[full][:-1])
            
            fig.add_scatter(x=[mean_time], 
                            y=[mean_shared_fifo_count], 
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_shared_fifo_count-mean_shared_fifo_count],
                                arrayminus=[mean_shared_fifo_count-min_shared_fifo_count]),
                            name=self.shared_fifo_labels[full], showlegend=self.n_files==0,
                            row=1,col=1,line=dict(width=2, color=self.fifo_colors[full]))
            
            fig.add_scatter(x=[mean_time], 
                            y=[mean_local_fifo_count], 
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_local_fifo_count-mean_local_fifo_count],
                                arrayminus=[mean_local_fifo_count-min_local_fifo_count]),
                            name=self.local_fifo_labels[full], showlegend=self.n_files==0,
                            row=1,col=1,line=dict(width=2, dash='dash', color=self.fifo_colors[full]))
            
            mean_shared_ratio_fifo_count = np.mean((shared_fifo_count[full] / packet_count)[:-1])
            min_shared_ratio_fifo_count = np.min((shared_fifo_count[full] / packet_count)[:-1])
            max_shared_ratio_fifo_count = np.max((shared_fifo_count[full] / packet_count)[:-1])

            mean_local_ratio_fifo_count = np.mean((local_fifo_count[full] / packet_count)[:-1])
            min_local_ratio_fifo_count = np.min((local_fifo_count[full] / packet_count)[:-1])
            max_local_ratio_fifo_count = np.max((local_fifo_count[full] / packet_count)[:-1])

            fig.add_scatter(x=[mean_time], 
                            y=[mean_shared_ratio_fifo_count],
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_shared_ratio_fifo_count-mean_shared_ratio_fifo_count],
                                arrayminus=[mean_shared_ratio_fifo_count-min_shared_ratio_fifo_count]),
                            name=self.shared_fifo_labels[full], showlegend=False,
                            row=2,col=1,line=dict(width=2, color=self.fifo_colors[full]))

            fig.add_scatter(x=[mean_time], 
                            y=[mean_local_ratio_fifo_count], 
                            error_y=dict(
                                type='data',
                                symmetric=False,
                                array=[max_local_ratio_fifo_count-mean_local_ratio_fifo_count],
                                arrayminus=[mean_local_ratio_fifo_count-min_local_ratio_fifo_count]),
                            name=self.local_fifo_labels[full], showlegend=False,
                            row=2,col=1,line=dict(width=2, dash='dash', color=self.fifo_colors[full]))
            
            fig.update_xaxes(range=[mean_time-datetime.timedelta(hours=25),
                                    mean_time+datetime.timedelta(hours=1)])

            fig.update_layout(height=600,width=900,margin=dict(t=20))
            fig.update_yaxes(type="log") 
            fig.update_yaxes(title='rate [Hz]', row=1, col=1)
            fig.update_yaxes(title='fraction', row=2, col=1)

        self.n_files += 1

        return fig
