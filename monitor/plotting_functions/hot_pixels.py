import matplotlib.pyplot as plt
import numpy as np

class HotPixelPlot(object):
    def __call__(self, filename, fh, fig=None):
        if fig is not None:
            plt.figure(fig.number)
            plt.close()
            fig = None
            
        # do stuff to make new plot
        fig = plt.figure(dpi=100, figsize=(6,18))

        mask = fh['packets']['packet_type'] == 0

        key, counts = np.unique(fh['packets'][mask][['io_group', 'io_channel', 'chip_id', 'channel_id']], return_counts=True)
        total = np.sum(counts)
        sorting = np.argsort(counts)[-100:]
        key = key[sorting]
        counts = counts[sorting]

        labels = [f'{int(d["io_group"])}-{d["io_channel"]}-{d["chip_id"]}-{d["channel_id"]}'
                  for d in key]
        
        plt.barh(np.arange(len(counts)), counts/np.clip(total,1,None),
                tick_label=labels)
        plt.xlabel('fraction of data packets')
        plt.xscale('log')
        plt.tight_layout()
        
        return fig
