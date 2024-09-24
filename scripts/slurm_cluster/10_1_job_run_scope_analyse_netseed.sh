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
#SBATCH --array=1-107%55                           #108 networks


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
OBJECTIVE_DIR="${DATA_DIR}/objective"
SBML_DIR="${DATA_DIR}/bigg/sbml"
RESULT_DIR="../../results"
SCOPE_DIR="$RESULT_DIR/scopes_netseed"


LIST_DIR_LEV1=("netseed")
LIST_DIR_LEV2=("netseed")
LIST_DIR_LEV3=("other")
LIST_DIR_LEV4=("accu")

./10_01_run_scope_analyse.sh -r $SCOPE_DIR -s $SBML_DIR -o $OBJECTIVE_DIR \
            -a $LIST_DIR_LEV1 -b $LIST_DIR_LEV2 -c $LIST_DIR_LEV3 -d $LIST_DIR_LEV4