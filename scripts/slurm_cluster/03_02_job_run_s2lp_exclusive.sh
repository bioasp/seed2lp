#!/bin/bash
#SBATCH --job-name=job_s2lp         # Job name
#SBATCH --output=../output/s2lp/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp/s2lp-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.

#SBATCH -C zonda
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%1                           #108 networks
#SBAYCH --exclusive


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp


DATA_DIR="../../data"
S2LP_RESULT_DIR="../../results/s2lp"
SBML_DIR="${DATA_DIR}/bigg/sbml"
OBJECTIVE_DIR="${DATA_DIR}/objective"
TEMP_DIR="../../tmp/"

while getopts c:m:a:s: flag
do
    case "${flag}" in
        c) COMMAND=${OPTARG};;
        m) 
          if [[ ! -z ${OPTARG} ]]; then
              MAXIMIZATION=${OPTARG}
          fi
        ;;
        a) 
          if [[ ! -z ${OPTARG} ]]; then
              ACCUMULATION=${OPTARG}
          fi
        ;;
        s) 
          if [[ ! -z ${OPTARG} ]]; then
              SOLVE=${OPTARG}
          fi
        ;;
    esac
done

OPTION=""
if [[ ! -z ${MAXIMIZATION} ]]; then
    OPTION="-m m"
fi
if [[ ! -z ${ACCUMULATION} ]]; then
    OPTION="${OPTION} -a a"
fi
if [[ ! -z ${SOLVE} ]]; then
OPTION="${OPTION} -s ${SOLVE}"
fi

########### ALL SBML source in RESULTS dir ###########

./03_run_s2lp.sh -i $SBML_DIR -r $S2LP_RESULT_DIR \
              -c $COMMAND -t $TEMP_DIR -o $OBJECTIVE_DIR $OPTION