from proveit import Operation, Literal, USE_DEFAULTS, ProofFailure
from proveit.logic.irreducible_value import IrreducibleValue
from proveit._common_ import A, P

class BooleanSet(Literal):
    def __init__(self):
        Literal.__init__(self, stringFormat='BOOLEANS', latexFormat=r'\mathbb{B}')
    
    def membershipSideEffects(self, element, knownTruth):
        '''
        Yield side-effect methods to try when the element is proven to be in the set of Booleans
        by calling 'inBoolSideEffects' on the element if it has such a method.
        '''
        if hasattr(element, 'inBoolSideEffects'):
            for sideEffect in element.inBoolSideEffects(knownTruth):
                yield sideEffect

    def membershipEquivalence(self, element, assumptions=USE_DEFAULTS):
        '''
        Deduce [(element in Booleans) = [(element = TRUE) or (element = FALSE)].
        '''
        from ._theorems_ import inBoolEquiv
        return inBoolEquiv.specialize({A:element})

    def nonMembershipEquivalence(self, element, assumptions=USE_DEFAULTS):
        '''
        Deduce [(element not in Booleans) = [(element != TRUE) and (element != FALSE)].
        '''
        from ._theorems_ import notInBoolEquiv
        return notInBoolEquiv.specialize({A:element})

    def unfoldMembership(self, element, assumptions=USE_DEFAULTS):
        '''
        From inBool(Element), derive and return [element or not(element)].
        '''
        from ._theorems_ import unfoldInBool
        #  [(element = TRUE) or (element = FALSE)] assuming inBool(element)
        return unfoldInBool.specialize({A:element}).deriveConclusion().checked({inBool(element)})
    
    def deduceMembership(self, element, assumptions=USE_DEFAULTS):
        '''
        Try to deduce that the given element is in the set of Booleans under the given assumptions.
        '''   
        from ._theorems_ import inBoolIfTrue, inBoolIfFalse
        if hasattr(element, 'deduceInBool'):
            return element.deduceInBool(assumptions=assumptions)
        try:
            element.prove(assumptions=assumptions, automation=False)
            return inBoolIfTrue.specialize({A:element}, assumptions=assumptions)
        except:
            pass
        try:
            element.disprove(assumptions=assumptions, automation=False)
            return inBoolIfFalse.specialize({A:element}, assumptions=assumptions)
        except:
            pass
        raise ProofFailure(inBool(element), assumptions, str(element) + ' not proven to be equal to TRUE or FALSE.')

    def evaluateForall(self, forallStmt, assumptions):
        '''
        Given a forall statement over the BOOLEANS domain, evaluate to TRUE or FALSE
        if possible.
        '''        
        from proveit.logic import Forall, Equals, EvaluationError
        from ._theorems_ import falseEqFalse, trueEqTrue 
        from ._theorems_ import forallBoolEvalTrue, forallBoolEvalFalseViaTF, forallBoolEvalFalseViaFF, forallBoolEvalFalseViaFT
        from ._common_ import TRUE, FALSE, Booleans
        from conjunction import compose
        assert(isinstance(forallStmt, Forall)), "May only apply evaluateForall method of BOOLEANS to a forall statement"
        assert(forallStmt.domain == Booleans), "May only apply evaluateForall method of BOOLEANS to a forall statement with the BOOLEANS domain"
        assert(len(forallStmt.instanceVars) == 1), "May only apply evaluateForall method of BOOLEANS to a forall statement with 1 instance variable"
        instanceVar = forallStmt.instanceVars[0]
        instanceExpr = forallStmt.instanceExpr
        P_op = Operation(P, instanceVar)
        trueInstance = instanceExpr.substituted({instanceVar:TRUE})
        falseInstance = instanceExpr.substituted({instanceVar:FALSE})
        if trueInstance == TRUE and falseInstance == FALSE:
            # special case of Forall_{A in BOOLEANS} A
            falseEqFalse # FALSE = FALSE
            trueEqTrue # TRUE = TRUE
            return forallBoolEvalFalseViaTF.specialize({P_op:instanceExpr}).deriveConclusion()
        else:
            # must evaluate for the TRUE and FALSE case separately
            evalTrueInstance = trueInstance.evaluate(assumptions)
            evalFalseInstance = falseInstance.evaluate(assumptions)
            if not isinstance(evalTrueInstance.expr, Equals) or not isinstance(evalFalseInstance.expr, Equals):
                raise EvaluationError('Quantified instances must produce equalities as evaluations')            
            # proper evaluations for both cases (TRUE and FALSE)
            trueCaseVal = evalTrueInstance.rhs
            falseCaseVal = evalFalseInstance.rhs
            if trueCaseVal == TRUE and falseCaseVal == TRUE:
                # both cases are TRUE, so the forall over booleans is TRUE
                compose([evalTrueInstance.deriveViaBooleanEquality(), evalFalseInstance.deriveViaBooleanEquality()], assumptions)
                forallBoolEvalTrue.specialize({P_op:instanceExpr, A:instanceVar})
                return forallBoolEvalTrue.specialize({P_op:instanceExpr, A:instanceVar}, assumptions=assumptions).deriveConclusion(assumptions)
            else:
                # one case is FALSE, so the forall over booleans is FALSE
                compose([evalTrueInstance, evalFalseInstance], assumptions)
                if trueCaseVal == FALSE and falseCaseVal == FALSE:
                    return forallBoolEvalFalseViaFF.specialize({P_op:instanceExpr, A:instanceVar}, assumptions=assumptions).deriveConclusion(assumptions)
                elif trueCaseVal == FALSE and falseCaseVal == TRUE:
                    return forallBoolEvalFalseViaFT.specialize({P_op:instanceExpr, A:instanceVar}, assumptions=assumptions).deriveConclusion(assumptions)
                elif trueCaseVal == TRUE and falseCaseVal == FALSE:
                    return forallBoolEvalFalseViaTF.specialize({P_op:instanceExpr, A:instanceVar}, assumptions=assumptions).deriveConclusion(assumptions)
                else:
                    raise EvaluationError('Quantified instance evaluations must be TRUE or FALSE')         
    
    def unfoldForall(self, forallStmt, assumptions=USE_DEFAULTS):
        '''
        Given forall_{A in Booleans} P(A), derive and return [P(TRUE) and P(FALSE)].
        '''
        from proveit.logic import Forall
        from ._theorems_ import unfoldForallOverBool
        from ._common_ import Booleans
        assert(isinstance(forallStmt, Forall)), "May only apply unfoldForall method of Booleans to a forall statement"
        assert(forallStmt.domain == Booleans), "May only apply unfoldForall method of Booleans to a forall statement with the Booleans domain"
        assert(len(forallStmt.instanceVars) == 1), "May only apply unfoldForall method of Booleans to a forall statement with 1 instance variable"
        return unfoldForallOverBool.specialize({Operation(P, forallStmt.instanceVars[0]): forallStmt.instanceExpr, A:forallStmt.instanceVars[0]}).deriveConclusion(assumptions)

    def foldAsForall(self, forallStmt, assumptions=USE_DEFAULTS):
        '''
        Given forall_{A in Booleans} P(A), conclude and return it from [P(TRUE) and P(FALSE)].
        '''
        from proveit.logic import Forall
        from ._theorems_ import foldForallOverBool
        from ._common_ import Booleans
        assert(isinstance(forallStmt, Forall)), "May only apply foldAsForall method of Booleans to a forall statement"
        assert(forallStmt.domain == Booleans), "May only apply foldAsForall method of Booleans to a forall statement with the Booleans domain"
        assert(len(forallStmt.instanceVars) == 1), "May only apply foldAsForall method of Booleans to a forall statement with 1 instance variable"
        # forall_{A in Booleans} P(A), assuming P(TRUE) and P(FALSE)
        return foldForallOverBool.specialize({Operation(P, forallStmt.instanceVars[0]):forallStmt.instanceExpr}, {A:forallStmt.instanceVars[0]})

