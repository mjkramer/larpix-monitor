import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import yaml

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

        def __call__(self, filename, fh, fig=None):
            global pixel_xy
            tpc_mask = fh['packets']['io_group'] == self.tpc_number
            unixtime = fh['packets'][tpc_mask]['timestamp'][ fh['packets'][tpc_mask]['packet_type'] == 4 ]
            if len(unixtime) == 0:
                return fig if fig is not None else plt.figure()
            livetime = np.clip(max(unixtime) - min(unixtime), 1, np.inf)

            io_channels = np.arange(self.tile_number*4, self.tile_number*4+4)
            tile_mask = tpc_mask & np.isin(fh['packets']['io_channel'], io_channels)
            if not np.any(tile_mask):
                return fig if fig is not None else plt.figure()

            data_mask = fh['packets'][tile_mask]['packet_type'] == 0
            dataword = fh['packets'][tile_mask][data_mask]['dataword']
            chip_id = fh['packets'][tile_mask][data_mask]['chip_id']
            channel_id = fh['packets'][tile_mask][data_mask]['channel_id']
            unique_ids = unique_channel_id(chip_id.astype(int), channel_id.astype(int))
            unique_id_set = np.unique(unique_ids)

            data = dict()
            for unique_id in unique_id_set:
                mask = unique_ids == unique_id
                masked_dataword = dataword[mask]

                data[unique_id] = dict()
                data[unique_id]['mean'] = np.clip(np.mean(masked_dataword),0,256)
                data[unique_id]['std'] = np.clip(np.std(masked_dataword),0,256)
                data[unique_id]['count'] = np.clip(np.sum(mask),0,np.inf)
                data[unique_id]['x'], data[unique_id]['y'] = pixel_xy.get(unique_id,(0,0))

            x = np.array([data[_id]['x'] for _id in unique_id_set])
            y = np.array([data[_id]['y'] for _id in unique_id_set])
            mean = np.array([data[_id]['mean'] for _id in unique_id_set])
            std = np.array([data[_id]['std'] for _id in unique_id_set])
            count = np.array([data[_id]['count'] for _id in unique_id_set])
            mask = (~np.isnan(mean)) | (~np.isnan(std)) | (~np.isnan(count))
            mask = mask & (std != 0) & (count != 0)
            if not np.any(mask):
                return fig if fig is not None else plt.figure()

            x = x[mask]
            y = y[mask]
            mean = mean[mask]
            std = std[mask]
            count = count[mask]

            # always create a new plot
            fig,axes = plt.subplots(3,1,dpi=100,sharex='all',sharey='all',figsize=(6,12))

            c0 = fig.colorbar(axes[0].scatter(x, y, c=mean, marker='.'), ax=axes[0])
            c1 = fig.colorbar(axes[1].scatter(x, y, c=std, marker='.', norm=colors.LogNorm()), ax=axes[1])
            c2 = fig.colorbar(axes[2].scatter(x, y, c=count/livetime, marker='.', norm=colors.LogNorm()), ax=axes[2])

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
