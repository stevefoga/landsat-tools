"""
plot_hist.py

Purpose: plot histogram with CSV, accept optional argument for split variable.

Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  17 October 2016
Modified: 29 December 2016
"""


def do_plot(csv_in, fn_out, y_var, hist_n=10, y_units="Units", split_var=None):
    """
    Function to scrape csv and do the plots.

    Args:
        csv_in <str>: input CSV file
        fn_out <str>: output directory
        y_var <str>: variable to be plotted
        y_units <str>: units of y_var (default='Units')
        hist_n <int>: number of breaks for histogram
        split_var <str>: split variable (generates boxplot for each category)
        """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.offsetbox import AnchoredText

    # read data
    c_in = pd.read_csv(csv_in)

    # get data variable
    plot_var = c_in[y_var]

    # filter out invalid entries (Excel-based nodata, etc.)
    nodata_vals = ['#VALUE!', 'NA', 'NaN', '#NULL!', '#NAME?', '#N/A',
                   '#DIV/0',
                   '#REF!', '#NUM!', 'N/A']
    valid_var = plot_var[~plot_var.isin(nodata_vals)].astype('float64')

    # if the variable is to be split into categories, plot a certain way
    if split_var:
        # get categories
        c_var = c_in[split_var]

        # remove nodata coincident with valid_var
        cat_var = c_var[~plot_var.isin(nodata_vals)]

        # combine data (easier to work with in plot)
        all_var = pd.concat([valid_var, cat_var], axis=1)

        # make histogram for data by split_var
        all_var.groupby(split_var).boxplot(return_type='axes')

        # write plot out to PNG
        plt.savefig(fn_out + "_boxplot_combined.png",
                    bbox_inches="tight",
                    dpi=350)

    # regardless, write out histogram of valid data values (i.e., NOT split)
    # plot histogram
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.hist(valid_var, int(hist_n))

    # use AnchoredText() to snap annotation to corner of graph
    anchored_text = AnchoredText("n=" + str(len(valid_var)) + "\n" +
                                 "bins=" + str(hist_n) + "\n" +
                                 "mean: " + str(
        round(np.mean(valid_var), 3)) + "\n" +
                                 "abs. mean diff: " + str(
        round(abs(np.mean(valid_var)), 3)) + "\n",
                                 prop=dict(size=8),
                                 loc=1)

    # add snapped text to axis
    ax.add_artist(anchored_text)
    ax.set_xlabel(y_units)
    ax.set_ylabel("Frequency")

    # write plot out to PNG
    plt.savefig(fn_out + "_hist_alldata.png",
                bbox_inches="tight",
                dpi=350)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    req_named = parser.add_argument_group('Required named arguments')
    req_named.add_argument('-c', action='store', dest='csv_in', type=str,
                           help='Input CSV file.', required=True)

    req_named.add_argument('-o', action='store', dest='fn_out', type=str,
                           help='Output file name.', required=True)

    req_named.add_argument('-y', action='store', dest='y_var', type=str,
                           help='Name of Y variable to be plotted.',
                           required=True)

    parser.add_argument('-yu', action='store', dest='y_units', type=str,
                        help='Name of Y variable units used in Y-axis label'
                             '(default="Units")', required=False)

    parser.add_argument('-n', action='store', dest='hist_n', type=int,
                        help='Number of bins for histogram (default=10)',
                        required=False)

    parser.add_argument('-s', action='store', dest='split_var',
                        help='Name of variable in which to split data into'
                             'separate variables. Split data generates'
                             'additional boxplot (default=None)',
                        required=False)

    arguments = parser.parse_args()

    do_plot(**vars(arguments))
