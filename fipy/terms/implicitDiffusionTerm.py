#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "implicitDiffusionTerm.py"
 #                                    created: 11/28/03 {10:07:06 AM} 
 #                                last update: 12/7/04 {2:53:08 PM} 
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

__docformat__ = 'restructuredtext'

from fipy.terms.diffusionTerm import DiffusionTerm

class ImplicitDiffusionTerm(DiffusionTerm):
    r"""
    The discretization for the `ImplicitDiffusionTerm` is given by

    .. raw:: latex

       $$ \int_V \nabla \cdot (\Gamma\nabla\phi) dV \simeq \sum_f \Gamma_f
       \frac{\phi_A-\phi_P}{d_{AP}} A_f. $$ The variable $\phi$ is
       evaluated implicitly as part of the solution
       routine.
    """
        
    def _getWeight(self, mesh):
	return {
	    'implicit':{
		'cell 1 diag':    -1, 
		'cell 1 offdiag':  1, 
		'cell 2 diag':    -1, 
		'cell 2 offdiag':  1
	    }
	}
