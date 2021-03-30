#!/usr/bin/env python3
import argparse
import json
import os
import datetime

from monitor.file_watcher import FileWatcher
from monitor.file_parser import FileParser
from monitor.plotter import Plotter
from monitor.plotting_functions import available_plots
from collections import defaultdict 
import plotly

available_plots_plotly = [plot for plot in available_plots if 'Plotly' in plot]

def main(**kwargs):

    fw = FileWatcher(
        directory = kwargs.get('in_directory','./'),
        interval = kwargs.get('interval')
        )
    fp = FileParser(
        temp_dir = kwargs.get('temp_directory','./'),
        sampling = not kwargs.get('sampling_off'),
        max_msgs = kwargs.get('max_msgs'),
        clean_up_interval = kwargs.get('flush_interval')
        )
    p  = Plotter(
        plots = kwargs.get('plots'),
        clean_up_interval = kwargs.get('flush_interval')
        )
    
    figures = defaultdict(lambda: None)
    
    while True:
        print(datetime.datetime.now(), end='\r')

        if kwargs.get('once',None):
            datafiles = [kwargs['once']]
        else:
            datafiles = fw()
        if not datafiles: continue
        print()
        print('\tnew data in',datafiles)

        datafile_fh = fp(datafiles)
        print('\tgot',sum(map(lambda fh: len(fh['packets']),datafile_fh)),'packets')

        for d, d_fh in zip(datafiles, datafile_fh):
            if len(d_fh['packets']) == 0: continue
            for plot in p._plotters:
                figures[plot] = p._plotters[plot](d, d_fh, figures[plot])          

        index_filename = kwargs.get('out_directory')+"/index.html"
        index_file = open(index_filename, "w")
        index_file.write("<html><head><title>Module 0 data quality monitor</title><script src='https://cdn.plot.ly/plotly-latest.min.js'></script></head><body>")

        index_file.write("<h1>Module0 Data Quality Monitor</h1>")
        index_file.write('<p><em><script>document.write("This document was lastly modified on" + " " +document.lastModified);</script></em></p>')
        for f in figures:
            index_file.write("<h2>%s</h2>" % f.rstrip("Plotly"))
            index_file.write(plotly.offline.plot(figures[f], include_plotlyjs=False, output_type='div'))

        index_file.write("</body></html>")
        index_file.close()
        os.chmod(index_filename, 0o755)
        fp.clean_up_temp_files(datafiles)

        if kwargs.get('once',None):
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the LArPix data quality monitor')
    parser.add_argument('-i','--in_directory', type=str, required=False, default='./', help='''
        Directory to watch (default=%(default)s)
        ''')
    parser.add_argument('-o','--out_directory', type=str, required=False, default='./', help='''
        Directory to save plots (default=%(default)s)
        ''')
    parser.add_argument('--interval', type=float, required=False, default=30., help='''
        File update interval [s] (default=%(default)s)
        ''')
    parser.add_argument('--max_msgs', type=int, required=False, default=100000, help='''
        Maximum number of new messages to fetch from file (default=%(default)s), -1 for all messages
        ''')
    parser.add_argument('--sampling_off', action='store_true', required=False, default=False, help='''
        Disable skipping subsets of datafile
        ''')
    parser.add_argument('--once', type=str, required=False, help='''
        Run once on passed file and then exit, otherwise continously monitor for new data
        ''')
    parser.add_argument('--flush_interval', type=float, required=False, default=1800., help='''
        Memory cleaning interval [s] (default=%(default)s)
        ''')
    parser.add_argument('--ext', type=str, required=False, default='.png', help='''
        File extension to save plots as (default=%(default)s)
        ''')
    parser.add_argument('--plots', nargs='+', type=str, required=False, default=available_plots_plotly, help='''
        Plot names to generate (default=%(default)s)
        ''')
    args = parser.parse_args()
    main(**vars(args))
