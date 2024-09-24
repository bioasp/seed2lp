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
conda activate s2lp

DATA_DIR="../../data"
SBML_DIR="${DATA_DIR}/bigg/sbml"
SPECIES="iCN718"
SBML_FILE="${SBML_DIR}/${SPECIES}.xml"
RESULT_DIR="../../results"
SPECIES_RESULT_DIR="$RESULT_DIR/${SPECIES}/${SPECIES}"
OUT_DIR="${RESULT_DIR}/metabolites_${SPECIES}"

if [[ ! -d "$OUT_DIR" ]]
then
  mkdir -p "$OUT_DIR"
fi

python ../10_3_iCN718_metabolite_analyses.py $SPECIES_RESULT_DIR $SBML_FILE $OUT_DIR