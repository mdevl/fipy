#!/usr/bin/env python

## -*-Pyth-*-
 # #############################################################################
 # FiPy - a finite volume PDE solver in Python
 # 
 # FILE: "meshVariable.py"
 #
 # Author: Jonathan Guyer <guyer@nist.gov>
 # Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 # Author: James Warren   <jwarren@nist.gov>
 #   mail: NIST
 #    www: <http://www.ctcms.nist.gov/fipy/>
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
 # 
 # #############################################################################
 ##

__docformat__ = 'restructuredtext'

from fipy.variables.variable import Variable
from fipy.variables.constant import _Constant
from fipy.tools import numerix

class _MeshVariable(Variable):
    """
    .. attention:: This class is abstract. Always create one of its subclasses.
    
    Abstract base class for a `Variable` that is defined on a mesh
    """
    def __init__(self, mesh, name='', value=0., rank=None, elementshape=None, 
                 unit=None, cached=1):
        """
        :Parameters:
          - `mesh`: the mesh that defines the geometry of this `Variable`
          - `name`: the user-readable name of the `Variable`
          - `value`: the initial value
          - `rank`: the rank (number of dimensions) of each element of this 
            `Variable`. Default: 0
          - `elementshape`: the shape of each element of this variable
             Default: `rank * (mesh.getDim(),)`
          - `unit`: the physical units of the `Variable`
        """
        if elementshape is None:
            if rank is not None:
                elementshape = rank * (mesh.getDim(),)
            else:
                elementshape = ()
        else:
            if rank is not None and len(elementshape) != rank:
                raise DimensionError, 'len(elementshape) != rank'
        self.elementshape = elementshape
        
        if value is None:
            array = None
        else:
            array = numerix.zeros(self.elementshape 
                                  + self._getShapeFromMesh(mesh),
                                  numerix.obj2sctype(value))
            if numerix._broadcastShape(array.shape, numerix.shape(value)) is None:
                if not isinstance(value, Variable):
                    value = _Constant(value)
                value = value[..., numerix.newaxis]
                                  
        if isinstance(value, _MeshVariable):
            mesh = mesh or value.mesh
            
        self.mesh = mesh

        Variable.__init__(self, name=name, value=value, unit=unit, 
                          array=array, cached=cached)
                  
    @staticmethod
    def _globalToLocalValue(value, globalNumber, globalIDs):
        if value is not None:
            if not isinstance(value, Variable):
                value = _Constant(value)
            valueShape = value.getShape()
            if valueShape is not () and valueShape[-1] == globalNumber:
                value = value[..., globalIDs]
        return value
        
    def _getGlobalValue(self, localIDs, globalIDs):
        from fipy.tools import parallel
        localValue = self.getValue()
        if parallel.Nproc > 1:
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            if localValue.shape[-1] != 0:
                localValue = localValue[..., localIDs]
            globalIDs = numerix.concatenate(comm.allgather(globalIDs))
            
            globalValue = numerix.empty(localValue.shape[:-1] + (max(globalIDs) + 1,))
            globalValue[..., globalIDs] = numerix.concatenate(comm.allgather(localValue), axis=-1)
            
            return globalValue
        else:
            return localValue

                            
    def getMesh(self):
        return self.mesh
        
    def __str__(self):
        return str(self.getGlobalValue())
        
    def __repr__(self):
        if hasattr(self, 'name') and len(self.name) > 0:
            return self.name
        else:
            s = self.__class__.__name__ + '('
            s += 'value=' + `self.getGlobalValue()`
            s += ')'
            if len(self.name) == 0:
                s = s[:-1] + ', mesh=' + `self.mesh` + s[-1]
            return s
        
    def _getShapeFromMesh(mesh):
        """
        Return the shape of this `MeshVariable` type, given a particular mesh.
        Return `None` if unknown or independent of the mesh.
        """
        return None
    _getShapeFromMesh = staticmethod(_getShapeFromMesh)

    def getShape(self):
        """
            >>> from fipy.meshes.grid2D import Grid2D
            >>> from fipy.variables.cellVariable import CellVariable
            >>> mesh = Grid2D(nx=2, ny=3)
            >>> var = CellVariable(mesh=mesh)
            >>> var.shape
            (6,)
            >>> var.getArithmeticFaceValue().shape
            (17,)
            >>> var.getGrad().shape
            (2, 6)
            >>> var.getFaceGrad().shape
            (2, 17)
        """
        return (Variable.getShape(self) 
                or (self.elementshape + self._getShapeFromMesh(self.getMesh())) 
                or ())

    def _dot(a, b, index):
        """
        Workhorse method to calculate the scalar product
        
        .. raw:: latex
        
           \[ \mathsf{a} \cdot \mathsf{b} \]

        for all but the last index of `a` and `b`. Both `a` and `b` can be of
        arbitrary rank, but at this point, both must be appropriately broadcast
        `array` objects.
        """
        rankA = len(a.shape) - 1
        rankB = len(b.shape) - 1
        if rankA <= 0 or rankB <= 0:
            # if either a or b is scalar, then just do multiplication
            return a[index] * b
        else:
            return numerix.sum(a[index] * b, axis=rankA - 1)
    _dot = staticmethod(_dot)

    def __dot(A, B, operatorClass):
        """
        Workhorse method to return a `_BinaryOperatorVariable` that will
        dynamically perform the mesh-element--by--mesh-element (cell-by-cell,
        face-by-face, etc.) scalar product
        
        .. raw:: latex
        
           \[ \mathsf{A} \cdot \mathsf{B} \]
           
        Both `A` and `B` can be of arbitrary rank, but at this point, both must
        be appropriately broadcast `_MeshVariable` objects.
        """
        rankA = len(A.shape) - 1
        rankB = len(B.shape) - 1
        
        index = (numerix.index_exp[...] + (numerix.newaxis,) * (rankB - 1) 
                 + numerix.index_exp[:])
        opShape = numerix._broadcastShape(A[index].shape, B.shape)
        if rankA > 0:
            opShape = opShape[:rankA-1] + opShape[rankA:]
        
        return A._BinaryOperatorVariable(lambda a,b: _MeshVariable._dot(a, b, index), 
                                         B, 
                                         opShape=opShape,
                                         operatorClass=operatorClass,
                                         canInline=False)
    __dot = staticmethod(__dot)

    def dot(self, other, opShape=None, operatorClass=None):
        """
        Return the mesh-element--by--mesh-element (cell-by-cell, face-by-face,
        etc.) scalar product
        
        .. raw:: latex
        
           \[ \text{self} \cdot \text{other} \]
           
        Both `self` and `other` can be of arbitrary rank, and `other` does not
        need to be a `_MeshVariable`.
        """
        if not isinstance(other, Variable):
            from fipy.variables.constant import _Constant
            other = _Constant(value=other)
        opShape, baseClass, other = self._shapeClassAndOther(opShape=None, operatorClass=None, other=other)
        
        return _MeshVariable.__dot(self, other, self._OperatorVariableClass(baseClass))

    def rdot(self, other, opShape=None, operatorClass=None):
        """
        Return the mesh-element--by--mesh-element (cell-by-cell, face-by-face,
        etc.) scalar product
        
        .. raw:: latex
        
           \[ \text{other} \cdot \text{self} \]
           
        Both `self` and `other` can be of arbitrary rank, and `other` does not
        need to be a `_MeshVariable`.
        """
        if not isinstance(other, Variable):
            from fipy.variables.constant import _Constant
            other = _Constant(value=other)
        opShape, baseClass, other = self._shapeClassAndOther(opShape=None, operatorClass=None, other=other)
        
        return self.__dot(other, self, self._OperatorVariableClass(baseClass))

    def _shapeClassAndOther(self, opShape, operatorClass, other):
        """
        Determine the shape of the result, the base class of the result, and (if
        necessary) a modified form of `other` that is suitable for the
        operation.
        
        By default, returns the result of the generic
        `Variable._shapeClassAndOther()`, but if that fails, and if each
        dimension of `other` is exactly the `Mesh` dimension, do what the user
        probably "meant" and project `other` onto the `Mesh`.
        """
        newOpShape, baseClass, newOther = Variable._shapeClassAndOther(self, opShape, operatorClass, other)
        
        if ((newOpShape is None or baseClass is None)
            and numerix.alltrue(numerix.array(numerix.getShape(other)) == self.getMesh().getDim())):
                newOpShape, baseClass, newOther = Variable._shapeClassAndOther(self, opShape, operatorClass, other[..., numerix.newaxis])

        return (newOpShape, baseClass, newOther)

    def _OperatorVariableClass(self, baseClass=None):
        baseClass = Variable._OperatorVariableClass(self, baseClass=baseClass)
                                     
        class _MeshOperatorVariable(baseClass):
            def __init__(self, op, var, opShape=None, canInline=True,
                         *args, **kwargs):
                mesh = reduce(lambda a, b: a or b, 
                              [getattr(v, "mesh", None) for v in var])
                for shape in [opShape] + [getattr(v, "opShape", None) for v in var]:
                    if shape is not None:
                        opShape = shape
                        break
