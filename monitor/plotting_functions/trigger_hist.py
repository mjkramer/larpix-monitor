import matplotlib.pyplot as plt
import numpy as np
import datetime

import matplotlib.colors as colors

class TriggerHistograms(object):
    clock_tick = 100e-9 # 100ns

    tpcs = range(1,3)

    sync_ticks = 1. / clock_tick
    sync_plot_range = 1000 # 100 ticks
    sync_bins = np.linspace(-sync_plot_range, sync_plot_range, 2*sync_plot_range)

    drift_len = int(300e-3 / (1.65e-3/1e-6) / clock_tick) #  30cm / (1.65mm/us) / tick
    trigger_bins = np.linspace(-2*drift_len, 4*drift_len, 6*drift_len//10) # 10 tick bins

    def __call__(self, filename, fh, fig=None):
        # get data from each tpc
        tpc_mask = [fh['packets']['io_group'] == tpc for tpc in self.tpcs]
        # find external triggers
        trigger_packet_mask = [
            tpc_mask[i_tpc] & (fh['packets']['packet_type'] == 7) & (fh['packets']['trigger_type'] == 2)
            for i_tpc in range(len(self.tpcs))
            ]
        # split data at external triggers
        trigger_grps = [
            np.split(fh['packets'][tpc_mask[i_tpc]], np.argwhere(trigger_packet_mask[i_tpc][tpc_mask[i_tpc]]).flatten())
            for i_tpc in range(len(self.tpcs))
            ]
        if not any([len(grp) for tpc_grps in trigger_grps for grp in tpc_grps]):
            return plt.figure() if fig is None else  fig
        # get data timestamp offsets relative to trigger
        rel_timestamps = [[
                grp[1:][ (grp[1:]['packet_type']==0) & (grp[1:]['valid_parity'].astype(bool)) ]['timestamp'].astype(int) - grp[0]['timestamp'].astype(int)
                for grp in trigger_grps[i_tpc]
                if len(grp) > 1 and np.any((grp[1:]['packet_type']==0) & (grp[1:]['valid_parity'].astype(bool)))
                ]
            for i_tpc in range(len(self.tpcs))
            ]
        rel_timestamps = [np.concatenate(ts, axis=0) if len(ts) else np.empty(0,) for ts in rel_timestamps]
        # get timestamp offsets relative to other triggers
        trigger_dt = np.diff(
            fh['packets'][np.logical_or(*trigger_packet_mask)]['timestamp'].astype(int)
            )

        trigger_corr_hist = [
            np.histogram(
                np.clip(rel_timestamps[i_tpc], self.trigger_bins[0], self.trigger_bins[-1]), bins=self.trigger_bins)[0]
            for i_tpc in range(len(self.tpcs))
            ]
        trigger_sync_hist = np.histogram(np.clip(trigger_dt, self.sync_bins[0], self.sync_bins[-1]), bins=self.sync_bins)[0]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()

            for i_tpc in range(len(self.tpcs)):
                ax0_lines[i_tpc].set_ydata(ax0_lines[i_tpc].get_ydata() + trigger_corr_hist[i_tpc])
            ax1_lines[0].set_ydata(ax1_lines[0].get_ydata() + trigger_sync_hist)

            for ax in axes:
                ax.relim()
                ax.autoscale(axis='x', tight=True)
                ax.autoscale(axis='y', tight=False)
            plt.draw()
        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(2,1,dpi=100,figsize=(10,8))

            for i_tpc in range(len(self.tpcs)):
                axes[0].plot((self.trigger_bins[:-1]+self.trigger_bins[1:])/2, trigger_corr_hist[i_tpc], '.-',
                    alpha=0.5, label='tpc {}'.format(self.tpcs[i_tpc]))
            axes[1].plot((self.sync_bins[:-1]+self.sync_bins[1:])/2, trigger_sync_hist, '.-',
                alpha=0.5)

            axes[0].axvline(0, color='k', linewidth=1)
            axes[0].set_xlabel('timestamp relative to external trigger [0.1us]')
            axes[0].set_ylabel('count')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            axes[0].autoscale(axis='x', tight=True)

            axes[1].axvline(0, color='k', linewidth=1)
            axes[1].set_xlabel(r'external trigger $\Delta t$ [0.1us]')
            axes[1].set_ylabel('count')
            axes[1].set_yscale('log')
            axes[1].grid()
            axes[1].autoscale(axis='x', tight=True)

            fig.tight_layout()

        return fig
