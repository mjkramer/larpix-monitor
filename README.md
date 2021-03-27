# LArPix monitor
A near-ish realtime data quality monitoring framework, this library + script
allows for the quick addition of new data quality plots and automated monitoring
of a live data directory.

## Installation

To install::

    pip install -e .

## Usage

To use as continuous data quality monitor::

    run_monitor.py \
        -i <data directory to monitor> \
        -o <directory to place plots> \
        --interval <time between checking for data updates> \
        --flush_interval <max time to keep temporary data> \
        --ext <file extension for plots> \
        --plots <set of custom plots to generate>

To manually force generation of plots on a specific file::

    run_monitor.py \
        --once <file to process> \
        -o <directory to place plots> \
        --ext <file extension for plots> \
        --plots <set of custom plots to generate>

## Extending

To add additional data quality plots, create a new file ``<some name>.py``
within the ``monitor/plotting_functions`` directory. Within this file, create
a class with the desired plot name as the class name. Then implement the
``__call__`` method to accept as arguments ``self``, ``filename``,
``fh``, and ``fig=None``. These are
 - ``self``: your custom plotting class instance
 - ``filename``: the filename of the file that is being plotted
 - ``fh``: an ``h5py`` temporary file object containing *new* packets to plot
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

## Template plotting class

To get you started, here's an example bare-bones template::

    import maplotlib.pyplot as plt
    import numpy as np

    class TemplatePlot(object):
        def __call__(self, filename, fh, fig=None):
            # pre-process data in fh
            if fig is not None:
                # do stuff to update plot
                pass
            else:
                # do stuff to make new plot
                fig = plt.figure()
            return fig

# Other notes

## Pixel map geometry

The pixel map plots (``PixelMap_X_X``) require a geometry file to look up each
pixel position. The path to a ``larpix-geometry`` yaml file should be specified
via the environment variable ``PIXEL_GEOMETRY_PATH``. Otherwise, a default
path of ``./layout-2.4.0.yaml`` will be used.