class TrueLiteral(Literal, IrreducibleValue):
    def __init__(self):
        Literal.__init__(self, stringFormat='TRUE', latexFormat=r'\top')
    
    def conclude(self, assumptions):
        from ._axioms_ import trueAxiom
        return trueAxiom
    
    def evalEquality(self, other):
        from ._theorems_ import trueEqTrue, trueNotFalse
        from ._common_ import TRUE, FALSE
        if other == TRUE:
            return trueEqTrue.evaluate()
        elif other == FALSE:
            return trueNotFalse.unfold().equateNegatedToFalse()

    def notEqual(self, other):
        from ._theorems_ import trueNotFalse
        from ._common_ import TRUE, FALSE
        if other == FALSE:
            return trueNotFalse
        if other == TRUE:
            raise ProofFailure("Cannot prove TRUE != TRUE since that statement is false")
        raise ProofFailure("Inequality between TRUE and a non-boolean not defined")
        
    def deduceInBool(self, assumptions=USE_DEFAULTS):
        from ._theorems_ import trueInBool
        return trueInBool
        
class FalseLiteral(Literal, IrreducibleValue):
    def __init__(self):
        Literal.__init__(self, stringFormat='FALSE', latexFormat=r'\bot')
    
    def evalEquality(self, other):
        from ._axioms_ import falseNotTrue
        from ._theorems_ import falseEqFalse
        from ._common_ import TRUE, FALSE
        if other == FALSE:
            return falseEqFalse.evaluate()
        elif other == TRUE:
            return falseNotTrue.unfold().equateNegatedToFalse()

    def concludeNegation(self, assumptions):
        from proveit.logic.boolean.negation._theorems_ import notFalse
        return notFalse # the negation of FALSE

    def notEqual(self, other):
        from _.theorems_ import falseNotTrue
        from ._common_ import TRUE, FALSE
        if other == TRUE:
            return falseNotTrue
        if other == FALSE:
            raise ProofFailure("Cannot prove FALSE != FALSE since that statement is false")
        raise ProofFailure("Inequality between FALSE and a non-boolean not defined")

    def deduceInBool(self, assumptions=USE_DEFAULTS):
        from ._theorems_ import falseInBool
        return falseInBool

def inBool(*elements):
    from proveit.logic.set_theory import InSet
    from ._common_ import Booleans
    if len(elements) == 1:
        return InSet(elements[0], Booleans)
    return [InSet(element, Booleans) for element in elements]

try:
    # Import some fundamental axioms and theorems without quantifiers.
    # Fails before running the _axioms_ and _theorems_ notebooks for the first time, but fine after that.
    from ._axioms_ import trueAxiom, boolsDef, falseNotTrue
    from ._theorems_ import trueEqTrue, falseEqFalse, trueNotFalse, trueInBool, falseInBool
except:
    pass
    