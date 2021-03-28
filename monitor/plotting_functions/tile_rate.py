import matplotlib.pyplot as plt
import numpy as np
import datetime

import matplotlib.colors as colors

class TileRate(object):
    tile_numbers = ['{}-{}'.format(tpc, tile) for tpc in range(1,3) for tile in range(1,9)]
    io_channels = [np.arange(tile*4,tile*4+4) + tpc*100 for tpc in range(1,3) for tile in range(1,9)]

    tile_colors = plt.get_cmap('hsv')

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

        unixtimes = [datetime.datetime.fromtimestamp(ts) for ts in unixtimes]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()

            for i_tile in range(len(self.tile_numbers)):
                if i_tile < len(self.tile_numbers)//2:
                    ax0_lines[i_tile].set_xdata(np.append(
                        ax0_lines[i_tile].get_xdata(),
                        unixtimes[:-2]
                        , axis=0))
                    ax0_lines[i_tile].set_ydata(np.append(
                        ax0_lines[i_tile].get_ydata(),
                        tile_packet_count[i_tile][:-1]
                        , axis=0))
                else:
                    ax1_lines[i_tile%(len(self.tile_numbers)//2)].set_xdata(np.append(
                        ax1_lines[i_tile%(len(self.tile_numbers)//2)].get_xdata(),
                        unixtimes[:-2]
                        , axis=0))
                    ax1_lines[i_tile%(len(self.tile_numbers)//2)].set_ydata(np.append(
                        ax1_lines[i_tile%(len(self.tile_numbers)//2)].get_ydata(),
                        tile_packet_count[i_tile][:-1]
                        , axis=0))

                # ax1_lines[i_tile*3].set_xdata(np.append(
                #     ax1_lines[i_tile*3].get_xdata(),
                #     unixtimes[:-1]
                #     , axis=0))
                # ax1_lines[i_tile*3].set_ydata(np.append(
                #     ax1_lines[i_tile*3].get_ydata(),
                #     tile_shared_fifo_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf)
                #     , axis=0))
                # ax1_lines[i_tile*3+1].set_xdata(np.append(
                #     ax1_lines[i_tile*3+1].get_xdata(),
                #     unixtimes[:-1]
                #     , axis=0))
                # ax1_lines[i_tile*3+1].set_ydata(np.append(
                #     ax1_lines[i_tile*3+1].get_ydata(),
                #     tile_local_fifo_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf)
                #     , axis=0))
                # ax1_lines[i_tile*3+2].set_xdata(np.append(
                #     ax1_lines[i_tile*3+2].get_xdata(),
                #     unixtimes[:-1]
                #     , axis=0))
                # ax1_lines[i_tile*3+2].set_ydata(np.append(
                #     ax1_lines[i_tile*3+2].get_ydata(),
                #     tile_parity_error_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf)
                #     , axis=0))

            for ax in axes:
                ax.relim()
                ax.autoscale()
            plt.draw()
        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(2,1,dpi=100,sharex='all',figsize=(10,8))

            for i_tile in range(len(self.tile_numbers)):
                color = 'C{}'.format(i_tile%(len(self.tile_numbers)//2))
                if i_tile < len(self.tile_numbers)//2:
                    axes[0].plot(unixtimes[:-2], tile_packet_count[i_tile][:-1], '.-',
                        alpha=0.5, label='tile {}'.format(self.tile_numbers[i_tile]),
                        color=color)
                else:
                    axes[1].plot(unixtimes[:-2], tile_packet_count[i_tile][:-1], '.-',
                        alpha=0.5, label='tile {}'.format(self.tile_numbers[i_tile]),
                        color=color)

                # axes[1].plot(unixtimes[:-1], tile_shared_fifo_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf), '.-',
                #     alpha=0.5, color=self.tile_colors(i_tile/len(self.tile_numbers)))
                # axes[1].plot(unixtimes[:-1], tile_local_fifo_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf), '.--',
                #     alpha=0.5, color=self.tile_colors(i_tile/len(self.tile_numbers)))
                # axes[1].plot(unixtimes[:-1], tile_parity_error_count[i_tile] / np.clip(tile_packet_count[i_tile],1,np.inf), '.-.',
                #     alpha=0.5, color=self.tile_colors(i_tile/len(self.tile_numbers)))

            axes[0].set_ylabel('trigger rate [Hz]')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            # axes[1].set_ylabel('fraction')
            axes[1].set_ylabel('trigger rate [Hz]')
            axes[1].set_yscale('log')
            axes[1].legend()
            # axes[1].legend(['shared fifo >50%','local fifo >50%','parity errors'])
            axes[1].grid()

            fig.tight_layout()

        return fig
