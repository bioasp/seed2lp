############################################
################## GLOBAL ##################
############################################

# REASONING

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so reasoning -nbs 0  -tmp tmp/


############################################

# FILTER MIN FLUX

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm global -so filter -nbs 0  -tmp tmp/

############################################

# FILTER EQUALITY FLUX

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm global -so filter -nbs 0 -ef -tmp tmp/

############################################
################# BISTEPS ##################
############################################

# REASONING

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so reasoning -nbs 0  -tmp tmp/


############################################

# FILTER MIN FLUX

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm bisteps -so filter -nbs 0  -tmp tmp/


############################################

# FILTER EQUALITY FLUX

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm bisteps -so filter -nbs 0 -ef -tmp tmp/


############################################
################ DELSUPSET #################
############################################

# REASONING


seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so reasoning -nbs 0  -tmp tmp/


############################################

# FILTER MIN FLUX


seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com/ -cm delsupset -so filter -nbs 0  -tmp tmp/


############################################

# FILTER EQUALITY FLUX

seed2lp community ../networks/toys_communities/communities/com2_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_5.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com2_6.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com3_1.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_2.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_3.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community ../networks/toys_communities/communities/com3_4.txt ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/

seed2lp community ../networks/toys_communities/communities/com4.txt   ../networks/toys_communities/sbml/ ../results/toy_com_equality_flux/ -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
