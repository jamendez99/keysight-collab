import os
import argparse
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# set up command line arguments
parser = argparse.ArgumentParser(
    description='Script for plotting polarization stability transient files.')
parser.add_argument('filename', type=str,
                    help='Path to transient csv file to be plotted.')
parser.add_argument('-o', '--output', type=str,
                    default='figs/longterm_pol/',
                    help='Directory in which to store generated figure. Defaults to \'./figs/longterm_pol/\'')
args = parser.parse_args()


# constants for time formatting
TIME_FMT = "%Y%m%d-%H%M%S.%f"
TIME_FMT_IMG = "%d %b %H:%M:%S"
TIME_FMT_STORE = "%m_%d_%H%M%S"

# column names
POWER = "Power (W)"
ANGLE = " Angle (deg)"
S1 = " S1"
S2 = " S2"
S3 = " S3 "
stokes_params = (S1, S2, S3)

# plotting params
# update plotting parameters
mpl.rcParams.update({'font.sans-serif': 'Helvetica',
                     'font.size': 12})


df_transient = pd.read_csv(args.filename, header=0)
time_points = np.arange(len(df_transient[POWER]), dtype=float)
time_points *= 1e-5  # convert to seconds

# get what time of file is
file_split_ext = os.path.splitext(args.filename)[0]  # remove extension
time_str = file_split_ext.split('_')[-1]  # remove everything before timestamp
time = pd.to_datetime(time_str, format=TIME_FMT)
time_image = time.strftime(TIME_FMT_IMG)

# get output filename
time_store = time.strftime(TIME_FMT_STORE)
output_filename = os.path.join(args.output, f"transient_{time_store}.png")


# plotting
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

handles = []
line = ax2.plot(time_points, df_transient[ANGLE],
                color='k', label="Angle")
for i, s in enumerate(stokes_params):
    line_stokes = ax1.plot(time_points, df_transient[s],
                           label=rf'$s_{i+1}$')
    handles.append(line_stokes[0])
handles.append(line[0])

ax1.grid('on')
ax1.set_title("Transient Data at " + time_image)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Stokes Parameter Values")
ax2.set_ylabel(r"$\Delta\theta$ (degrees)")
ax2.legend(shadow=True,
           handles=handles)

fig.tight_layout()
fig.savefig(output_filename)

print(f"Saved image to '{output_filename}'")
