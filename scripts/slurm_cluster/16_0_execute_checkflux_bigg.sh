#!/bin/bash
#SBATCH --job-name=bigg_check_flux       # Job name
#SBATCH --output=../output/s2lp_com/bigg_check_flux-%A_%a.out
#SBATCH -e ../error/s2lp_com/bigg_check_flux-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

# NORMAL

COM_DIR="../../results_communities"

DIR_LIST=(
         "com_bigg_15min"
         #"com_bigg_1h"
         "com_bigg_1st"
         )

COM_LIST=(
          "com_BiGG_2_2"
          "com_BiGG_2_3"
          "com_BiGG_2_4"
          "com_BiGG_4_3"
          )

COM_MOD=(
          "global"
          "bisteps"
          "delsupset"
)

# EXECUTE



for dir in "${DIR_LIST[@]}"
do
  # Create directories if needed
  OUTPUT_DIR="${COM_DIR}/${dir}_fluxes/"
  if [[ ! -d "$OUTPUT_DIR" ]]
  then
    mkdir -p "$OUTPUT_DIR"
  fi

 for mod in "${COM_MOD[@]}"
  do
    for com in "${COM_LIST[@]}"
    do
      DIR_RESULTS="${COM_DIR}/${dir}_results/"
      sbatch 16_0_job_run_checkflux.sh -c $com -d $DIR_RESULTS -o ${OUTPUT_DIR}/min -m $mod
      sbatch 16_0_job_run_checkflux.sh -c $com -d $DIR_RESULTS -o ${OUTPUT_DIR}/equal -q q -m $mod
    done
  done
done
