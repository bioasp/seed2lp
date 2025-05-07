solseed("abc","A").
solseed("abc","B").
solseed("abc","C").

solseed("abcde","A").
solseed("abcde","B").
solseed("abcde","C").
solseed("abcde","D").
solseed("abcde","E").

solseed("efg","E").
solseed("efg","F").
solseed("efg","G").

solseed("mnopq","M").
solseed("mnopq","N").
solseed("mnopq","O").
solseed("mnopq","P").
solseed("mnopq","Q").

soltransfert("12345","1").
soltransfert("12345","2").
soltransfert("12345","3").
soltransfert("12345","4").
soltransfert("12345","5").

soltransfert("678","6").
soltransfert("678","7").
soltransfert("678","8").

soltransfert("5678","5").
soltransfert("5678","6").
soltransfert("5678","7").
soltransfert("5678","8").

psolseedname("abc").
psolseedname("abcde").
psolseedname("efg").
psolseedname("mnopq").

psoltransfertname("12345").
psoltransfertname("678").
psoltransfertname("5678").

1{solseedname(A): psolseedname(A)}1.
1{soltransfertname(A): psoltransfertname(A)}1.

%seed(M) :- solseed(A,M), solseedname(A).
seed("A"). seed("B"). seed("C").

transfert(M) :- soltransfert(A,M), soltransfertname(A).


#heuristic seed(_). [2,false]
#heuristic transfert(_). [1,false]

%#show solseedname/1.
%#show soltransfertname/1.

#show seed/1.
#show transfert/1.