##                 opShape = reduce(lambda a, b: a or b, 
##                                  [opShape] + [getattr(v, "opShape", None) for v in var])
                if opShape is not None:
                    elementshape = opShape[:-1]
                else:
                    elementshape = reduce(lambda a, b: a or b, 
                                          [getattr(v, "elementshape", None) for v in var])

                baseClass.__init__(self, mesh=mesh, op=op, var=var, 
                                   opShape=opShape, canInline=canInline,
                                   elementshape=elementshape,
                                   *args, **kwargs)
                                 
            def getRank(self):
                return len(self.opShape) - 1
                
        return _MeshOperatorVariable
                          
    def getRank(self):
        return len(self.shape) - 1
        
    def setValue(self, value, unit = None, where = None):
        if where is not None:
            shape = numerix.getShape(where)
            if shape != self.shape \
              and shape == self._getShapeFromMesh(mesh=self.getMesh()):
                for dim in self.elementshape:
                    where = numerix.repeat(where[numerix.newaxis, ...], repeats=dim, axis=0)
        
        return Variable.setValue(self, value=value, unit=unit, where=where)

    def _axisClass(self, axis):
        """
        if we operate along the mesh elements, then this is no longer a
        `_MeshVariable`, otherwise we get back a `_MeshVariable` of the same
        class, but lower rank.
        """
        if axis is None or axis == len(self.shape) or axis == -1:
            return Variable._OperatorVariableClass(self, baseClass=Variable)
        else:
            return self._OperatorVariableClass()

    def _getitemClass(self, index):
        indexshape = numerix._indexShape(index=index, arrayShape=self.shape)
        if (len(indexshape) > 0
            and indexshape[-1] == self.shape[-1]):
            return self._OperatorVariableClass()
        else:
            return Variable._OperatorVariableClass(self, baseClass=Variable)
        
    def __getstate__(self):
        """
        Used internally to collect the necessary information to ``pickle`` the 
        `_MeshVariable` to persistent storage.
        """
        return {
            'mesh': self.mesh,
            'name': self.name,
            'value': self.getValue(),
            'unit': self.getUnit(),
        }


