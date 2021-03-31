import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
from pytz import timezone

cols = plotly.colors.DEFAULT_PLOTLY_COLORS

class TileRatePlotly(object):
    tile_numbers = ['{}-{}'.format(tpc, tile) for tpc in range(1,3) for tile in range(1,9)]
    io_channels = [np.arange((tile-1)*4+1, (tile-1)*4+1+4) + tpc*100 for tpc in range(1,3) for tile in range(1,9)]
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

        tile_mask = [np.isin(fh['packets']['io_channel'].astype(int) + fh['packets']['io_group'].astype(int)*100, self.io_channels[i_tile]) for i_tile in range(len(self.tile_numbers))]
        data_mask = fh['packets']['packet_type'] == 0 # data packets
        shared_fifo_mask = fh['packets'][data_mask]['shared_fifo'] > 0
        local_fifo_mask = fh['packets'][data_mask]['local_fifo'] > 0
        parity_error_mask = fh['packets'][data_mask]['valid_parity'] == 0

        tile_packet_count = [np.histogram(unixtime[tile_mask[i_tile] & data_mask], bins=unixtimes)[0] for i_tile in range(len(self.tile_numbers))]
        # tile_shared_fifo_count = [np.histogram(unixtime[data_mask][tile_mask[i_tile][data_mask] & shared_fifo_mask], bins=unixtimes)[0] for i_tile in range(len(self.tile_numbers))]
        # tile_local_fifo_count = [np.histogram(unixtime[data_mask][tile_mask[i_tile][data_mask] & local_fifo_mask], bins=unixtimes)[0] for i_tile in range(len(self.tile_numbers))]
        # tile_parity_error_count = [np.histogram(unixtime[data_mask][tile_mask[i_tile][data_mask] & parity_error_mask], bins=unixtimes)[0] for i_tile in range(len(self.tile_numbers))]

        unixtimes = [datetime.datetime.fromtimestamp(ts, timezone('Europe/Zurich')) for ts in unixtimes]

        if fig is None:
            fig = go.Figure()
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("TPC 1", "TPC 2"))

        if not len(unixtimes[:-2]):
            return fig
            
        for i_tile in range(len(self.tile_numbers)):
            color = 'C{}'.format(i_tile%(len(self.tile_numbers)//2))
            
            if not len(tile_packet_count[i_tile][:-1]):
                continue
            
            mean_tile_count = np.mean(tile_packet_count[i_tile][:-1])
            max_tile_count = np.max(tile_packet_count[i_tile][:-1])
            min_tile_count = np.min(tile_packet_count[i_tile][:-1])
            mean_time = unixtimes[:-2][len(unixtimes[:-2])//2]
            
            if i_tile < len(self.tile_numbers)//2:
                fig.add_scatter(x=[mean_time], y=[mean_tile_count], name='tile {}'.format(self.tile_numbers[i_tile]),
                                error_y=dict(
                                    type='data',
                                    symmetric=False,
                                    array=[max_tile_count-mean_tile_count],
                                    arrayminus=[mean_tile_count-min_tile_count]),
                                row=1, col=1, showlegend=self.n_files==0, 
                                mode='lines+markers',
                                line=dict(width=2, color=cols[i_tile%(len(self.tile_numbers)//2)]))
            else:
                fig.add_scatter(x=[mean_time], y=[mean_tile_count], name='tile {}'.format(self.tile_numbers[i_tile]),
                                error_y=dict(
                                    type='data',
                                    symmetric=False,
                                    array=[max_tile_count-mean_tile_count],
                                    arrayminus=[mean_tile_count-min_tile_count]),
                                row=2, col=1, showlegend=self.n_files==0, 
                                mode='lines+markers',
                                line=dict(width=2, color=cols[i_tile%(len(self.tile_numbers)//2)]))

        fig.update_xaxes(range=[mean_time-datetime.timedelta(hours=25),
                                mean_time+datetime.timedelta(hours=1)])

        fig.update_layout(height=600,width=900,margin=dict(t=20))
        fig.update_yaxes(type="log") 
        fig.update_yaxes(title='trigger rate [Hz]')

        self.n_files+=1

#             axes[0].set_ylabel('trigger rate [Hz]')
#             axes[0].set_yscale('log')
#             axes[0].legend()
#             axes[0].grid()
#             # axes[1].set_ylabel('fraction')
#             axes[1].set_ylabel('trigger rate [Hz]')
#             axes[1].set_yscale('log')
#             axes[1].legend()
#             # axes[1].legend(['shared fifo >50%','local fifo >50%','parity errors'])
#             axes[1].grid()

#             fig.tight_layout()

        return fig
