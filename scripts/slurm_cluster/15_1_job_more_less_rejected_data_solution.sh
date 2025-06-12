#!/bin/bash
#SBATCH --job-name=more_less_data       # Job name
#SBATCH --output=../output/s2lp_com/more_less_data-%A_%a.out
#SBATCH -e ../error/s2lp_com/more_less_data-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp


COM_DIR="../../results_communities"

DIR_LIST=(
          #"more_less_rejected_nolimtransf_15min"
          #"more_less_rejected_limtransf6_15min"
          "more_less_rejected_limtransf12_15min"
          #"more_less_rejected_nolimtransf_24h"
          #"more_less_rejected_limtransf6_24h"
          #"more_less_rejected_limtransf12_24h"
          #"more_less_rejected_nolimtransf_1h"
          #"more_less_rejected_limtransf6_1h"
          "more_less_rejected_limtransf12_1h"
          #"more_less_rejected_nolimtransf_1st"
          #"more_less_rejected_limtransf6_1st"
          "more_less_rejected_limtransf12_1st"
         )




# EXECUTE

for dir in "${DIR_LIST[@]}"
do
  S2LP_RESULT_DIR="${COM_DIR}/${dir}_results"
  DATA_RESULT_DIR="${COM_DIR}/${dir}_data"
  
  # Create directories if needed
  if [[ ! -d "$DATA_RESULT_DIR" ]]
  then
    mkdir -p "$DATA_RESULT_DIR"
  fi
  python ../13_2_com_more_less_rejected_get_data_solution.py $S2LP_RESULT_DIR $DATA_RESULT_DIR
done

