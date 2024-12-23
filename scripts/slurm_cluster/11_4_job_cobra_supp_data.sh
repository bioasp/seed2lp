#!/bin/bash
#SBATCH --job-name=job_cobra_supp         # Job name
#SBATCH --output=../output/cobra_supp/cobra_supp-%A_%a.out
#SBATCH -e ../error/cobra_supp/cobra_supp-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=24:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../analyses/data"
OBJECTIVE_DIR="${DATA_DIR}/objective"
SBML_DIR="${DATA_DIR}/sbml_corrected"

######################################
############ ONE SOLUTION ############
######################################
NUM="_1"
RESULT_DIR="../../analyses/results/cobra$NUM"
SOLUTION_DIR="$RESULT_DIR/seeds_results"

python ../11_4_get_cobra_supp_data.py $SOLUTION_DIR $RESULT_DIR 
######################################




######################################
########### TEN SOLUTIONS ############
######################################
NUM="_10"
RESULT_DIR="../../analyses/results/cobra$NUM"
SOLUTION_DIR="$RESULT_DIR/seeds_results"

python ../11_4_get_cobra_supp_data.py $SOLUTION_DIR $RESULT_DIR 
######################################