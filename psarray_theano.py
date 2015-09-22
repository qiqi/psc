import numbers
import itertools
import numpy as np
import theano.tensor as T

import psarray

#==============================================================================#
#                                 grid2d class                                 #
#==============================================================================#

class grid2d_theano(object):
    def __init__(self, nx, ny):
        assert nx > 0
        assert ny > 0

        self._nx = int(nx)
        self._ny = int(ny)

        self._i = T.lmatrix()
        self._j = T.lmatrix()

    @property
    def nx(self):
        return self._nx

    @property
    def ny(self):
        return self._ny

    # -------------------------------------------------------------------- #
    #                           array constructors                         #
    # -------------------------------------------------------------------- #

    def array(self, init_func):
        return psarray_theano(self, init_func)

    def empty(self, shape):
        a = self.array(None)
        a._data = np.empty((self.nx, self.ny) + tuple(shape))
        return a

    def zeros(self, shape):
        a = self.array(None)
        a._data = np.zeros((self.nx, self.ny) + tuple(shape))
        return a

    def ones(self, shape):
        a = self.array(None)
        a._data = np.ones((self.nx, self.ny) + tuple(shape))
        return a

    def random(self, shape=()):
        a = self.array(None)
        a._data = np.random.random((self.nx, self.ny) + tuple(shape))
        return a

    # -------------------------------------------------------------------- #
    #                            global operations                         #
    # -------------------------------------------------------------------- #

    def sum(self, a):
        assert a.grid == self
        return a._data.sum(axis=(0,1))

#==============================================================================#
#                                 psarray class                                #
#==============================================================================#