def _testDot(self):
    """
        >>> from fipy import *
        >>> mesh = Grid2D(nx=2, ny=3)

        >>> s1 = CellVariable(mesh=mesh, value=2)
        >>> s2 = CellVariable(mesh=mesh, value=3)

        >>> v1 = CellVariable(mesh=mesh, rank=1, 
        ...                   value=array([2,3])[..., newaxis])
        >>> v2 = CellVariable(mesh=mesh, rank=1, 
        ...                   value=array([3,4])[..., newaxis])
        
        >>> t21 = CellVariable(mesh=mesh, rank=2, 
        ...                    value=array([[2, 3],
        ...                                 [4, 5]])[..., newaxis])
        >>> t22 = CellVariable(mesh=mesh, rank=2, 
        ...                    value=array([[3, 4],
        ...                                 [5, 6]])[..., newaxis])

        >>> t31 = CellVariable(mesh=mesh, rank=3, 
        ...                    value=array([[[3, 4],
        ...                                  [5, 6]],
        ...                                 [[5, 6],
        ...                                  [7, 8]]])[..., newaxis])
        >>> t32 = CellVariable(mesh=mesh, rank=3, 
        ...                    value=array([[[2, 3],
        ...                                  [4, 5]],
        ...                                 [[4, 5],
        ...                                  [6, 7]]])[..., newaxis])

        >>> def P(a):
        ...     print a[...,0], a.shape
        
        >>> P(v1.dot(v2))
        18 (6,)
        >>> P(v1.dot(t22))
        [21 26] (2, 6)
        >>> P(v1.dot(t31))
        [[21 26]
         [31 36]] (2, 2, 6)
        
        >>> P(t21.dot(v1))
        [13 23] (2, 6)
        >>> P(t21.dot(t22))
        [[21 26]
         [37 46]] (2, 2, 6)
        >>> P(t21.dot(t31))
        [[[21 26]
          [31 36]]
        <BLANKLINE>
         [[37 46]
          [55 64]]] (2, 2, 2, 6)
          
        >>> P(t31.dot(v1))
        [[18 28]
         [28 38]] (2, 2, 6)
        >>> P(t31.dot(t21))
        [[[22 29]
          [34 45]]
        <BLANKLINE>
         [[34 45]
          [46 61]]] (2, 2, 2, 6)
        >>> P(t31.dot(t32))
        [[[[22 29]
           [36 43]]
        <BLANKLINE>
          [[34 45]
           [56 67]]]
        <BLANKLINE>
        <BLANKLINE>
         [[[34 45]
           [56 67]]
        <BLANKLINE>
          [[46 61]
           [76 91]]]] (2, 2, 2, 2, 6)
    """
    pass

def _test(): 
    import doctest
    return doctest.testmod()
    
if __name__ == "__main__": 
    _test() 
