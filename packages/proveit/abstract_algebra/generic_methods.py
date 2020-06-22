from proveit import USE_DEFAULTS, singleOrCompositeExpression

def apply_commutation_thm(expr, initIdx, finalIdx, binaryThm, leftwardThm, rightwardThm, assumptions=USE_DEFAULTS):
    from proveit.logic import Equals
    from proveit.number import num
    if initIdx is None or finalIdx is None:
        if len(expr.operands) != 2:
            raise IndexError("May only use default 'initIdx' or 'finalIdx' when there are only 2 operands when applying commutation.")
        if initIdx is not finalIdx:
            raise IndexError("Must supply both 'initIdx' and 'finalIdx' or supply neither (allowed when there are only 2 operands) when applying commutation.")
        initIdx, finalIdx = 0, 1 # defaults when there are 2 operands
    if initIdx < 0: initIdx = len(expr.operands)+initIdx # use wrap-around indexing
    if finalIdx < 0: finalIdx = len(expr.operands)+finalIdx # use wrap-around indexing
    if len(expr.operands)==2 and set([initIdx, finalIdx]) == {0, 1}:
        A, B = binaryThm.allInstanceVars()
        return binaryThm.specialize({A:expr.operands[0], B:expr.operands[1]}, assumptions=assumptions)
    if initIdx >= len(expr.operands):
        raise IndexError("'initIdx' out of range")
    if finalIdx >= len(expr.operands):
        raise IndexError("'finalIdx' out of range")
    if initIdx==finalIdx:
        return Equals(expr, expr).prove() # trivial non-commutation
    if initIdx < finalIdx:
        thm = rightwardThm
        l, m, n, A, B, C, D = rightwardThm.allInstanceVars()
        Asub, Bsub, Csub, Dsub = expr.operands[:initIdx], expr.operands[initIdx], expr.operands[initIdx+1:finalIdx+1], expr.operands[finalIdx+1:]
        lSub, mSub, nSub = num(len(Asub)), num(len(Csub)), num(len(Dsub))
    else:
        thm = leftwardThm
        l, m, n, A, B, C, D = thm.allInstanceVars()
        Asub, Bsub, Csub, Dsub = expr.operands[:finalIdx], expr.operands[finalIdx:initIdx], expr.operands[initIdx], expr.operands[initIdx+1:]
        lSub, mSub, nSub = num(len(Asub)), num(len(Bsub)), num(len(Dsub))
    return thm.specialize({l:lSub, m:mSub, n:nSub, A:Asub, B:Bsub, C:Csub, D:Dsub}, assumptions=assumptions)

def apply_association_thm(expr, startIdx, length, thm, assumptions=USE_DEFAULTS):
    from proveit.logic import Equals
    from proveit.number import num
    beg, end = startIdx, startIdx+length
    if beg < 0: beg = len(expr.operands)+beg # use wrap-around indexing
    if not length >= 2:
        raise IndexError ("The 'length' must be 2 or more when applying association.")
    if end > len(expr.operands):
        raise IndexError("'startIdx+length' out of bounds: %d > %d."%(end, len(expr.operands)))
    if beg==0 and end==len(expr.operands):
        # association over the entire range is trivial:
        return Equals(expr, expr).prove() # simply the self equality
    l, m, n, AA, BB, CC = thm.allInstanceVars()
    return thm.specialize({l :num(beg), m:num(end - beg), n: num(len(expr.operands) - end), AA:expr.operands[:beg], BB:expr.operands[beg : end], CC: expr.operands[end :]}, assumptions=assumptions)

def apply_disassociation_thm(expr, idx, thm=None, assumptions=USE_DEFAULTS):
    from proveit.number import num
    if idx < 0: idx = len(expr.operands)+idx # use wrap-around indexing
    if idx >= len(expr.operands):
        raise IndexError("'idx' out of range for disassociation")
    if not isinstance(expr.operands[idx], expr.__class__):
        raise ValueError("Expecting %d index of %s to be grouped (i.e., a nested expression of the same type)"%(idx, str(expr)))
    l, m, n, AA, BB, CC = thm.allInstanceVars()
    length = len(expr.operands[idx].operands)
    return thm.specialize({l:num(idx), m:num(length), n: num(len(expr.operands) - idx - 1), AA:expr.operands[:idx], BB:expr.operands[idx].operands, CC:expr.operands[idx+1:]}, assumptions=assumptions)