def from_numpy(a):
    psarray_theano(a.grid, 

class psarray_theano(object):
    def __init__(self, grid, init_func):
        self.grid = grid
        assert grid.nx > 0
        assert grid.ny > 0

        if isinstance(init, psarray.psarray):
            tensor_dim = init.ndim + 2
            self._data = T.TensorType('float64', (False,) * tensor_dim)()
        elif init:
            raw_data = np.array(init(grid._i, grid._j))
            self._shape = raw_data.shape

            # rollaxis
            while raw_data.ndim > 0:
                new_shape = raw_data.shape[1:]
                new_data = []
                for i in itertools.product(*(range(n) for n in new_shape)):
                    ds = raw_data[(slice(None),) + i]
                    ds = [T.shape_padright(d.astype('float64')) for d in ds]
                    new_data.append(T.concatenate(ds, axis=-1))
                raw_data = np.array(new_data).reshape(new_shape)

            self._data = new_data[0]

    # -------------------------------------------------------------------- #
    #                           size information                           #
    # -------------------------------------------------------------------- #

    @property
    def shape(self):
        return self._shape

    @property
    def size(self):
        return np.prod(self._shape)

    @property
    def ndim(self):
        return len(self._shape)

    @property
    def nx(self):
        return self.grid.nx

    @property
    def ny(self):
        return self.grid.ny

    # -------------------------------------------------------------------- #
    #                         access spatial neighbors                     #
    # -------------------------------------------------------------------- #

    @property
    def x_p(self):
        y = self.grid.array(None)
        y._data = T.roll(self._data, -1, axis=0)
        return y

    @property
    def x_m(self):
        y = self.grid.array(None)
        y._data = T.roll(self._data, +1, axis=0)
        return y

    @property
    def y_p(self):
        y = self.grid.array(None)
        y._data = T.roll(self._data, -1, axis=1)
        return y

    @property
    def y_m(self):
        y = self.grid.array(None)
        y._data = T.roll(self._data, +1, axis=1)
        return y

    # -------------------------------------------------------------------- #
    #                         algorithmic operations                       #
    # -------------------------------------------------------------------- #

    def __neg__(self):
        y = self.grid.array(None)
        y._data = -self._data
        return y

    def __radd__(self, a):
        return self.__add__(a)

    def __add__(self, a):
        if isinstance(a, psarray_theano):
            assert a.nx == self.nx and a.ny == self.ny
            y = self.grid.array(None)
            y._data = self._data + a._data
        else:
            y = self.grid.array(None)
            y._data = self._data + a
        return y

    def __rsub__(self, a):
        return a + (-self)

    def __sub__(self, a):
        return self + (-a)

    def __rmul__(self, a):
        return self.__mul__(a)

    def __mul__(self, a):
        if isinstance(a, psarray_theano):
            assert a.nx == self.nx and a.ny == self.ny
            y = self.grid.array(None)
            y._data = self._data * a._data
        else:
            y = self.grid.array(None)
            y._data = self._data * a
        return y

    def __div__(self, a):
        return self.__truediv__(a)

    def __truediv__(self, a):
        if isinstance(a, psarray_theano):
            assert a.nx == self.nx and a.ny == self.ny
            y = self.grid.array(None)
            y._data = self._data / a._data
        else:
            y = self.grid.array(None)
            y._data = self._data / a
        return y

    def __pow__(self, a):
        if isinstance(a, psarray_theano):
            assert a.nx == self.nx and a.ny == self.ny
            y = self.grid.array(None)
            y._data = self._data ** a._data
        else:
            y = self.grid.array(None)
            y._data = self._data ** a
        return y

    # -------------------------------------------------------------------- #
    #                               indexing                               #
    # -------------------------------------------------------------------- #

    def _data_index_(self, ind):
        if not isinstance(ind, tuple):
            ind = (ind,)
        ind = (slice(None),) * 2 + ind
        return ind

    def __getitem__(self, ind):
        ind = self._data_index_(ind)
        a = self.grid.array(None)
        a._data = self._data[ind]
        return a
        
    def __setitem__(self, ind, a):
        ind = self._data_index_(ind)
        if isinstance(a, psarray_theano):
            assert a.nx == self.nx and a.ny == self.ny
            self._data[ind] = a._data
        elif isinstance(a, numbers.Number):
            self._data[ind] = a
        elif isinstance(a, np.ndarray):
            self._data[ind] = a

    # -------------------------------------------------------------------- #
    #                           input / output                             #
    # -------------------------------------------------------------------- #

    def save(self, filename):
        np.save(filename, self._data)


#==============================================================================#
#                                 array operations                             #
#==============================================================================#

def empty_like(a):
    b = a.grid.array(None)
    b._data = np.empty((a.nx, a.ny) + a.shape)
    return b

def exp(x):
    if isinstance(x, psarray_theano):
        y = x.grid.array(None)
        y._data = np.exp(x._data)
        return y
    else:
        return np.exp(x)

def sqrt(x):
    if isinstance(x, psarray):
        y = x.grid.array(None)
        y._data = np.sqrt(x._data)
        return y
    else:
        return np.sqrt(x)

def sin(x):
    y = x.grid.array(None)
    y._data = np.sin(x._data)
    return y

def cos(x):
    y = x.grid.array(None)
    y._data = np.cos(x._data)
    return y

def log(x):
    y = x.grid.array(None)
    y._data = np.log(x._data)
    return y

def copy(x):
    y = x.grid.array(None)
    y._data = x._data
    return y

def ravel(x):
    y = x.grid.array(None)
    y._data = x._data.reshape(y.shape + (y.size,))
    return y

def transpose(x, axes=None):
    y = x.grid.array(None)
    if axes is None:
        axes = reversed(tuple(range(x.ndim)))
    y._data = x._data.transpose((0, 1) + tuple(i+2 for i in axes))
    return y


#==============================================================================#
#                                 compilation                                  #
#==============================================================================#

class psc_compile_theano(object):
    def __init__(self, function):
        self._function = function
        self._compiled_function = None

    def __call__(self, u, *args, **argv):
        assert isinstance(u, psarray.psarray)
        if not self._compiled_function:
            u_theano = psarray_theano(u)
            ret = self._function(u_theano, *args, **argv)
            self._compiled_function = theano.function([u_theano], ret)
        ret = u.grid.array(None)
        ret._data = self._compiled_function(u._data)
        return ret


if __name__ == '__main__':
    G = grid2d(2,2)
    a = G.array(lambda i,j : [[i,j], [i,j]])
    b = exp(a)

