import matplotlib.pyplot as plt
import numpy as np
import datetime

class PacketRate(object):
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

    def __call__(self, filename, fh, fig=None):
        timestamp_packet_mask = fh['packets']['packet_type'] == 4
        timestamp_idcs = np.argwhere(timestamp_packet_mask).flatten()
        message_groups = np.split(fh['packets']['timestamp'], timestamp_idcs)
        if timestamp_idcs[0] != 0:
            message_groups[0][0] = message_groups[1][0]
        unixtime = np.array([grp[0] for grp in message_groups for _ in range(0,len(grp))])
        unixtimes = np.arange(min(unixtime), max(unixtime) + 1)

        packet_type_mask = [fh['packets']['packet_type'] == packet_type for packet_type in range(8)]
        larpix_packet_mask = packet_type_mask[0] | packet_type_mask[1] | packet_type_mask[2] | packet_type_mask[3]
        parity_error_mask = fh['packets'][larpix_packet_mask]['valid_parity'] == 0

        packet_count = np.histogram(unixtime, bins=unixtimes)[0]
        larpix_packet_count = np.histogram(unixtime[larpix_packet_mask], bins=unixtimes)[0]
        packet_type_count = [np.histogram(unixtime[packet_type_mask[packet_type]], bins=unixtimes)[0] for packet_type in range(8)]
        parity_error_count = np.histogram(unixtime[larpix_packet_mask][parity_error_mask], bins=unixtimes)[0]

        unixtimes = [datetime.datetime.fromtimestamp(ts) for ts in unixtimes]

        if fig is not None:
            # do stuff to update plot
            axes = fig.get_axes()

            ax0_lines = axes[0].get_lines()
            ax1_lines = axes[1].get_lines()
            ax2_lines = axes[2].get_lines()

            ax0_lines[0].set_xdata(np.append(
                ax0_lines[0].get_xdata(),
                unixtimes[:-1]
                , axis=0))
            ax0_lines[0].set_ydata(np.append(
                ax0_lines[0].get_ydata(),
                packet_count
                , axis=0))
            for packet_type in range(1,9):
                ax0_lines[packet_type].set_xdata(np.append(
                    ax0_lines[packet_type].get_xdata(),
                    unixtimes[:-1]
                    , axis=0))
                ax0_lines[packet_type].set_ydata(np.append(
                    ax0_lines[packet_type].get_ydata(),
                    packet_type_count[packet_type]
                    , axis=0))

                ax1_lines[packet_type-1].set_xdata(np.append(
                    ax1_lines[packet_type-1].get_xdata(),
                    unixtimes[:-1]
                    , axis=0))
                ax1_lines[packet_type-1].set_ydata(np.append(
                    ax1_lines[packet_type-1].get_ydata(),
                    packet_type_count[packet_type-1] / np.clip(packet_count, 1, np.inf)
                    , axis=0))

            ax2_lines[0].set_xdata(np.append(
                    ax1_lines[0].get_xdata(),
                    unixtimes[:-1]
                    , axis=0))
            ax2_lines[0].set_ydata(np.append(
                ax1_lines[0].get_ydata(),
                parity_error_count / np.clip(larpix_packet_count, 1, np.inf)
                , axis=0))
        else:
            # do stuff to make new plot
            fig,axes = plt.subplots(3,1,dpi=100,sharex='all',figsize=(10,12))

            axes[0].plot(unixtimes[:-1], packet_count,
                alpha=0.5, label='total', color='k', zorder=np.inf)
            for packet_type in range(8):
                axes[0].plot(unixtimes[:-1], packet_type_count[packet_type], '.-',
                    alpha=0.5, label=self.packet_type_labels[packet_type])

                axes[1].plot(unixtimes[:-1], packet_type_count[packet_type] / np.clip(packet_count, 1, np.inf), '.-',
                    alpha=0.5, label=self.packet_type_labels[packet_type])

            axes[2].plot(unixtimes[:-1], parity_error_count / np.clip(larpix_packet_count, 1, np.inf), '.-',
                    alpha=0.5, label='parity errors')

            axes[0].set_ylabel('rate [Hz]')
            axes[0].set_yscale('log')
            axes[0].legend()
            axes[0].grid()
            axes[1].set_ylabel('fraction')
            axes[1].set_yscale('log')
            axes[1].legend()
            axes[1].grid()
            axes[2].set_ylabel('fraction')
            axes[2].set_yscale('log')
            axes[2].legend()
            axes[2].grid()

            fig.tight_layout()

        return fig
