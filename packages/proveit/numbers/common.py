from proveit import Operation
from proveit.numbers import Add, zero, one
from proveit import k, m, n, P
from proveit.numbers.number_sets.integers import*

Pzero = Operation(P, zero)
Pn = Operation(P, n)
P_nAddOne = Operation(P, Add(n, one))
Pm = Operation(P, m)
P_mAddOne = Operation(P, Add(m, one))
Pk = Operation(P, k)
