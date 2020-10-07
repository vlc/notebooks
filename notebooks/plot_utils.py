"""Utils for working with notebooks."""
import logging
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.core.display import display, HTML
from scipy import stats

from four_step.common.logging_utils import indent


def plot_trip_ends(productions, attractions, year):
    """Plot the trip ends."""
    f, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True)
    sns.despine(left=True)

    productions = productions.sum()
    attractions = attractions.sum()
    labels = [x.upper() for x in productions.index]
    sns.barplot(x=labels, y=productions.values, palette="vlag", ax=axes[0])
    axes[0].title.set_text("Productions by Purpose {}".format(year))
    sns.barplot(x=labels, y=attractions.values, palette="vlag", ax=axes[1])
    axes[1].title.set_text("Attractions by Purpose {}".format(year))
    plt.show()


def plot_matrix_as_image(title, actual, expected):
    """Show a matrix as an image."""
    # First setup our figure
    sns.set()
    plt.tight_layout()

    # Get data
    diff = expected - actual
    max_diff = diff.max()

    # Actual plot
    plot = sns.heatmap(diff)

    # Title and stats
    plot.set_title(
        """{title}
        $max(Difference) = {diff}$""".format(
            title=title, diff=abs(round(max_diff, 3))
        )
    )
    plt.show()


def get_stats(x, y, thresh=0.0):
    """Perform linear regression between x & y and return stats of such."""
    if len(x.shape) > 1:
        x = x.ravel()
        y = y.ravel()
    slope, intercept, r_value, p_value, err = stats.linregress(x, y)
    r2 = round(r_value ** 2, 3)
    m = round(slope, 2)
    diff = y - x
    min_diff, max_diff = min(diff), max(diff)
    perc_diff = 100.0 * sum(abs(diff) > thresh) / len(diff)
    return (m, r2, min_diff, max_diff, perc_diff)


def plot_matrix_diff(x, y, x_label, y_label, title, regplot=False, exclude_threshold=None):
    # type: (np.ndarray, np.ndarray, str, str, str, bool, float) -> None
    """Compare two matrices using various plots."""
    x_col = x.ravel()
    y_col = y.ravel()
    plot_scatter(x_col, y_col, x_label, y_label, title, regplot, exclude_threshold)


def plot_scatter(x_col, y_col, x_label, y_label, title, regplot=False, exclude_threshold=None):
    # type: (np.ndarray, np.ndarray, str, str, str, bool, float) -> Tuple
    """Produce plots comparing two matrices."""
    diff = y_col - x_col
    if exclude_threshold is not None:
        x_col = x_col[abs(diff) > exclude_threshold]
        y_col = y_col[abs(diff) > exclude_threshold]
        diff = diff[abs(diff) > exclude_threshold]
        if diff.size < 2:
            raw_html = "<h3>{}</h3><p>There were no differences within the given threshold, nothing to plot</p>"
            display(HTML(raw_html.format(title)))
            return ()

    # Get linregress
    m, r2, _, _, _ = get_stats(x_col, y_col, 0.0)
    raw_html = "<div><h3>{title} [N={N} > {thresh}]</h3><p>$r^2 = {r2}$ $y = {m}$</h3></div>".format(
        title=title, r2=r2, m=m, N=diff.size, thresh=exclude_threshold
    )

    display(HTML(raw_html))

    # Plots
    plt.figure(figsize=(10, 5))

    # Plot scatter plot with regression line
    if regplot:
        _ = plt.subplot(1, 2, 1)
        sns.regplot(x_col, y_col)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        _ = plt.subplot(1, 2, 2)

    # Plot histogram of differences
    sns.distplot(diff, kde_kws={"shade": True}, rug=True)
    plt.show()
    return (m, r2)


def log_summary_of_dict(dict, title, label):
    """Log summary of dictionary."""
    df = pd.DataFrame(dict, index=[label]).T
    log_dataframe(df, title)


def log_dataframe(df, title):
    """Log dataframe."""
    summary_table = str(df).splitlines()
    longest_line = max(len(title), len(summary_table[0]) + 2)
    logging.info("=" * longest_line)
    with indent(title):
        for line in summary_table:
            logging.info(line)
    logging.info("=" * longest_line)


def bar_plot_from_dict(dict, title, label="things"):
    # type: (Dict[str,float], str, Optional[str]) -> None
    """Generate a bar chart from the given dictionary."""
    plt.figure(figsize=(10, 5))
    x = np.arange(len(dict))
    plt.bar(x, list(dict.values()))
    plt.xticks(x, list(dict.keys()))
    log_summary_of_dict(dict, title, label)
    title and plt.title(title)
