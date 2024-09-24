#!/bin/bash
#SBATCH --job-name=job_timers         # Job name
#SBATCH --output=../output/timers/timers-%A_%a.out
#SBATCH -e ../error/timers/timers-%A_%a.err
#SBATCH #SBATCH --nodes=1                                   #Number of nodes    
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=10:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
NORM_SBML_DIR="${DATA_DIR}/sbml_corrected"
RESULT_DIR="../../results"
S2LP_RESULT_DIR="${RESULT_DIR}/s2lp"
iCN718_RESULT_DIR="${RESULT_DIR}/iCN718"
ONESOL_RESULT_DIR="${RESULT_DIR}/one_solution"
OUT_DIR="${RESULT_DIR}/supp_data"
FILE="../10_4_get_supp_data.py"


# SERVER
python $FILE $S2LP_RESULT_DIR $NORM_SBML_DIR $OUT_DIR "seed2lp"
python $FILE $iCN718_RESULT_DIR $NORM_SBML_DIR $OUT_DIR "iCN718_2000"
python $FILE $ONESOL_RESULT_DIR $NORM_SBML_DIR $OUT_DIR "one_solution"
