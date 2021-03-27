import time
from collections import defaultdict
import os

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

    def __call__(self, datafile_packets):
        rv = list()
        for datafile, packets in datafile_packets:
            rd = dict()
            for plot in self.plots:
                fig_name = self._format_fig_name(datafile, plot)
                self._figs[datafile][plot] = self._plotters[plot](
                    datafile,
                    packets,
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
        for filename,last in self._last_updated.items():
            if time.time() > last + self.clean_up_interval:
                del self._last_updated[filename]
                del self._curr_index[filename]
