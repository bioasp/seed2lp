#const limit_transfers=1.
%%%%%%%%%%%%%%%%%%%%%%% COMMUNITY METABOLITES ACTIVATION %%%%%%%%%%%%%%%%%%%%%%%
%*
A metabolite is activated by transfer between networks.
We choose the transferred metabolites that needed to be activate.
*%
nb_transfers(N) :- N=#count{M : transferred(M,_,_,_,_)}.
:- nb_transfers(N), N>limit_transfers.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%