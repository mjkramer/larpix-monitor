import time
from collections import defaultdict
import os
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('agg')

from . import plotting_functions

class Plotter(object):
    def __init__(self, plots, clean_up_interval):
        self.plots = plots
        self.clean_up_interval = clean_up_interval

        self._last_updated = dict()

        # look up available plot functions
        self._plotters = dict([
            (plot_name, getattr(plotting_functions, plot_name)())
            for plot_name in self.plots
            if hasattr(plotting_functions, plot_name)
            ])
        self._figs = defaultdict(dict)

    def __call__(self, datafile_fh):
        rv = list()
        for datafile, fh in datafile_fh:
            rd = dict()
            for plot in self.plots:
                if len(fh['packets']) == 0: continue
                fig_name = self._format_fig_name(datafile, plot)
                self._figs[datafile][plot] = self._plotters[plot](
                    datafile,
                    fh,
                    self._figs[datafile].get(plot, None)
                    )
                rd[fig_name] = self._figs[datafile][plot]

            rv.append(rd)
            self._last_updated[datafile] = time.time()

        self._clean_up()

        return rv

    def _format_fig_name(self, datafile, plot_name):
        return '{}_{}'.format(os.path.basename(datafile[:-3]), plot_name)

    def _clean_up(self):
        to_clean = []
        for filename,last in self._last_updated.items():
            if time.time() > last + self.clean_up_interval:
                to_clean.append(filename)
        for filename in to_clean:
            del self._last_updated[filename]
            for plot in self._figs[filename]:
                plt.figure(self._figs[filename][plot].number)
                plt.close()
            del self._figs[filename]
