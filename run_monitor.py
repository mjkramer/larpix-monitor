#!/usr/bin/env python3
import argparse
import json
import os
import datetime

from monitor.file_watcher import FileWatcher
from monitor.file_loader import FileLoader
from monitor.plotter import Plotter
from monitor.plotting_functions import available_plots

def main(**kwargs):

    fw = FileWatcher(
        directory=kwargs.get('in_directory','./'),
        interval=kwargs.get('interval')
        )
    fl = FileLoader(
        clean_up_interval=kwargs.get('flush_interval')
        )
    p  = Plotter(
        plots=kwargs.get('plots'),
        clean_up_interval=kwargs.get('flush_interval')
        )

    while True:
        datafiles = fw()
        print(datetime.datetime.now(), end='\r')
        if not datafiles: continue
        print('',end='\n\t')
        print('new data in',datafiles, end='\n\t')

        datafile_packets = fl(datafiles)
        print('got',sum(map(len,datafile_packets)),'packets', end='\n\t')

        datafile_figs = p(zip(datafiles, datafile_packets))
        print('generated',sum(map(len,datafile_figs)),'plots', end='\n\t')

        for filename,figs in zip(datafiles,datafile_figs):
            dir_name = os.path.join(kwargs.get('out_directory'), filename[:-3] + '_dqm')
            for fig_name, fig in figs.items():
                os.makedirs(dir_name, exist_ok=True)
                fig.savefig(os.path.join(
                    dir_name, fig_name + kwargs.get('ext')
                    ))
            print('done writing to',dir_name, end='\n\t')

        print()
        if kwargs.get('once',False):
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
    parser.add_argument('--once', action='store_true', required=False, help='''
        Run once and then exit, otherwise continously monitor for new data
        ''')
    parser.add_argument('--flush_interval', type=float, required=False, default=1800., help='''
        Memory cleaning interval [s] (default=%(default)s)
        ''')
    parser.add_argument('--ext', type=str, required=False, default='.png', help='''
        File extension to save plots as (default=%(default)s)
        ''')
    parser.add_argument('--plots', nargs='+', type=str, required=False, default=available_plots, help='''
        Plot names to generate (default=%(default)s)
        ''')
    args = parser.parse_args()
    main(**vars(args))
