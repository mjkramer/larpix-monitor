import matplotlib.pyplot as plt

class TestPlot(object):
    def __call__(self, filename, packet_collection, fig=None):
        if fig is not None:
            # do stuff to update plot
            pass
        else:
            # do stuff to make new plot
            fig = plt.figure(dpi=100)
        return fig
