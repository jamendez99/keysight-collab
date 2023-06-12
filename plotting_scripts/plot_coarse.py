import glob
import os
import argparse
import pandas as pd
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


# set up command line arguments
parser = argparse.ArgumentParser(
    description='Script for plotting long-term polarization stability studies.')
parser.add_argument('csv_path', type=str,
                    help='Directory containing link data stored as CSV files.'
                         'Should contain both the single coarse measurement file and several transient measurements.')
parser.add_argument('-o', '--output', type=str,
                    default='figs/longterm_pol/',
                    help='Directory in which to store generated figure. Defaults to \'./figs/longterm_pol/\'')
args = parser.parse_args()


# constants for time formatting
TIME_FMT = "%Y%m%d-%H%M%S.%f"
TIME_FMT_STORE = "%m_%d"

# column names
TIME = "time"
POWER = " Power (W)"
S1 = " S1"
S2 = " S2"
S3 = " S3 "
stokes_params = (S1, S2, S3)

# plotting params
mpl.rcParams.update({'font.sans-serif': 'Helvetica',
                     'font.size': 12})
TRUNCATE_TIME = False
TIME_FMT_LIMITS = "%Y%m%d-%H"
time_start = pd.to_datetime("20230515-12", format=TIME_FMT_LIMITS)
time_end = pd.to_datetime("20230515-18", format=TIME_FMT_LIMITS)


# locate coarse file
coarse_file = glob.glob('*_coarse_*', root_dir=args.csv_path)[0]
coarse_path = os.path.join(args.csv_path, coarse_file)

df_coarse = pd.read_csv(coarse_path, header=1)
time_datetime = pd.to_datetime(df_coarse[TIME],
                               format=TIME_FMT)

# make output filename
time_to_label = time_datetime[0]
output_filename = os.path.join(args.output, f"coarse_{time_to_label.strftime(TIME_FMT_STORE)}.png")

# get time of all transient recordings
transient_files = glob.glob('*_transient_*', root_dir=args.csv_path)
transient_times = [None] * len(transient_files)
for i, file in enumerate(transient_files):
    file_split_ext = os.path.splitext(file)[0]  # remove extension
    time_str = file_split_ext.split('_')[-1]  # remove excess info
    time = pd.to_datetime(time_str, format=TIME_FMT)
    transient_times[i] = time


# plotting
fig, ax = plt.subplots()
fig.autofmt_xdate()

for time in transient_times:
    ax.axvline(x=time, color='k')
for i, s in enumerate(stokes_params):
    ax.plot(time_datetime, df_coarse[s],
            label=rf'$s_{i+1}$')

if TRUNCATE_TIME:
    ax.set_xlim((time_start, time_end))
xfmt = mdates.DateFormatter('%d %b %H:%M')
ax.xaxis.set_major_formatter(xfmt)
ax.grid('on', axis='y')
ax.set_title("Polarization Drift and Transient Recording")
ax.set_xlabel("Time")
ax.set_ylabel("Stokes Parameter Values")
ax.legend(shadow=True)

fig.tight_layout()
fig.savefig(output_filename)

print(f"Saved image to '{output_filename}'")
