from proveit import defaults, Literal, Operation, ProofFailure, USE_DEFAULTS
# from proveit.number.sets import Integers, Reals
from proveit._common_ import a, b

class Mod(Operation):
    # operator of the Mod operation.
    _operator_ = Literal(stringFormat='mod ', latexFormat=r'~\textup{mod}~',
                         context=__file__)
    
    def __init__(self, dividend, divisor):
        Operation.__init__(self, Mod._operator_, (dividend, divisor))
        self.dividend = self.operands[0]
        self.divisor = self.operands[1]
    
    # def deduceInInterval(self, assumptions=frozenset()):
    #     from ._theorems_ import modInInterval, modInIntervalCO
    #     from numberSets import deduceInIntegers, deduceInReals
    #     try:
    #         # if the operands are integers, then we can deduce that
    #         # a mod b is in 0..(b-1)
    #         deduceInIntegers(self.operands, assumptions)
    #         return modInInterval.instantiate(
    #                 {a:self.dividend, b:self.divisor}).checked(assumptions)
    #     except:
    #         # if the operands are reals, then we can deduce that a mod b is in [0, b)
    #         deduceInReals(self.operands, assumptions)
    #         return modInIntervalCO.instantiate({a:self.dividend, b:self.divisor}).checked(assumptions)

    def deduceInInterval(self, assumptions=USE_DEFAULTS):
        from ._theorems_ import modInInterval, modInIntervalCO
        # from numberSets import deduceInIntegers, deduceInReals
        try:
            # if the operands are integers, then we can deduce that
            # a mod b is an integer in the set {0,1,...,(b-1)}
            return modInInterval.instantiate(
                    {a:self.dividend, b:self.divisor}, assumptions=assumptions)
        except:
            # if the operands are reals, then we can deduce that
            # a mod b is in half-open real interval [0, b)
            return modInIntervalCO.instantiate(
                    {a:self.dividend, b:self.divisor}, assumptions=assumptions)

    def deduceInNumberSet(self, number_set, assumptions=USE_DEFAULTS):
        '''
        Given a number set number_set (such as Integers, Reals, etc),
        attempt to prove that the given Mod expression is in that number
        set using the appropriate closure theorem.
        '''
        from proveit.logic import InSet
        from proveit.number.modular._theorems_ import (
                  modIntClosure, modIntToNatsClosure, modRealClosure)
        from proveit.number import Integers, Naturals, Reals

        # among other things, make sure non-existent assumptions
        # manifest as empty tuple () rather than None
        assumptions = defaults.checkedAssumptions(assumptions)

        if number_set == Integers:
            return modIntClosure.instantiate(
                    {a:self.dividend, b:self.divisor}, assumptions=assumptions)

        if number_set == Naturals:
            return modIntToNatsClosure.instantiate(
                    {a:self.dividend, b:self.divisor}, assumptions=assumptions)

        if number_set == Reals:
            return modRealClosure.instantiate(
                    {a:self.dividend, b:self.divisor}, assumptions=assumptions)

        msg = ("'Mod.deduceInNumberSet()' not implemented for "
               "the %s set"%str(number_set))
        raise ProofFailure(InSet(self, number_set), assumptions, msg)
