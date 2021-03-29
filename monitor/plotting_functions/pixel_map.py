import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import yaml
import collections

import matplotlib.colors as colors
import matplotlib as mpl

def unique_channel_id(chip_id, channel_id):
    return chip_id*100 + channel_id

# load pixel geometry once
global pixel_xy
pixel_xy = dict()
geometry_path = os.environ.get('PIXEL_GEOMETRY_PATH','./layout-2.4.0.yaml')
with open(os.path.abspath(os.path.expanduser(geometry_path))) as fi:
    geo = yaml.full_load(fi)
    for chip_id, pixels in geo['chips']:
        for channel,pixel in enumerate(pixels):
            if pixel:
                pixel_xy[unique_channel_id(chip_id, channel)] = (geo['pixels'][pixel][1], geo['pixels'][pixel][2])

def pixel_map_factory(tpc_number, tile_number):
    class PixelMap(object):
        tpc_number = 1
        tile_number = 1

        integration_constant = 0.1

        def __init__(self):
            self.data = collections.defaultdict(dict)

        def update_data(self, array_name, unique_id, new_data):
            if unique_id in self.data and array_name in self.data[unique_id]:
                self.data[unique_id][array_name] = new_data * self.integration_constant + self.data[unique_id][array_name] * (1 - self.integration_constant)
            else:
                self.data[unique_id][array_name] = new_data

        def __call__(self, filename, fh, fig=None):
            # always regerate figure
            if fig is not None:
                plt.figure(fig.number)
                plt.close()

            global pixel_xy
            tpc_mask = fh['packets']['io_group'] == self.tpc_number
            unixtime = fh['packets'][tpc_mask]['timestamp'][ fh['packets'][tpc_mask]['packet_type'] == 4 ]
            if len(unixtime) == 0:
                return plt.figure()
            livetime = np.clip(max(unixtime) - min(unixtime), 1, np.inf)

            io_channels = np.arange((self.tile_number-1)*4+1, (self.tile_number-1)*4+4+1)
            tile_mask = tpc_mask & np.isin(fh['packets']['io_channel'], io_channels)
            if not np.any(tile_mask):
                return plt.figure()

            data_mask = fh['packets'][tile_mask]['packet_type'] == 0
            dataword = fh['packets'][tile_mask][data_mask]['dataword']
            chip_id = fh['packets'][tile_mask][data_mask]['chip_id']
            channel_id = fh['packets'][tile_mask][data_mask]['channel_id']
            unique_ids = unique_channel_id(chip_id.astype(int), channel_id.astype(int))
            unique_id_set = set(list(np.unique(unique_ids)) + list(self.data.keys()))

            for unique_id in unique_id_set:
                mask = unique_ids == unique_id
                n_hits = np.count_nonzero(mask)
                self.update_data('rate', unique_id, n_hits / livetime)
                if n_hits:
                    masked_dataword = dataword[mask]
                    self.update_data('x', unique_id, pixel_xy.get(unique_id,(0,0))[0])
                    self.update_data('y', unique_id, pixel_xy.get(unique_id,(0,0))[1])
                    self.update_data('mean', unique_id, np.mean(masked_dataword))
                    if n_hits > 3:
                        self.update_data('std', unique_id, np.std(masked_dataword))

            x = np.array([self.data[_id].get('x', np.nan) for _id in unique_id_set])
            y = np.array([self.data[_id].get('y', np.nan) for _id in unique_id_set])
            mean = np.array([self.data[_id].get('mean', np.nan) for _id in unique_id_set])
            std = np.array([self.data[_id].get('std', np.nan) for _id in unique_id_set])
            rate = np.array([self.data[_id].get('rate', np.nan) for _id in unique_id_set])
            mask = (np.isfinite(mean)) & (np.isfinite(std)) & (np.isfinite(rate))
            mask = mask & (std != 0) & (rate != 0)
            if not np.any(mask):
                return plt.figure()


            fig,axes = plt.subplots(3,1,dpi=100,sharex='all',sharey='all',figsize=(6,12))

            c0 = fig.colorbar(axes[0].scatter(x[mask], y[mask], c=mean[mask], marker='.'), ax=axes[0])
            c1 = fig.colorbar(axes[1].scatter(x[mask], y[mask], c=std[mask], marker='.', norm=colors.LogNorm()), ax=axes[1])
            c2 = fig.colorbar(axes[2].scatter(x[mask], y[mask], c=rate[mask], marker='.', norm=colors.LogNorm()), ax=axes[2])

            axes[0].set_ylabel('y [mm]')
            axes[1].set_ylabel('y [mm]')
            axes[2].set_ylabel('y [mm]')
            axes[2].set_xlabel('x [mm]')
            c0.set_label('mean ADC')
            c1.set_label('std ADC')
            c2.set_label('rate [Hz]')

            fig.tight_layout()
            return fig

    PixelMap.tpc_number = tpc_number
    PixelMap.tile_number = tile_number
    return PixelMap

# actually generate classes
for tpc in range(1,3):
    for tile in range(1,9):
        globals()['PixelMap_{}_{}'.format(tpc,tile)] = pixel_map_factory(tpc, tile)
