% Add minimze option and show the total number of seeds in a set
% Ensure the minimality of the set of seeds

nb_seed(N) :- N=#count{X,M : seed(X,M)}.

% minimize seed has a lower priority than maximize number produced target  (from maximize_produced_targets.lp)
#minimize{N@1, N:nb_seed(N)}.
%#show nb_seed/1.
