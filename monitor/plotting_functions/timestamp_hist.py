import matplotlib.pyplot as plt
import numpy as np
import datetime

import matplotlib.colors as colors

class TimestampHistograms(object):
    clock_tick = 100e-9 # 100ns

    tpcs = range(1,3)

    sync_plot_range = 10e-6 # 10us
    sync_bins = np.linspace(1.-sync_plot_range,1.+sync_plot_range,int(2*sync_plot_range/clock_tick))

    delay_plot_range = 5e-3 # 5ms
    delay_bins = np.linspace(0,delay_plot_range,200)

    def __call__(self, filename, fh, fig=None):

        sync_packet_mask = (fh['packets']['packet_type'] == 6) & (fh['packets']['trigger_type'] == 83) # synchronization packets
        data_mask = (fh['packets']['packet_type'] == 0) & (fh['packets']['valid_parity'].astype(bool))
        tpc_mask = [fh['packets']['io_group'] == tpc for tpc in self.tpcs]

        data_timestamps = [fh['packets'][data_mask & tpc_mask[i_tpc]]['timestamp'] for i_tpc in range(len(self.tpcs))]
        data_delay = [
            np.clip(
                self.clock_tick * ((fh['packets'][data_mask & tpc_mask[i_tpc]]['receipt_timestamp']) % (2**31) - data_timestamps[i_tpc]),
                self.delay_bins[0], self.delay_bins[-1])
            for i_tpc in range(len(self.tpcs))
            ]
        data_delay_hist = [np.histogram(data_delay[i_tpc], bins=self.delay_bins)[0] for i_tpc in range(len(self.tpcs))]

        sync_timestamps = [
            np.clip(
                self.clock_tick * fh['packets'][sync_packet_mask & tpc_mask[i_tpc]]['timestamp'],
                self.sync_bins[0], self.sync_bins[-1])
            for i_tpc in range(len(self.tpcs))
            ]
        sync_hist = [np.histogram(sync_timestamps[i_tpc], bins=self.sync_bins)[0] for i_tpc in range(len(self.tpcs))]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()

            for i_tpc in range(len(self.tpcs)):
                ax0_lines[i_tpc].set_ydata(ax0_lines[i_tpc].get_ydata() + data_delay_hist[i_tpc])
                ax1_lines[i_tpc].set_ydata(ax1_lines[i_tpc].get_ydata() + sync_hist[i_tpc])

            for ax in axes:
                ax.relim()
                ax.autoscale(tight=True)
            plt.draw()
        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(2,1,dpi=100,figsize=(10,8))

            for i_tpc in range(len(self.tpcs)):
                axes[0].plot(1e3*(self.delay_bins[:-1]+self.delay_bins[1:])/2, data_delay_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))
                axes[1].plot(1e6*((self.sync_bins[:-1]+self.sync_bins[1:])/2 - 1), sync_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))

            axes[1].axvline(0, color='k', linewidth=1)

            axes[0].set_xlabel('hydra network readout delay [ms]')
            axes[0].set_ylabel('count')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            axes[0].autoscale(tight=True)
            axes[1].set_xlabel('clock synchronization [us]')
            axes[1].set_ylabel('count')
            axes[1].set_yscale('log')
            axes[1].legend()
            axes[1].grid()
            axes[1].autoscale(tight=True)

            fig.tight_layout()

        return fig
