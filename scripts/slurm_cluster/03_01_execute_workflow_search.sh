#!/bin/bash
#SBATCH --job-name=job_s2lp         # Job name
#SBATCH --output=../output/workflow/s2lp-%A_%a.out
#SBATCH -e ../error/workflow/s2lp-%A_%a.err
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

# Cluster
FILE="03_01_job_run_s2lp"
###### EXECUTE FULL NETWORK #######
### ALL ###
# Accumulation Forbidden
#sbatch $FILE -c full -m m
# Accumulation Allowed
#sbatch $FILE -c full -m m -a a

### SPECIFIC ###
sbatch $FILE -c full -m m -s filter 
sbatch $FILE -c full -m m -s guess_check
sbatch $FILE -c full -m m -s guess_check_div


sbatch $FILE -c full -m m -s filter -a a
sbatch $FILE -c full -m m -s guess_check -a a
sbatch $FILE -c full -m m -s guess_check_div -a a
###################################

########## EXECUTE TARGET ##########
### ALL ###
# Accumulation Forbidden
#sbatch $FILE -c target -m m 
# Accumulation Allowed
#sbatch $FILE -c target -m m -a a

### SPECIFIC ###
sbatch $FILE -c target -m m -s filter
sbatch $FILE -c target -m m -s guess_check
sbatch $FILE -c target -m m -s guess_check_div


sbatch $FILE -c target -m m -s filter -a a
sbatch $FILE -c target -m m -s guess_check -a a
sbatch $FILE -c target -m m -s guess_check_div -a a
###################################
