#!/bin/bash
#SBATCH --job-name=job_scope_s2lp         # Job name
#SBATCH --output=../output/scope_s2lp/scope_s2lp-%A_%a.out
#SBATCH -e ../error/scope_s2lp/scope_s2lp-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=24:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01



source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate seed2lp


RESULT_DIR="../../results"
S2LP_SCOPE_DIR="$RESULT_DIR/scopes_s2lp"
NETSEED_SCOPE_DIR="$RESULT_DIR/scopes_netseed"
ICN718_SCOPE_DIR="$RESULT_DIR/scopes_iCN718"

./10_2_run_scope_analyse_concat.sh -r $S2LP_SCOPE_DIR
./10_2_run_scope_analyse_concat.sh -r $NETSEED_SCOPE_DIR
./10_2_run_scope_analyse_concat.sh -r $ICN718_SCOPE_DIR
