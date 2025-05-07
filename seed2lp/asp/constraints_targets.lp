% Discard any model that is not activating all targets when not possible seeds 
% given by the user.
% This constraint is needed both for seed search (seed_solving.asp)
% and for the second step of the bistep mode in community 
% (where seed_solving.asp is not used anymore)
:- target(N,M) ; not activated(M), subseed=0.

% no_scope(N,M) :- target(N,M) ; not activated(M), subseed=0.
% #show no_scope/2.
% #show p_seed/2.
% #show new_seed/1.
% #show authorized_accu/1.
% #show target/2.
% #show can_reach/1.
% #show forbidden/1.