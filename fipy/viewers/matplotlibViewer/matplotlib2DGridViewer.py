#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "matplotlib2DViewer.py"
 #                                    created: 9/14/04 {2:48:25 PM} 
 #                                last update: 5/13/06 {10:01:25 AM} { 2:45:36 PM}
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
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2003-11-10 JEG 1.0 original
 # ###################################################################
 ##
 
__docformat__ = 'restructuredtext'

import pylab

from matplotlibViewer import MatplotlibViewer

class Matplotlib2DGridViewer(MatplotlibViewer):
    """
    Displays an image plot of a 2D `CellVariable` object using Matplotlib_.

    .. _Matplotlib: http://matplotlib.sourceforge.net/
    """


    def __init__(self, vars, limits = None, title = None):
        """
        Creates a `Matplotlib2DGridViewer`.
        
        :Parameters:
          - `vars`: A `CellVariable` object.
          - `limits`: A dictionary with possible keys `'xmin'`, `'xmax'`, 
            `'ymin'`, `'ymax'`, `'datamin'`, `'datamax'`. Any limit set to 
            a (default) value of `None` will autoscale.
          - `title`: displayed at the top of the Viewer window

        """
        MatplotlibViewer.__init__(self, vars = vars, limits = limits, title = title)

        self.image = pylab.imshow(self._getData(),
                                  extent=(self._getLimit('xmin'), self._getLimit('xmax'), 
                                          self._getLimit('ymin'), self._getLimit('ymax')),
                                  vmin=self._getLimit('datamin'),
                                  vmax=self._getLimit('datamax'))
                                          
        pylab.title(self.vars[0].getName())

        # colorbar will not automatically update
        # http://sourceforge.net/mailarchive/forum.php?thread_id=10159140&forum_id=33405
        pylab.colorbar()

    def _getLimit(self, key):
        limit = MatplotlibViewer._getLimit(self, key)
        if limit is None:
            if key == 'xmin' or key == 'ymin':
                limit = 0
            elif key == 'xmax':
                limit = float(self.vars[0].getMesh().getPhysicalShape()[0])
            elif key == 'ymax':
                limit = float(self.vars[0].getMesh().getPhysicalShape()[1])
        return limit
        
    def _getSuitableVars(self, vars):
##         from fipy.viewers import MeshDimensionError
##         raise MeshDimensionError, "I'm just being pissy"
        from fipy.meshes.numMesh.uniformGrid2D import UniformGrid2D
        from fipy.variables.cellVariable import CellVariable
        vars = [var for var in MatplotlibViewer._getSuitableVars(self, vars) \
          if (isinstance(var.getMesh(), UniformGrid2D) and isinstance(var, CellVariable))]
        if len(vars) == 0:
            from fipy.viewers import MeshDimensionError
            raise MeshDimensionError, "The mesh must be a UniformGrid2D instance"
        # this viewer can only display one variable
        return [vars[0]]
        
    def _getData(self):
        from fipy.tools.numerix import array, reshape
        return reshape(array(self.vars[0]), self.vars[0].getMesh().getShape())
    
    def _plot(self):
        self.image.set_data(self._getData())

        