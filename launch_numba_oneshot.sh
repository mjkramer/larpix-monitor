# Launch the larpix data quality monitor
#
# Usage:
#   ./launch.sh

# directory to monitor for new data
#INDIR="/data/LArPix/Module2_Nov2022/TPC12/dataRuns/rawData/"
#INDIR="/data/LArPix/Module2_Nov2022/TPC12"

# !!! Note from P Madigan (11/19/2022):
# The DQM should point to the "live" data directory, otherwise the DQM plots will be delayed until the run completes
# If you need use the DQM to monitor a different "live" directory, then you can point it there, but for the standard
# operation so far the directory below is the one we want

if [[ "$CONDA_DEFAULT_ENV" != "larpix-monitor" ]]; then
      echo "Please do "conda activate larpix-monitor" before launching me"
      exit 1
fi

INDIR="/data/LArPix/ModuleX/temp"
# INDIR="/home/daq/PACMANv1rev3b/ModuleX/crs_daq"

# directory to generate plots in
OUTDIR="/data/LArPix/ModuleX/DQM/commission"
#OUTDIR="$INDIR/DQM"

mkdir -p $OUTDIR

DQMTMPDIR=./dqm_temp/
mkdir -p $DQMTMPDIR

export PIXEL_GEOMETRY_PATH="/home/daq/PACMANv1rev3b/larpix-geometry/larpixgeometry/layouts/layout-2.4.0.yaml"

# this is just a symlink to run_monitor.py, to avoid a name collision with the
# non-numba monitor which would trigger the zombie-detection code below
DQM="./run_monitor_numba.py"

if [[ "$1" == "--kill" ]]; then
     ps ux | grep $DQM | grep -v grep | awk '{print $2}' | xargs -l kill -9
fi

nprocs=$(ps ux | grep $DQM | grep -v grep | wc -l)
if [[ "$nprocs" != "0" ]]; then
     echo "Existing DQM processes found, they might be zombies!"
     echo "Pass --force to spin up a new DQM anyway."
     echo "Pass --kill to kill existing DQMs and spin up a new one."
     echo "Use 'ps ux | grep $DQM' to get an idea of what is going on."

     if [[ "$1" == "--force" ]]; then
          echo -e "\nYou passed --force, so here we go."
     else
          echo -e "\nYou did not pass --force, bailing out."
          exit 1
     fi
fi

for f in $INDIR/*.h5; do
    # echo $f
    if [[ ! -d "$OUTDIR/$(basename $f .h5)_dqm" ]]; then
        $DQM --once $f -o $OUTDIR \
             --numba --max_msgs=-1 \
             --temp_directory=$DQMTMPDIR
    fi
done

