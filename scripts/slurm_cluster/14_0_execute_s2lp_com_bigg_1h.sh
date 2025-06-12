#!/bin/bash
#SBATCH --job-name=job_s2lp_com         # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --mem-per-cpu=10gb
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

COM_DIR="../../results_communities"
DIR_NAME="com_bigg_1h_results"
DIR_EQ_FLUX_NAME="com_bigg_1h_equality_flux_results"
RESULT_DIR="${COM_DIR}/${DIR_NAME}/"
RESULT_EQ_FLUX_DIR="${COM_DIR}/${DIR_EQ_FLUX_NAME}/"
TEMP_DIR=../../tmp2/
TEMP_DIR2=../../tmp6/

COM_LIST=(
          #"com_BiGG_2_2.txt"
          #"com_BiGG_2_3.txt"
          "com_BiGG_2_4.txt"
          #"com_BiGG_4_3.txt"
          )


########## EXECUTE COMMUNITY ##########

for file in "${COM_LIST[@]}"
do
  # GLOBAL
  #sbatch 14_0_job_run_s2lp.sh -c global -f $file -s reasoning -d $RESULT_DIR -t 60 -b $TEMP_DIR
  #sbatch 14_0_job_run_s2lp.sh -c global -f $file -s filter -d $RESULT_DIR -t 60 -b $TEMP_DIR
  #sbatch 14_0_job_run_s2lp.sh -c global -f $file -s filter -d $RESULT_EQ_FLUX_DIR -t 60 -b $TEMP_DIR2 -q q


  # BISTEPS
  #sbatch 14_0_job_run_s2lp.sh -c bisteps -f $file -s reasoning -d $RESULT_DIR -t 60 -b $TEMP_DIR
  #sbatch 14_0_job_run_s2lp.sh -c bisteps -f $file -s filter -d $RESULT_DIR -t 60 -b $TEMP_DIR
  #sbatch 14_0_job_run_s2lp.sh -c bisteps -f $file -s filter -d $RESULT_EQ_FLUX_DIR -t 60 -b $TEMP_DIR2 -q q


  # DELSUPSET FULL VERSION
  #sbatch 14_0_job_run_s2lp.sh -c delsupset -f $file -s reasoning -d $RESULT_DIR -t 60 -b $TEMP_DIR
  #sbatch 14_0_job_run_s2lp.sh -c delsupset -f $file -s filter -d $RESULT_DIR -t 60 -b $TEMP_DIR
  sbatch 14_0_job_run_s2lp.sh -c delsupset -f $file -s filter -d $RESULT_EQ_FLUX_DIR -t 60 -b $TEMP_DIR2 -q q

done

