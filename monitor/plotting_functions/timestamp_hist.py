import matplotlib.pyplot as plt
import numpy as np
import datetime

import matplotlib.colors as colors

class TimestampHistograms(object):
    clock_tick = 100e-9 # 100ns

    tpcs = range(1,3)

    sync_ticks = 1. / clock_tick
    sync_plot_range = 1000 # 100 ticks
    sync_bins = np.linspace(-sync_plot_range, sync_plot_range, 2*sync_plot_range)

    uart_word_len = (64+2)*4 # 64 data + start + stop
    delay_plot_range = uart_word_len * 100 * 2 # max 100 chip depth x 2
    delay_bins = np.linspace(0,delay_plot_range,int(2*delay_plot_range/uart_word_len))
    readout_sync_bins = np.linspace(0,uart_word_len,uart_word_len)

    def __call__(self, filename, fh, fig=None):

        sync_packet_mask = (fh['packets']['packet_type'] == 6) & (fh['packets']['trigger_type'] == 83) # synchronization packets
        data_mask = (fh['packets']['packet_type'] == 0) & (fh['packets']['valid_parity'].astype(bool))
        tpc_mask = [fh['packets']['io_group'] == tpc for tpc in self.tpcs]

        data_timestamps = [
            fh['packets'][data_mask & tpc_mask[i_tpc]]['timestamp'].astype(int)
            for i_tpc in range(len(self.tpcs))
            ]
        data_delay = [
            ((fh['packets'][data_mask & tpc_mask[i_tpc]]['receipt_timestamp']) % (2**31)).astype(int) - data_timestamps[i_tpc]
            for i_tpc in range(len(self.tpcs))
            ]
        data_sync = [
            np.fmod(data_delay[i_tpc], self.uart_word_len)
            for i_tpc in range(len(self.tpcs))
        ]
        data_delay_hist = [
            np.histogram(
                np.clip(data_delay[i_tpc], self.delay_bins[0], self.delay_bins[-1]), bins=self.delay_bins)[0]
            for i_tpc in range(len(self.tpcs))
            ]
        data_sync_hist = [
            np.histogram(
                np.clip(data_sync[i_tpc], self.readout_sync_bins[0], self.readout_sync_bins[-1]), bins=self.readout_sync_bins)[0]
            for i_tpc in range(len(self.tpcs))
            ]

        sync_timestamps = [
            fh['packets'][sync_packet_mask & tpc_mask[i_tpc]]['timestamp'].astype(int) - self.sync_ticks
            for i_tpc in range(len(self.tpcs))
            ]
        sync_hist = [
            np.histogram(
                np.clip(sync_timestamps[i_tpc], self.sync_bins[0], self.sync_bins[-1]), bins=self.sync_bins)[0]
            for i_tpc in range(len(self.tpcs))
            ]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()
            ax2_lines = axes[2].get_lines()

            for i_tpc in range(len(self.tpcs)):
                ax0_lines[i_tpc].set_ydata(ax0_lines[i_tpc].get_ydata() + sync_hist[i_tpc])
                ax1_lines[i_tpc].set_ydata(ax1_lines[i_tpc].get_ydata() + data_delay_hist[i_tpc])
                ax2_lines[i_tpc].set_ydata(ax2_lines[i_tpc].get_ydata() + data_sync_hist[i_tpc])

            for ax in axes:
                ax.relim()
                ax.autoscale(axis='x', tight=True)
                ax.autoscale(axis='y', tight=False)
            plt.draw()
        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(3,1,dpi=100,figsize=(10,12))

            for i_tpc in range(len(self.tpcs)):
                axes[0].plot((self.sync_bins[:-1]+self.sync_bins[1:])/2, sync_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))
                axes[1].plot((self.delay_bins[:-1]+self.delay_bins[1:])/2, data_delay_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))
                axes[2].plot((self.readout_sync_bins[:-1]+self.readout_sync_bins[1:])/2, data_sync_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))

            axes[0].axvline(0, color='k', linewidth=1)
            axes[0].set_xlabel('clock synchronization [0.1us]')
            axes[0].set_ylabel('count')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            axes[0].autoscale(axis='x', tight=True)
            axes[1].set_xlabel('Hydra network delay [0.1us]')
            axes[1].set_ylabel('count')
            axes[1].set_yscale('log')
            axes[1].legend()
            axes[1].grid()
            axes[1].autoscale(axis='x', tight=True)
            axes[2].set_xlabel('UART synchronization [0.1us]')
            axes[2].set_ylabel('count')
            axes[2].set_yscale('log')
            axes[2].legend()
            axes[2].grid()
            axes[2].autoscale(axis='x', tight=True)

            fig.tight_layout()

        return fig
