#!/bin/bash
#SBATCH --job-name=ecoli_data       # Job name
#SBATCH --output=../output/s2lp_com/ecoli_data-%A_%a.out
#SBATCH -e ../error/s2lp_com/ecoli_data-%A_%a.err
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
PARTIAL_DELSUPSET_COM_DIR="../../results_communities_pd"

DIR_LIST=(
        #"e_coli_core_2_1_altered_limtransf2_1st"
        "e_coli_core_2_1_altered_limtransf2_15min"
         #"e_coli_core_2_1_altered_limtransf2_1h"
         #"e_coli_core_2_1_limtransf2_1st"
         #"e_coli_core_2_1_limtransf2_15min"
         #"e_coli_core_2_1_limtransf3_15min"
         #"e_coli_core_2_1_limtransf2_1h"
         #"e_coli_core_2_1_limtransf3_1h"
         #"e_coli_core_2_1_nolimtransf_24h"
         )

PARTIAL_DELSUPSET_DIR_LIST=(
        #"e_coli_core_2_1_limtransf2_15min"
        #"e_coli_core_2_1_limtransf3_15min"
        #"e_coli_core_2_1_limtransf2_1h"
        #"e_coli_core_2_1_limtransf3_1h"
        #"e_coli_core_2_1_nolimtransf_24h"
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
  python ../13_2_com_ecoli_get_data_solution.py $S2LP_RESULT_DIR $DATA_RESULT_DIR
done


for dir in "${PARTIAL_DELSUPSET_DIR_LIST[@]}"
do
  S2LP_RESULT_DIR="${PARTIAL_DELSUPSET_COM_DIR}/${dir}_results"
  DATA_RESULT_DIR="${PARTIAL_DELSUPSET_COM_DIR}/${dir}_data"
  # Create directories if needed
  if [[ ! -d "$DATA_RESULT_DIR" ]]
  then
    mkdir -p "$DATA_RESULT_DIR"
  fi
  python ../13_2_com_ecoli_get_data_solution.py $S2LP_RESULT_DIR $DATA_RESULT_DIR
done
# python scripts/13_2_com_ecoli_get_data_solution.py results/e_coli_core_2_1_lim_transf results/e_coli_core_2_1_lim_transf_data