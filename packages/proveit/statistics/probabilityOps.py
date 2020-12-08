from proveit import Operation, Literal
from proveit._common_ import x, X

pkg = __package__

class Prob(Operation):
    '''
    Updated Sun 1/26/2020 by wdc: updating the __init__ and _formatted
    methods, import statements. deduceInInterval and deduceInReal
    methods untouched.
    '''
    # the literal operator of the Prob operation class
    _operator_ = Literal('PROB', theory=__file__)

    def __init__(self, event, random_variable):
        Operation.__init__(self, Prob._operator_, (event, random_variable))
        self.event = self.operands[0]
        self.random_variable = self.operands[1]
    
    def _formatted(self, formatType, fence=False):
        formattedEvent = self.event.formatted(formatType, fence=False)
        formattedVar = self.random_variable.formatted(formatType, fence=False)
        return 'Pr_{' + formattedVar + '}['+formattedEvent+']'
    
    def deduceInInterval(self):
        from axioms import probBetweenZeroAndOne
        return probBetweenZeroAndOne.instantiate({x:self.random_variable, X:self.event})
    
    def deduceInReal(self):
        from theorems import probInReal
        return probInReal.instantiate({x:self.random_variable, X:self.event})

# PROB = Literal(pkg, 'PROB', operationMaker = lambda operands : Prob(*operands))
