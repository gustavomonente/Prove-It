from .mod import Mod
from .mod_abs import ModAbs


# KEEP THE FOLLOWING AT THE BOTTOM OF THIS __init__.py.
#  (Additions may be made above)
# This allows us to import common expression, axioms, and theorems of
# the theory package directly from the package.
import sys
from proveit._core_.theory import TheoryPackage
sys.modules[__name__] = TheoryPackage(__name__, __file__, locals())
