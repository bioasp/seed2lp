#!/bin/bash
#SBATCH --job-name=job_scope_phylomint         # Job name
#SBATCH --output=../output/scope_phylomint/scope_phylomint-%A_%a.out
#SBATCH -e ../error/scope_phylomint/scope_phylomint-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%55                           #107 networks

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../analyses/data"
NORM_SBML_DIR="${DATA_DIR}/sbml_corrected"
SBML_DIR="${DATA_DIR}/bigg/sbml"
RESULT_DIR="../../analyses/results/phylomint"
SCOPE_DIR="$RESULT_DIR/scopes"
FLUX_DIR="$RESULT_DIR/fluxes"
SOLUTION_DIR="$RESULT_DIR/seeds_results"

./12_2_run_scope_flux.sh -i $SOLUTION_DIR -s $SCOPE_DIR -f $FLUX_DIR -n $NORM_SBML_DIR -b $SBML_DIR