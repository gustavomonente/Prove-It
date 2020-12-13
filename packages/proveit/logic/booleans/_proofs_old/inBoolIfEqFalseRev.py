from proveit.basiclogic.booleans.theorems import falseInBool
from proveit.basiclogic import FALSE, inBool, Implies, Equals
from proveit.common import A, X

# hypothesis = (FALSE=A)
hypothesis = Equals(FALSE, A)
# inBool(FALSE)
falseInBool.proven()
# inBool(A) assuming hypothesis
conclusion = hypothesis.subRightSideInto(inBool(X), X).proven({hypothesis})
# forall_{A} (FALSE=A) => inBool(A)
Implies(hypothesis, conclusion).generalize(A).qed(__file__)
