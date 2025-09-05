% Maximization 
% When possible seeds given by the user, a subset of these seeds is choosen 
% by maximizing the targets into the scope
nb_produced_targets(X) :- X = #count{   M : target(N,M), activated(M) }.

% maximize number produced target has a higher priority than minimize seed (from minimize.lp)
#maximize{X@2, X:nb_produced_targets(X)}.