def apply_permutation_thm(expr, initIdx, finalIdx, binaryThm, leftwardThm,
                          rightwardThm, assumptions=USE_DEFAULTS):
    '''
    UNDER CONSTRUCTION
    '''
    from proveit.logic import SetEquiv
    # Some initial print statements for testing
    print("Entering apply_permutation_thm.")
    print("    initIdx = {}".format(initIdx))
    print("    finalIdx = {}".format(finalIdx))
    print("    assumptions = {}".format(assumptions))

    # check validity of supplied indices in terms of defaults
    if initIdx is None or finalIdx is None:
        if len(expr.operands) != 2:
            raise IndexError("You may use default 'initIdx' or "
                             "'finalIdx' values when applying "
                             "permutation only if your set or "
                             "set-like object contains exactly 2 "
                             "elements.")
        if initIdx is not finalIdx:
            raise IndexError("When applying permutation, you must "
                             "either supply both 'initIdx' and "
                             "'finalIdx' or supply neither (allowed "
                             "when there are only 2 elements)")
        initIdx, finalIdx = 0, 1  # defaults when there are 2 elements

    # acknowledge any wrap-around indexing; transform for simplicity
    if initIdx < 0: initIdx = len(expr.operands)+initIdx
    if finalIdx < 0: finalIdx = len(expr.operands)+finalIdx

    # check validity of supplied index values
    if initIdx >= len(expr.operands):
        raise IndexError("'initIdx' = {0} is out of range. Should "
                         "have 0 ≤ initIdx ≤ {1}.".
                         format(initIdx, len(expr.operands) - 1))
    if finalIdx >= len(expr.operands):
        raise IndexError("'finalIdx' = {0} is out of range. Should "
                         "have 0 ≤ finalIdx ≤ {1}.".
                         format(finalIdx, len(expr.operands) - 1))

    # trivial permutation
    if initIdx==finalIdx:
        return SetEquiv(expr, expr).prove()

    # Set or set-like object with cardinality = 2
    if len(expr.operands)==2 and set([initIdx, finalIdx]) == {0, 1}:
        A, B = binaryThm.allInstanceVars()
        return binaryThm.specialize({A:expr.operands[0], B:expr.operands[1]},
                                    assumptions=assumptions)

    

    return expr

def groupCommutation(expr, initIdx, finalIdx, length, disassociate=True, assumptions=USE_DEFAULTS):
    '''
    Derive a commutation equivalence on a group of multiple operands by
    associating them together first.  If 'dissassociate' is true, the
    group will be disassociated at end. For example, the following call:
    Or(A,B,C,D).groupCommutation(0, 1, length=2,
                                 assumptions=inBool(A,B,C,D))
    essentially goes through the following steps:
    (1) associates 2 elements (i.e. length = 2) starting at index 0 to
        obtain (A V B) V C V D
    (2) removes the element to be commuted to obtain C V D
    (2) inserts the element to be commuted at the desire index to
        obtain C V (A V B) V D
    (3) then disassociates to obtain C V A V B V D
    (4) eventually producing the output:
    {A in Bool, ..., D in Bool} |- (A V B V C V D) = (C V A V B V D)
    '''
    from proveit import TransRelUpdater

    if initIdx < 0: initIdx = len(expr.operands)+initIdx # use wrap-around indexing
    if finalIdx < 0: finalIdx = len(expr.operands)+finalIdx # use wrap-around indexing
    if length==1:
        return expr.commutation(initIdx, finalIdx, assumptions=assumptions)

    eq = TransRelUpdater(expr, assumptions) # for convenience while updating our equation
    expr = eq.update(expr.association(initIdx, initIdx+length, assumptions=assumptions)) # modified 1/13/2020 by wdc
    # expr = eq.update(expr.association(initIdx, length, assumptions=assumptions))
    expr = eq.update(expr.commutation(initIdx, finalIdx, assumptions=assumptions))
    if disassociate:
        expr = eq.update(expr.disassociation(finalIdx, assumptions=assumptions))
    return eq.relation

def groupCommute(expr, initIdx, finalIdx, length, disassociate=True, assumptions=USE_DEFAULTS):
    '''
    Derive a commuted form of the given expr expression on a group of multiple
    operands by associating them together first.
    If 'dissassociate' is true, the group will be disassociated at end.
    '''
    if initIdx < 0: initIdx = len(expr.operands)+initIdx # use wrap-around indexing
    if finalIdx < 0: finalIdx = len(expr.operands)+finalIdx # use wrap-around indexing
    if length==1:
        return expr.commute(initIdx, finalIdx, assumptions=assumptions)

    expr = expr.associate(initIdx, length, assumptions=assumptions)
    expr = expr.commute(initIdx, finalIdx, assumptions=assumptions)
    if disassociate:
        expr = expr.disassociate(finalIdx, assumptions=assumptions)
    return expr

def pairwiseEvaluation(expr, assumptions):
    '''
    Evaluation routine applicable to associative operations in which
    operands at the beginning are paired and evaluated sequentially.
    '''
    from proveit import TransRelUpdater
    # successively evaluate and replace the operation performed on
    # the first two operands

    eq = TransRelUpdater(expr, assumptions) # for convenience while updating our equation

    if len(expr.operands)==2:
        raise ValueError("pairwiseEvaluation may only be used when there are more than 2 operands")
    while len(expr.operands) > 2:
        expr = eq.update(expr.association(0, length=2, assumptions=assumptions))
        expr = eq.update(expr.innerExpr().operands[0].evaluation(assumptions))
    eq.update(expr.evaluation(assumptions=assumptions))
    return eq.relation
