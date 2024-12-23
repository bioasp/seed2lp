#!/bin/bash
#SBATCH --job-name=job_cobra         # Job name
#SBATCH --output=../output/cobra/cobra-%A_%a.out
#SBATCH -e ../error/cobra/cobra-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../analyses/data"
OBJECTIVE_DIR="${DATA_DIR}/objective"
TARGET_DIR="${DATA_DIR}/target"
SBML_DIR="${DATA_DIR}/bigg/sbml"


######################################
########### TEN SOLUTIONS ############
######################################
NB_SOLUTION=10
NUM="_$NB_SOLUTION"
RESULT_DIR="../../analyses/results/cobra$NUM"

./11_1_run_cobra_seedsearch.sh  -s $SBML_DIR -o $OBJECTIVE_DIR -t $TARGET_DIR -r $RESULT_DIR -n $NB_SOLUTION
######################################