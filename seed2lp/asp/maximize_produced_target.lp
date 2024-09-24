% Maximization 
% When possible seeds given by the user, a subset of these seeds is choosen 
% by maximizing the targets into the scope
nb_produced_targets(N) :- N = #count{   M : target(M), activated(M) }.

% maximize number produced target has a higher priority than minimize seed (from minimize.lp)
#maximize{N@2, N:nb_produced_targets(N)}.