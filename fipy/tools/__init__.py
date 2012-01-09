#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "__init__.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  See the file "license.terms" for information on usage and  redistribution
 #  of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 #  
 # ###################################################################
 ##

def _parallelImport():
    try:
        import scipy
    except:
        pass

    from PyTrilinos import Epetra
    from fipy.tools.comms.commWrapper import CommWrapper

    parallel = CommWrapper(Epetra=Epetra)

    if parallel.Nproc > 1:

        try:
            from mpi4py import MPI
            from fipy.tools.comms.mpi4pyCommWrapper import Mpi4pyCommWrapper
            parallel = Mpi4pyCommWrapper(Epetra=Epetra, MPI=MPI)
        except ImportError:
            raise ImportError("Could not import mpi4py. The package mpi4py is a required package if you are using Trilinos in parallel. Try installing using 'easy_install mpi4py'.")

    from fipy.tools.comms.serialCommWrapper import SerialCommWrapper
    return SerialCommWrapper(Epetra=Epetra), parallel

def _getComms():
    from fipy.tools.parser import _parseSolver
    if _parseSolver() in ("trilinos",  "no-pysparse"):
        serial, parallel = _parallelImport()
    elif _parseSolver() is None:
        try:
            serial, parallel = _parallelImport()
        except ImportError:
            from fipy.tools.comms.dummyComm import DummyComm
            serial, parallel = DummyComm(), DummyComm()
    else:
        from fipy.tools.comms.dummyComm import DummyComm
        serial, parallel = DummyComm(), DummyComm()
        
    return serial, parallel
    
serial, parallel = _getComms()

from fipy.tests.doctestPlus import register_skipper

register_skipper(flag="SERIAL",
                 test=lambda: parallel.Nproc == 1,
                 why="more than one processor found",
                 skipWarning=False)

register_skipper(flag="PARALLEL",
                 test=lambda: parallel.Nproc > 1,
                 why="only one processor found",
                 skipWarning=False)

register_skipper(flag="PROCESSOR_0",
                 test=lambda: parallel.procID == 0,
                 why="not running on processor 0",
                 skipWarning=False)

for M in (2, 3):
    for N in range(M):
        register_skipper(flag="PROCESSOR_%d_OF_%d" % (N, M),
                         test=lambda N=N, M=M: parallel.procID == N and parallel.Nproc == M,
                         why="not running on processor %d of %d" % (N, M),
                         skipWarning=False)

import fipy.tools.dump
import fipy.tools.numerix
import fipy.tools.vector
from dimensions.physicalField import PhysicalField
from fipy.tools.numerix import *
from fipy.tools.vitals import Vitals

__all__ = ["serial",
           "parallel",
           "dump",
           "numerix",
           "vector",
           "PhysicalField",
           "Vitals"]
           
import os
if 'FIPY_INCLUDE_NUMERIX_ALL' in os.environ:
    import warnings
    class FiPyDeprecationWarning(DeprectationWarning):
        pass
    warnings.warn("""
The ability to include `numerix` functions in the `fipy` namespace
with the FIPY_INCLUDE_NUMERIX_ALL environment variable will
likely be removed in the future. If needed, the same effect can be 
accomplished with `from fipy.tools.numerix import *`
""", FutureWarning)
    __all__.extend(numerix.__all__)
