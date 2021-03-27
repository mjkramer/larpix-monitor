# LArPix monitor
A near-ish realtime data quality monitoring framework, this library + script
allows for the quick addition of new data quality plots and automated monitoring
of a live data directory.

## Installation

To install::

    pip install .

## Usage

To use::

    run_monitor.py -i <data directory to monitor> -o <directory to place plots> \
        --interval <time between checking for data updates> \
        --ext <file extension for plots> \
        --plots <set of custom plots to generate>

## Extending

To add additional data quality plots, create a new file ``<some name>.py``
within the ``monitor/plotting_functions`` directory. Within this file, create
a class with the desired plot name as the class name. Then implement the
``__call__`` method to accept as arguments ``self``, ``filename``,
``packet_collection``, and ``prev_fig=None``. These are
 - ``self``: your custom plotting class instance
 - ``filename``: the filename of the file that is being plotted
 - ``packet_collection``: a ``larpix.PacketCollection`` object containing *new* packets to plot
 - ``fig=None``: the instance of an existing ``matplotlib.pyplot.Figure`` (if it exists)

The implemented ``__call__`` method should return one argument -- the ``Figure``
that should be saved.

Updating a plot can be performed directly through interacting with the ``Figure``
instance. For example, to add points to a line plot::

    axes = fig.get_axes()
    lines = axes[0].get_lines()

    old_xy = lines[0].get_xydata()
    xy = np.append(old_xy, new_xy, axis=0)

    lines[0].set_xdata(xy[:,0])
    lines[0].set_ydata(xy[:,1])

If a previous figure does not exist, it is up to your implementation of ``__call__``
to generate a new figure.


To get you started, here's an example bare-bones template::

    import maplotlib.pyplot as plt
    import numpy as np

    class TemplatePlot(object):
        def __call__(self, filename, packet_collection, fig=None):
            if fig is not None:
                # do stuff to update plot
                pass
            else:
                # do stuff to make new plot
                fig = plt.figure()
            return fig
