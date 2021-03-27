import matplotlib.pyplot as plt
import numpy as np
import datetime

class FIFOFlags(object):
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
        0: 'C0',
        1: 'C1',
        2: 'r'
    }

    def __call__(self, filename, fh, fig=None):
        timestamp_packet_mask = fh['packets']['packet_type'] == 4
        timestamp_idcs = np.argwhere(timestamp_packet_mask).flatten()
        message_groups = np.split(fh['packets']['timestamp'], timestamp_idcs)
        if timestamp_idcs[0] != 0:
            message_groups[0][0] = message_groups[1][0]
        unixtime = np.array([grp[0] for grp in message_groups for _ in range(0,len(grp))])
        unixtimes = np.arange(min(unixtime),max(unixtime)+1)

        packet_type_mask = [fh['packets']['packet_type'] == packet_type for packet_type in range(8)]
        shared_fifo_mask = [fh['packets'][packet_type_mask[0]]['shared_fifo'] == full for full in range(3)]
        local_fifo_mask = [fh['packets'][packet_type_mask[0]]['local_fifo'] == full for full in range(3)]

        packet_count = np.histogram(unixtime[packet_type_mask[0]], bins=unixtimes)[0]
        shared_fifo_count = [np.histogram(unixtime[packet_type_mask[0]][shared_fifo_mask[full]], bins=unixtimes)[0] for full in range(3)]
        local_fifo_count = [np.histogram(unixtime[packet_type_mask[0]][local_fifo_mask[full]], bins=unixtimes)[0] for full in range(3)]

        unixtimes = [datetime.datetime.fromtimestamp(ts) for ts in unixtimes]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()
            for full in range(0,3*2,2):
                ax0_lines[full].set_xdata(np.append(
                    ax0_lines[full].get_xdata(),
                    unixtimes[:-1]
                    ,axis=0))
                ax0_lines[full].set_ydata(np.append(
                    ax0_lines[full].get_ydata(),
                    local_fifo_count[full]
                    ,axis=0))
                ax0_lines[full+1].set_xdata(np.append(
                    ax0_lines[full+1].get_xdata(),
                    unixtimes[:-1]
                    ,axis=0))
                ax0_lines[full+1].set_ydata(np.append(
                    ax0_lines[full+1].get_ydata(),
                    shared_fifo_count[full]
                    ,axis=0))

                ax1_lines[full].set_xdata(np.append(
                    ax1_lines[full].get_xdata(),
                    unixtimes[:-1]
                    ,axis=0))
                ax1_lines[full].set_ydata(np.append(
                    ax1_lines[full].get_ydata(),
                    local_fifo_count[full] / packet_count
                    ,axis=0))
                ax1_lines[full+1].set_xdata(np.append(
                    ax1_lines[full+1].get_xdata(),
                    unixtimes[:-1]
                    ,axis=0))
                ax1_lines[full+1].set_ydata(np.append(
                    ax1_lines[full+1].get_ydata(),
                    shared_fifo_count[full] / packet_count
                    ,axis=0))

        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(2,1,dpi=100,sharex='all',figsize=(10,8))

            for full in range(3):
                axes[0].plot(unixtimes[:-1], shared_fifo_count[full], '.-',
                    alpha=0.5, label=self.shared_fifo_labels[full], color=self.fifo_colors[full])
                axes[0].plot(unixtimes[:-1], local_fifo_count[full], '.--',
                    alpha=0.5, label=self.local_fifo_labels[full], color=self.fifo_colors[full])

                axes[1].plot(unixtimes[:-1], shared_fifo_count[full] / packet_count, '.-',
                    alpha=0.5, label=self.shared_fifo_labels[full], color=self.fifo_colors[full])
                axes[1].plot(unixtimes[:-1], local_fifo_count[full] / packet_count, '.--',
                    alpha=0.5, label=self.local_fifo_labels[full], color=self.fifo_colors[full])

            axes[0].set_ylabel('rate [Hz]')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            axes[1].set_ylabel('fraction')
            axes[1].set_yscale('log')
            axes[1].legend()
            axes[1].grid()

            fig.tight_layout()

        return fig
