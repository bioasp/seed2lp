#!/bin/bash
#SBATCH --job-name=job_com_s2lp         # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --mem-per-cpu=50gb
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH -C kona

########## SERVER ##########
COM_DIR="../../networks"
DESC_DIR="${COM_DIR}/description"
XML_DIR="${COM_DIR}/xml/"

while getopts c:f:s:e:a:p:d:t:l:n:b:q: flag
do
    case "${flag}" in
        c) COM_MODE=${OPTARG};;
        f) COM_FILE=${OPTARG};;
        s) SOLVE=${OPTARG};;
        e)
          if [[ -n ${OPTARG} ]]; then
              FORBIDDEN_SEEDS_FILE=${OPTARG}
          fi
        ;;
        p)
          if [[ -n ${OPTARG} ]]; then
              PARTIAL_DELSUPSET=${OPTARG}
          fi
        ;;
        d) RESULT_DIR=${OPTARG};;
        t)
          if [[ -n ${OPTARG} ]]; then
              TIME_LIMIT=${OPTARG}
          fi
        ;;
        l)
          if [[ -n ${OPTARG} ]]; then
              LIMIT_TRANSFERS=${OPTARG}
          fi
        ;;
        n)
          if [[ -n ${OPTARG} ]]; then
              NB_SOLUTION=${OPTARG}
          fi
        ;;
        a)
          if [[ -n ${OPTARG} ]]; then
              ALL_TRANSFERS=${OPTARG}
          fi
        ;;
        b)
          if [[ -n ${OPTARG} ]]; then
              TEMP_DIR=${OPTARG}
          fi
        ;;
        q)
          if [[ -n ${OPTARG} ]]; then
              EQ_FLUX=${OPTARG}
          fi
        ;;

    esac
done



COM_PATH="${DESC_DIR}/${COM_FILE}"

COMPLEMENT_ARG="-so $SOLVE "


# Create directories if needed
if [[ ! -d "$RESULT_DIR" ]]
then
  mkdir -p "$RESULT_DIR"
fi

if [[ ! -d "$RESULT_DIR/logs" ]]
then
  mkdir -p "$RESULT_DIR/logs"
fi

# if argument empty
if [[ -z ${TIME_LIMIT} ]]; then
  TIME_LIMIT=1440
fi

if [[ -z ${NB_SOLUTION} ]]; then
  NB_SOLUTION=0
fi

if [[ -z ${TEMP_DIR} ]]; then
  TEMP_DIR="../../tmp/"
fi


# if argument not empty
if [[ -n ${FORBIDDEN_SEEDS_FILE} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-fsf $FORBIDDEN_SEEDS_FILE "
fi

if [[ -n ${ALL_TRANSFERS} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-at "
fi

if [[ -n ${PARTIAL_DELSUPSET} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-pd "
fi

if [[ -n ${LIMIT_TRANSFERS} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-lt $LIMIT_TRANSFERS "
fi

if [[ -n ${EQ_FLUX} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-ef "
fi


#echo seed2lp community $COM_PATH $XML_DIR $RESULT_DIR -cm $COM_MODE -tl $TIME_LIMIT -nbs $NB_SOLUTION -tmp $TEMP_DIR $COMPLEMENT_ARG
seed2lp community $COM_PATH $XML_DIR $RESULT_DIR -cm $COM_MODE -tl $TIME_LIMIT -nbs $NB_SOLUTION -tmp $TEMP_DIR $COMPLEMENT_ARG
