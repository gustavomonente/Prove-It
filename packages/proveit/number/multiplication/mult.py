from proveit import Literal, Operation, USE_DEFAULTS, ProofFailure
from proveit.logic import Equals, InSet
from proveit.number.sets import Integers, Naturals, NaturalsPos, Reals, RealsPos, Complexes
from proveit._common_ import a, b, c, d, l, m, n, v, w, x, y, z, vv, ww, xx, yy, zz, S, A, B, C, D, E, AA, BB, CC, DD, EE

class Mult(Operation):
    # operator of the Mult operation.
    _operator_ = Literal(stringFormat='*', latexFormat=r'\cdot', context=__file__)
    
    def __init__(self, *operands):
        r'''
        Multiply together any number of operands from first operand.
        '''
        Operation.__init__(self, Mult._operator_, operands)
        self.factors = operands
    
    def deduceInNumberSet(self, numberSet, assumptions=USE_DEFAULTS):
        # edited by JML 7/20/19
        from ._theorems_ import multIntClosure, multIntClosureBin, multNatClosure, multNatClosureBin, multNatPosClosure, multNatClosureBin, multRealClosure, multRealClosureBin, multRealPosClosure, multRealPosClosureBin, multComplexClosure, multComplexClosureBin
        from proveit.number import num
        if hasattr(self, 'number_set'):
            numberSet = numberSet.number_set
        bin = False
        if numberSet == Integers:
            if len(self.operands) == 2:
                thm = multIntClosureBin
                bin = True
            else:
                thm = multIntClosure
        elif numberSet == Naturals:
            if len(self.operands) == 2:
                thm = multNatsClosureBin
                bin = True
            else:
                thm = multNatsClosure
        elif numberSet == NaturalsPos:
            if len(self.operands) == 2:
                thm = multNatsPosClosureBin
                bin = True
            else:
                thm = multNatsPosClosure
        elif numberSet == Reals:
            if len(self.operands) == 2:
                thm = multRealClosureBin
                bin = True
            else:
                thm = multRealClosure
        elif numberSet == RealsPos:
            if len(self.operands) == 2:
                thm = multRealsPosClosureBin
                bin = True
            else:
                thm = multRealPosClosure
        elif numberSet == Complexes:
            if len(self.operands) == 2:
                thm = multComplexClosureBin
                bin = True
            else:
                thm = multComplexClosure
        else:
            raise ProofFailure(InSet(self, numberSet), assumptions, "'deduceInNumberSet' not implemented for the %s set"%str(numberSet))
        from proveit._common_ import AA
        # print("thm", thm)
        # print("self in deduce in number set", self)
        # print("self.operands", self.operands)
        if bin:
            return thm.specialize({a:self.operands[0], b:self.operands[1]}, assumptions=assumptions)
        return thm.specialize({m:num(len(self.operands)),AA:self.operands}, assumptions=assumptions)
    
    def notEqual(self, rhs, assumptions=USE_DEFAULTS):
        from ._theorems_ import multNotEqZero
        if rhs == zero:
            return multNotEqZero.specialize({xMulti:self.operands}, assumptions=assumptions)
        raise ProofFailure(Equals(self, zero), assumptions, "'notEqual' only implemented for a right side of zero")
    
    def simplification(self, assumptions=USE_DEFAULTS):
        '''
        For trivial cases, a zero or one factor,
        derive and return this multiplication expression equated with a simplified form.
        '''
        from ._theorems_ import multOneLeft, multOneRight, multOneAny
        from proveit.number import one
        
        try:
            # if it can do an straight-up evaluation, go with that.
            return self.evaluation(assumptions)
        except:
            pass
        
        expr = self
        try:
            oneIdx = self.operands.index(one)
            if len(self.operands)==2:
                if oneIdx==0:
                    return multOneLeft.specialize({x:self.operands[1]}, assumptions=assumptions)
                else:
                    return multOneRight.specialize({x:self.operands[0]}, assumptions=assumptions)
            Afactors = self.operands[:oneIdx]
            Bfactors = self.operands[oneIdx+1:]
            return multOneAny.specialize({m:len(Afactors), n:len(Bfactors), AA:Afactors, BB:Bfactors}, assumptions=assumptions)
        except ValueError:
            pass # no one factor
        raise ValueError('Only trivial simplification is implemented (zero or one factors)')

    def simplified(self, assumptions=USE_DEFAULTS):
        '''
        For trivial cases, a zero or one factor,
        derive this multiplication expression equated with a simplified form
        and return the simplified form.
        Assumptions may be necessary to deduce necessary conditions for the simplification.
        '''
        return self.simplification(assumptions).rhs

    def evaluation(self, assumptions=USE_DEFAULTS):
        '''
        Derive and return this multiplication expression equated with an irreducible value.
        Handle the trivial case of a zero factor or use the default evaluation.
        '''
        from ._theorems_ import multZeroLeft, multZeroRight, multZeroAny
        from proveit.number import zero
        try:
            zeroIdx = self.operands.index(zero)
            if len(self.operands)==2:
                if zeroIdx==0:
                    return multZeroLeft.specialize({x:self.operands[1]}, assumptions=assumptions)
                else:
                    return multZeroRight.specialize({x:self.operands[0]}, assumptions=assumptions)
            Afactors = self.operands[:zeroIdx]
            Bfactors = self.operands[zeroIdx+1:]
            return multZeroAny.specialize({m:len(Afactors), n:len(Bfactors), AA:Afactors, BB:Bfactors}, assumptions=assumptions)
        except ValueError:
            # use the default if zero is not one of the factors:
            return Operation.evaluation(self, assumptions)
                
    def concludeMultDef(self, expr, assumptions=USE_DEFAULTS):
        '''
        created on 7/25/19 by JML
        given the addition of the same thing, return the equality of the multiplication:
        c + c + c = 3c
        '''
        from ._axioms_ import multDef
        from proveit.number import num, Add
        if not isinstance(expr, Add):
            raise ValueError("Expecting expression to be addition")
        for operand in expr.operands:
            if self.operands[1] != operand:
                raise ValueError("Expecting inputs to be equal to each other.")
        return multDef.specialize({m:self.operands[0], AA:expr.operands, x: self.operands[1]}, assumptions=assumptions)
    
    def commute(self, idx1, idx2, assumptions=USE_DEFAULTS):
        from ._theorems_ import commutation, swap
        if idx1 > idx2: 
            return self.commute(idx2, idx1, assumptions) # put the lesser index first
        if idx1==idx2:
            return Equals(self, self).prove() # trivial case
        if not (0 <= idx1 <= len(self.operands)) or not (0 <= idx2 <= len(self.operands)):
            raise ValueError("Index out of range")
        if len(self.operands)==2:
            # use binary commutation
            return commutation.specialize({x:self.operands[0], y:self.operands[1]}, assumptions=assumptions)
        # more general commutation (using swap)
        Afactors = self.operands[:idx1]
        Bfactor = self.operands[idx1]
        Cfactors = self.operands[idx1+1:idx2]
        Dfactor = self.operands[idx2]
        Efactors = self.operands[idx2+1:]
        return swap.specialize({l:len(Afactors), m:len(Cfactors), n:len(Efactors), AA:Afactors, B:Bfactor, CC:Cfactors, D:Dfactor, EE:Efactors}, assumptions=assumptions)

    def group(self, startIdx=None, endIdx=None, assumptions=USE_DEFAULTS):
        '''
        Group together (associate as a sub-product wrapped in parenthesis)
        consecutive operands, self.operands[startIdx:endIdx].
        Returns the equality that equates self to this new version.
        Give any assumptions necessary to prove that the operands are in 
        Complexes so that the commutation theorem is applicable.
        '''
        from ._theorems_ import group
        xSub = self.operands[:startIdx] if startIdx is not None else []
        ySub = self.operands[startIdx:endIdx]
        zSub = self.operands[endIdx:] if endIdx is not None else []
        if len(ySub)==0 or len(ySub)==1:
            # don't bother grouping a single (or no) item
            return Equals(self, self).prove() # just return the self identity
        if len(xSub)==0 and len(zSub)==0:
            # don't bother grouping the entire thing
            return Equals(self, self).prove() # just return the self identity            
        print(xSub, ySub, zSub)
        return group.specialize({l:len(xSub), m:len(ySub), n:len(zSub), AA:xSub, BB:ySub, CC:zSub}, assumptions=assumptions)

    def ungroup(self, idx, assumptions=USE_DEFAULTS):
        '''
        Ungroup (un-associate a sub-product wrapped in parenthesis)
        an operand, self.operands[idx].
        Returns the equality that equates self to this new version.
        Give any assumptions necessary to prove that the operands are in 
        Complexes so that the commutation theorem is applicable.
        '''
        if not isinstance(self.operands[idx], Mult):  
            raise ValueError("Selected term is not a Mult expression")

        from ._theorems_ import group
        xSub = self.operands[:idx] if idx is not None else []
        ySub = self.operands[idx].operands
        zSub = self.operands[idx+1:] if idx is not None else []
        return group.specialize({l:len(xSub), m:len(ySub), n:len(zSub), AA:xSub, BB:ySub, CC:zSub}, assumptions=assumptions).deriveReversed(assumptions=assumptions)

    def groupCommute(self, startIdx1=None, endIdx1=None, startIdx2=None, endIdx2=None, assumptions=USE_DEFAULTS):
        '''
        Commute self.operands[startIdx1:endIdx1] with self.operands[startIdx2:endIdx2].  
        The default, if no indices are provided, is to commute the first operand with the rest
        (convenient especially when there are just two operands).
        Returns the equality that equates self to this new version.
        Give any assumptions necessary to prove that the operands are in 
        Complexes so that the commutation theorem is applicable.
        '''
        if startIdx1 is None and endIdx1 is None and startIdx2 is None and endIdx2 is None:
            stattIdx1, endIdx1, startIdx2, endIdx2 = 0, 1, 1, None
        nOperands = len(self.operands)
        start1, stop1, _ = slice(startIdx1, endIdx1).indices(nOperands)
        start2, stop2, _ = slice(startIdx2, endIdx2).indices(nOperands)
        if start1  > start2:
            # swap 1 and 2 so that 1 comes first
            start1, stop1, start2, stop2 = start2, stop2, start1, stop1
        if stop1 > start2:
            raise ValueError("Cannot commute overlapping sets of operands")
        expr = self
        expr = expr.group(start2, stop2, assumptions=assumptions).rhs
        Equals(self, expr).prove(assumptions=assumptions)
        expr = expr.group(start1, stop1, assumptions=assumptions).rhs
        Equals(self, expr).prove(assumptions=assumptions)
        idx1 = start1
        idx2 = start2 - (stop1-start1)+1
        expr = expr.commute(idx1, idx2, assumptions=assumptions).rhs
        Equals(self, expr).prove(assumptions=assumptions)
        if isinstance(expr.operands[idx1], Mult):
            expr = expr.ungroup(idx1, assumptions=assumptions).rhs
            Equals(self, expr).prove(assumptions=assumptions)
        if isinstance(expr.operands[idx1], Mult):
            expr = expr.ungroup(idx2, assumptions=assumptions).rhs
        return Equals(self, expr).prove(assumptions=assumptions)
        
    def index(self, theFactor, alsoReturnNum=False):
        '''
        Return the starting index of theFactor, which may be a single operand,
        a list of consecutive operands, or a Mult expression that represents
        the product of the list of consecutive operands.  If alsoReturnNum is
        True, return a tuple of the index and number of operands for theFactor.
        '''
        if isinstance(theFactor, Mult):
            theFactor = theFactor.operands
        if hasattr(theFactor, '__getitem__') and hasattr(theFactor, '__len__'):
            # multiple operands in theFactor
            firstFactor = theFactor[0]
            num = len(theFactor)
            idx = -1
            try:
                while True:
                    idx = self.operands.index(firstFactor, idx+1)
                    if tuple(self.operands[idx:idx+num]) == tuple(theFactor):
                        break # found it all!
            except ValueError:
                raise ValueError("Factor is absent!")
        else:
            num = 1
            try:
                idx = self.operands.index(theFactor)
            except ValueError:
                raise ValueError("Factor is absent!")        
        return (idx, num) if alsoReturnNum else idx
    
    def pull(self, startIdx=None, endIdx=None, direction='left', assumptions=USE_DEFAULTS):
        '''
        Pull a subset of consecutive operands, self.operands[startIdx:endIdx],
        to one side or another. Returns the equality that equates self to 
        this new version.  Give any assumptions necessary to prove that the 
        operands are in Complexes so that the commutation theorem is applicable.
        '''
        if direction == "left": # pull the factor(s) to the left
            if startIdx == 0 or startIdx is None:
                return Equals(self, self).prove(assumptions) # no move necessary
            return self.groupCommute(None, startIdx, startIdx, endIdx, assumptions=assumptions)
        elif direction == "right": # pull the factor(s) to the right
            if endIdx == len(self.operands) or endIdx is None:
                return Equals(self, self).prove(assumptions) # no move necessary
            return self.groupCommute(startIdx, endIdx, endIdx, None, assumptions=assumptions)
        else:
            raise ValueError("Invalid pull direction!  (Acceptable values are \"left\" and \"right\".)")

    def distribute(self, index=None, assumptions=USE_DEFAULTS):
        r'''
        Distribute through the operand at the given index.  
        Returns the equality that equates self to this new version.
        Examples: 
            :math:`a (b + c + a) d = a b d + a c d + a a d`
            :math:`a (b - c) d = a b d - a c d`
            :math:`a \left(\sum_x f(x)\right c = \sum_x a f(x) c`
        Give any assumptions necessary to prove that the operands are in Complexes so that
        the associative and commutation theorems are applicable.            
        '''
        from ._theorems_ import distributeThroughSum, distributeThroughSubtract, distributeThroughSummation
        from proveit.number.division._theorems_ import fracInProd, prodOfFracs
        from proveit.number import Frac, Add, Subtract, Sum
        if index is None and len(self.factors) == 2 and all(isinstance(factor, Frac) for factor in self.factors):
            return prodOfFracs.specialize({x:self.factors[0].numerator, y:self.factors[1].numerator, z:self.factors[0].denominator, w:self.factors[1].denominator}, assumptions=assumptions)
        operand = self.operands[index]
        if isinstance(operand, Add):
            return distributeThroughSum.specialize({xMulti:self.operands[:index], yMulti:self.operands[index].operands, zMulti:self.operands[index+1:]}, assumptions=assumptions)
        elif isinstance(operand, Subtract):
            return distributeThroughSubtract.specialize({wMulti:self.operands[:index], x:self.operands[index].operands[0], y:self.operands[index].operands[1], zMulti:self.operands[index+1:]}, assumptions=assumptions)
        elif isinstance(operand, Frac):            
            eqn = fracInProd.specialize({wMulti:self.operands[:index], x:self.operands[index].operands[0], y:self.operands[index].operands[1], zMulti:self.operands[index+1:]}, assumptions=assumptions)            
            try:
                # see if the numerator can simplify (e.g., with a one factor)
                numerSimplification = eqn.rhs.numerator.simplification(assumptions=assumptions)
                dummyVar = eqn.safeDummyVar()
                return numerSimplification.subRightSideInto(Equals(eqn.lhs, Frac(dummyVar, eqn.rhs.denominator)), dummyVar)
            except:
                return eqn
        elif isinstance(operand, Sum):
            yMultiSub = operand.indices
            Pop, Pop_sub = Operation(P, operand.indices), operand.summand
            S_sub = operand.domain
            xDummy, zDummy = self.safeDummyVars(2)
            spec1 = distributeThroughSummation.specialize({Pop:Pop_sub, S:S_sub, yMulti:yMultiSub, 
                                                           xMulti:Etcetera(MultiVariable(xDummy)), zMulti:Etcetera(MultiVariable(zDummy))}, assumptions=assumptions)
            return spec1.deriveConclusion().specialize({Etcetera(MultiVariable(xDummy)):self.operands[:index], \
                                                        Etcetera(MultiVariable(zDummy)):self.operands[index+1:]}, assumptions=assumptions)
        else:
            raise Exception("Unsupported operand type to distribute over: " + str(operand.__class__))
        
    def factor(self,theFactor,pull="left", groupFactor=True, groupRemainder=False, assumptions=USE_DEFAULTS):
        '''
        Factor out "theFactor" from this product, pulling it either to the "left" or "right".
        If "theFactor" is a product, this may factor out a subset of the operands as
        long as they are next to each other (use commute to make this happen).  If
        there are multiple occurrences, the first occurrence is used.  If groupFactor is
        True and theFactor is a product, these operands are grouped together as a sub-product.
        If groupRemainder is True and there are multiple remaining operands (those not in
        "theFactor"), then these remaining operands are grouped together as a sub-product.
        Returns the equality that equates self to this new version.
        Give any assumptions necessary to prove that the operands are in Complexes so that
        the associative and commutation theorems are applicable.
        '''
        idx, num = self.index(theFactor, alsoReturnNum = True)
        expr = self.pull(idx, idx+num, pull, assumptions)
        if groupFactor and num > 1:
            if pull == 'left':  # use 0:num type of convention like standard pythong
                expr = expr.rhs.group(endIdx=num, assumptions=assumptions)
            elif pull == 'right':
                expr = expr.rhs.group(startIdx=-num, assumptions=assumptions)
        if groupRemainder and len(self.operands)-num > 1:
            # if the factor has been group, effectively there is just 1 factor operand now
            numFactorOperands = 1 if groupFactor else num
            if pull == 'left':           
                expr = expr.rhs.group(startIdx=numFactorOperands, assumptions=assumptions)
            elif pull == 'right':
                expr = expr.rhs.group(endIdx=-numFactorOperands, assumptions=assumptions)
        return Equals(self, expr.rhs)
        
    def combineExponents(self, startIdx=None, endIdx=None, assumptions=USE_DEFAULTS):
        '''
        Equates $a^b a^c$ to $a^{b+c}$, $a^b a^{-c}$ to $a^{b-c}$,  $a^b a$ to $a^{b+1}, $a a^b$ to $a^{1+b},
        or equates $a^c b^c$ to $(a b)^c$.
        '''
        from proveit.number.exponentiation._theorems_ import expOfPositivesProd, intExpOfProd, natsPosExpOfProd
        from proveit.number.exponentiation._theorems_ import sumInExp, diffInExp, diffFracInExp
        from proveit.number.exponentiation._theorems_ import addOneRightInExp, addOneLeftInExp
        from proveit.number.exponentiation._theorems_ import prodOfSqrts
        from proveit.number import Sqrt, Exp, Neg, Frac
        if startIdx is not None or endIdx is not None:
            dummyVar = self.safeDummyVar()
            grouped = self.group(startIdx, endIdx, assumptions=assumptions)
            innerCombineExponents = grouped.rhs.factors[startIdx].combineExponents(assumptions=assumptions)
            combineInGroup = innerCombineExponents.substitution(Mult(*(self.factors[:startIdx] + (dummyVar,) + self.factors[endIdx:])), dummyVar)
            return grouped.applyTransitivity(combineInGroup)
        if all(isinstance(factor, Sqrt) for factor in self.factors):
            # combine the square roots into one square root
            factorBases = [factor.base for factor in self.factors]
            return prodOfSqrts.specialize({xMulti:factorBases}, assumptions=assumptions)
        if len(self.operands) != 2 or not isinstance(self.operands[0], Exp) or not isinstance(self.operands[1], Exp):
            if len(self.operands) == 2 and isinstance(self.operands[0], Exp) and self.operands[0].base == self.operands[1]:
                # Of the form a^b a
                return addOneRightInExp.specialize({a:self.operands[1], b:self.operands[0].exponent}, assumptions=assumptions).deriveReversed(assumptions)
            elif len(self.operands) == 2 and isinstance(self.operands[1], Exp) and self.operands[1].base == self.operands[0]:
                # Of the form a a^b
                return addOneLeftInExp.specialize({a:self.operands[0], b:self.operands[1].exponent}, assumptions=assumptions).deriveReversed(assumptions)
            raise Exception('Combine exponents only implemented for a product of two exponentiated operands (or a simple variant)')
        if self.operands[0].base == self.operands[1].base:
            # Same base: a^b a^c = a^{b+c}$, or something similar
            aSub = self.operands[0].base
            bSub = self.operands[0].exponent
            if isinstance(self.operands[1].exponent, Neg):
                # equate $a^b a^{-c} = a^{b-c}$
                thm = diffInExp
                cSub = self.operands[1].exponent.operand
            elif isinstance(self.operands[1].exponent, Frac) and isinstance(self.operands[1].exponent.numerator, Neg):
                # equate $a^b a^{-c/d} = a^{b-c/d}$
                thm = diffFracInExp
                cSub = self.operands[1].exponent.numerator.operand
                dSub = self.operands[1].exponent.denominator
                return thm.specialize({a:aSub, b:bSub, c:cSub, d:dSub}, assumptions=assumptions)
            else:
                # standard $a^b a^c = a^{b+c}$
                thm = sumInExp
                cSub = self.operands[1].exponent
        elif self.operands[0].exponent == self.operands[1].exponent:
            # Same exponent: equate $a^c b^c = (a b)^c$
            aSub = self.operands[0].base
            bSub = self.operands[1].base
            expSub = self.operands[0].exponent
            try:
                return natsPosExpOfProd.specialize({n:expSub}, assumptions=assumptions).deriveReversed(assumptions).specialize({a:aSub, b:bSub}, assumptions=assumptions)
            except:
                pass
            try:
                return intExpOfProd.specialize({n:expSub}, assumptions=assumptions).deriveReversed(assumptions).specialize({a:aSub, b:bSub}, assumptions=assumptions)
            except:
                return expOfPositivesProd.specialize({c:expSub}, assumptions=assumptions).deriveReversed(assumptions).specialize({a:aSub, b:bSub}, assumptions=assumptions)
        else:
            raise Exception('Product is not in the correct form to combine exponents: ' + str(self))
        return thm.specialize({a:aSub, b:bSub, c:cSub}, assumptions=assumptions).deriveReversed(assumptions)
