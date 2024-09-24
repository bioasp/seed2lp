#!/bin/bash
#SBATCH --job-name=job_scope_netseed         # Job name
#SBATCH --output=../output/scope_netseed/scope_netseed-%A_%a.out
#SBATCH -e ../error/scope_netseed/scope_netseed-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=24:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%25                           #107 networks

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp


DATA_DIR="../../data"
NORM_SBML_DIR="${DATA_DIR}/sbml_corrected"
RESULT_DIR="../../results"
SOLUTION_DIR="$RESULT_DIR/netseed_formated_results"
SCOPE_DIR="$RESULT_DIR/scopes_netseed"



./09_run_scope.sh -i $SOLUTION_DIR -s $SCOPE_DIR -n $NORM_SBML_DIR