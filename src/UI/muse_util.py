def embedded_view(window, scale, refresh, figure, backend):
    import numpy as np
    import matplotlib
    matplotlib.use(backend)
    import matplotlib.pyplot as plt
    import seaborn as sns
    from pylsl import resolve_byprop
    from muselsl import viewer_v1

    sns.set(style="whitegrid")

    width, height = map(int, figure.split('x'))
    figsize = (width, height)

    print("Looking for an EEG stream...")
    LSL_SCAN_TIMEOUT = 10
    streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)
    if not streams:
        raise RuntimeError("Can't find EEG stream.")
    print("EEG stream found. Starting acquisition...")

    fig, axes = plt.subplots(1, 1, figsize=figsize)
    LSLViewer = viewer_v1.LSLViewer
    lslv = LSLViewer(streams[0], fig, axes, window, scale)
    
    # Monkey patch the update_plot method to ensure timestamps is always 1D.
    original_update_plot = lslv.update_plot
    def patched_update_plot(*args, **kwargs):
        # Ensure that any new timestamps are at least 1D
        if hasattr(lslv, 'times'):
            lslv.times = np.atleast_1d(lslv.times)
        return original_update_plot(*args, **kwargs)
    lslv.update_plot = patched_update_plot

    # Connect the canvas close event to lslv.stop
    fig.canvas.mpl_connect('close_event', lambda event: lslv.stop(close_event=True))
    
    # Start the live updating (this creates the update thread).
    lslv.start()
    
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    # Attach the viewer instance to the canvas so we can access it later.
    canvas.lslv = lslv
    return canvas
