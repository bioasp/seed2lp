#!/bin/bash
#SBATCH --job-name=job_s2lp_com         # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

########## EXECUTE COMMUNITY ##########
### CHEESE 2 species ###
#sbatch 13_job_run_s2lp_com_cheese_2.sh -c global -s filter
#sbatch 13_job_run_s2lp_com_cheese_2.sh -c bisteps -s filter
#sbatch 13_job_run_s2lp_com_cheese_2.sh -c delsupset -s filter

#sbatch 13_job_run_s2lp_com_cheese_2.sh -c global -s guess_check
#sbatch 13_job_run_s2lp_com_cheese_2.sh -c bisteps -s guess_check
#sbatch 13_job_run_s2lp_com_cheese_2.sh -c delsupset -s guess_check

#sbatch 13_job_run_s2lp_com_cheese_2.sh -c global -s guess_check_div
sbatch 13_job_run_s2lp_com_cheese_2.sh -c bisteps -s guess_check_div
sbatch 13_job_run_s2lp_com_cheese_2.sh -c delsupset -s guess_check_div

### CHEESE 3 species ###
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c global -s filter
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c bisteps -s filter
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c delsupset -s filter

#sbatch 13_job_run_s2lp_com_cheese_3.sh -c global -s guess_check
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c bisteps -s guess_check
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c delsupset -s guess_check

sbatch 13_job_run_s2lp_com_cheese_3.sh -c global -s guess_check_div
sbatch 13_job_run_s2lp_com_cheese_3.sh -c bisteps -s guess_check_div
#sbatch 13_job_run_s2lp_com_cheese_3.sh -c delsupset -s guess_check_div