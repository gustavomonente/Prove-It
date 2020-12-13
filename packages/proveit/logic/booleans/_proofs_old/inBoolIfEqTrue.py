from proveit.basiclogic.booleans.theorems import trueInBool
from proveit.basiclogic import TRUE, inBool, Implies, Equals
from proveit.common import A, X

# hypothesis = (A=TRUE)
hypothesis = Equals(A, TRUE)
# inBool(TRUE)
trueInBool.proven()
# inBool(A) assuming hypothesis
conclusion = hypothesis.subLeftSideInto(inBool(X), X).proven({hypothesis})
# forall_{A} A=TRUE => inBool(A)
Implies(hypothesis, conclusion).generalize(A).qed(__file__)
