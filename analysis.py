import pandas as pd
import numpy as np


def parse_data(filename, ftype='transient'):
    if ftype == 'coarse':
        df = pd.read_csv(filename, skiprows=1)
        vecs = df[[' S1', ' S2', ' S3 ']].values
        powers = df[' Power (W)'].values
        times = pd.to_datetime(df['time'], format='%Y%m%d-%H%M%S.%f').values
        return vecs, times, powers
    elif ftype == 'transient':
        'Power (W), Angle (deg), S1, S2, S3 '
        df = pd.read_csv(filename)
        vecs = df[[' S1', ' S2', ' S3 ']].values
        powers = df['Power (W)'].values
        angles = df[' Angle (deg)'].values
        return vecs, angles, powers
    else:
        raise Exception('Invalid ftype. Must be coarse or transient.')


def normalize(vector):
    magnitude = np.linalg.norm(vector)
    return vector / magnitude if magnitude != 0 else vector


def autocorrelation(vecs):
    # Normalize each Stokes vector
    norm_vecs = np.apply_along_axis(normalize, 1, vecs)

    n = len(norm_vecs)
    num_lag_values = int(n * 0.2)  # 20% of the number of inner products
    lag_values = np.arange(1, num_lag_values + 1)
    autocorrelation = np.zeros(num_lag_values)

    for i, lag in enumerate(lag_values):
        inner_products = np.sum(norm_vecs[:-lag] * norm_vecs[lag:], axis=1)
        autocorrelation[i] = np.mean(inner_products)

    return lag_values, autocorrelation

# Test comment
