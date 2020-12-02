from proveit.basiclogic.boolean.axioms import existsDef
from proveit.basiclogic import Equals, Or
from proveit.common import P, S, X, Qetc

# exists_{..x.. in S | ..Q(..x..)..} P(..x..) = not(forall_{..x.. | ..Q(..x..)..} P(..x..) != TRUE)
existsDefSpec = existsDef.instantiate().proven()
# [not(forall_{..x.. in S | ..Q(..x..)..} P(..x..) != TRUE) = TRUE] or [not(forall_{..x.. in S| ..Q(..x..)..} P(..x..) != TRUE) = FALSE]
rhsTrue, rhsFalse = existsDefSpec.rhs.deduceInBool().unfold().proven().operands
# exists_{..x.. in S | ..Q(..x..)..} P(..x..) in BOOLEANS assuming [not(forall_{..x.. in S | ..Q(..x..)..} P(..x..) != TRUE) = TRUE]
existsInBoolSpec = rhsTrue.subRightSideInto(Equals(existsDefSpec.lhs, X), X).inBoolViaBooleanEquality().proven({rhsTrue})
# exists_{..x.. | ..Q(..x..)..} P(..x..) in BOOLEANS assuming [not(forall_{..x.. in S | ..Q..(..x..)} P(..x..) != TRUE) = FALSE]
rhsFalse.subRightSideInto(Equals(existsDefSpec.lhs, X), X).inBoolViaBooleanEquality().proven({rhsFalse})
# deduce rhsTrue, rhsFals, existsInBoolSpec all in BOOLEANS
for expr in (rhsTrue, rhsFalse, existsInBoolSpec): expr.deduceInBool()
# forall_{P, ..Q.., S} exists_{..x.. | ..Q(..x..)..} P(..x..) in BOOLEANS
Or(rhsTrue, rhsFalse).deriveCommonConclusion(existsInBoolSpec).generalize((P, Qetc, S)).qed(__file__)
