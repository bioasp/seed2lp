#!/bin/bash
#SBATCH --job-name=bigg_data       # Job name
#SBATCH --output=../output/s2lp_com/bigg_data-%A_%a.out
#SBATCH -e ../error/s2lp_com/bigg_data-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

# NORMAL

COM_DIR="../../results_communities"

DIR_LIST=("com_bigg_15min"
         #"com_bigg_1h"
         "com_bigg_1st"
         )



# EXECUTE

for dir in "${DIR_LIST[@]}"
do
  S2LP_RESULT_DIR="${COM_DIR}/${dir}_results"
  S2LP_EQ_FLUX_RESULT_DIR="${COM_DIR}/${dir}_equality_flux_results"
  DATA_RESULT_DIR="${COM_DIR}/${dir}_data"
  # Create directories if needed
  if [[ ! -d "$DATA_RESULT_DIR" ]]
  then
    mkdir -p "$DATA_RESULT_DIR"
  fi
  python ../13_2_com_bigg_get_data_solution.py $S2LP_RESULT_DIR $S2LP_EQ_FLUX_RESULT_DIR $DATA_RESULT_DIR
done


