# miscellaneous stuff that's in development

# Load a dynamic library
# Global = Use a global name space so inter-library dependencies can be resolved
def load_lib (name, Global=False):
# {{{
#  from pygeode import libpath, pluginpath
  from ctypes.util import find_library
  from ctypes import CDLL, RTLD_GLOBAL, RTLD_LOCAL
  from os.path import exists, join, sep
  import os

#  print "debug: requested library is '%s'"%name

  import pygeode, pygeode.plugins

  # First try resolving it to a pygeode-specific library
  # Local (uninstalled) library
  if not exists(name):
    # Plugin?
    if name.startswith("plugins/"):
      for libpath in pygeode.plugins.__path__:
        libname = libpath + sep + name.strip("plugins/").replace("/",sep)
        if exists(libname): name = libname
    # Core library?
    else:
      for libpath in pygeode.__path__:
        libname = libpath + sep + name
        if exists(libname): name = libname

#  # Local (plugin) library
#  if not exists(name):
#    libname = pluginpath+"/"+name
#    if exists(libname): name = libname
  # Local (installed) library
  if not exists(name):
    libname = "/usr/local/lib/pygeode/" + name
    if exists(libname): name = libname
  # 'Official' (installed) library
  if not exists(name):
    libname = "/usr/lib/pygeode/" + name
    if exists(libname): name = libname

  # Try using LD_LIBRARY_PATH???
  # Why doesn't ctypes respect LD_LIBRARY_PATH?  Why must we force it like this??
  if not exists(name):
    dir=os.environ.get('LD_LIBRARY_PATH','')
    libname = dir + '/lib' + name + '.so'
    if exists(libname): name = libname

  # Fail all else, try resolving it to an installed library
  if not exists(name):
    libname = find_library(name)
    assert libname is not None, "can't find library '%s'"%name
    name = libname

  # If we have a library in the current directory, prepend it with './'
  if exists(name) and sep not in name: name = '.' + sep + name


#  print "debug: loading shared library %s"%name

  mode = RTLD_GLOBAL if Global==True else RTLD_LOCAL
  return CDLL(name, mode=mode)
# }}}
# Some compiled code used by this python module
libmisc = load_lib("libtools.so")

# C Pointer to a numpy array
def point (x):
# {{{
  from ctypes import c_void_p
  import numpy as np
  assert x is np.ascontiguousarray(x)
  return c_void_p(x.ctypes.data)
# }}}

# Get the best dtype to use for the given Vars (or numpy arrays)
def common_dtype (vars):
# {{{
  import numpy as np
  from pygeode.var import Var
  import re

  # Can work on PyGeode variables, numpy arrays, lists, tuples, or scalars
  dtypes = []
  for v in vars:
    if isinstance(v, (Var,np.ndarray)):
      dtypes.append(v.dtype)
    elif isinstance(v, (list,tuple)):
      dtypes.append(np.asarray(v).dtype)
    else:
      dtypes.append(np.asarray([v]).dtype)
#    raise Exception ("unrecognized type '%s'"%type(v))

  # Unfortunately, find_common_type is not available in older versions of numpy :(
  try:
    return np.find_common_type(dtypes, [])
  except AttributeError:
    from warnings import warn
    warn ("numpy.find_common_type not supported in this version of numpy.  Using an alternative method.")

  # Create some empty arrays of the given types, and see what happens
  # when we combine them together
  arrays = [np.empty(0,dtype=d) for d in dtypes]
  return sum(arrays,arrays[0]).dtype


# Common elements of a dictionary
# Used mainly for the optional attributes (.atts) of a var, to copy any consistent values to the output
def common_dict (*dicts):
  if len(dicts) == 1 and islist(dicts[0]): dicts = dicts[0]
  # Merge it all into a single dictionary
  d = dict([(k,v) for x in dicts for k,v in x.iteritems()])
  # Check for consistency (remove keys which have multiple values)
  for k,v in d.items():
    for x in dicts:
      if k in x:
        t = (x[k] != v)
        # should we use '__iter__' instead, to exclude strings?
        if (hasattr(t, '__len__') and  any(t)) or (not hasattr(t, '__len__') and t): 
          del d[k]
          break
  return d
# }}}

def whichaxis(axes, id):
# {{{
  '''
  Returns the index of the axis in the list of axes provided that is identified
  by id.

  Parameters
  ----------
  axes : list of :class:'Axis' instances
  id : string, :class:`Axis` class, or int
      The search criteria for finding the class.

  Returns
  -------
  The index of the matching Axis. Raises ``KeyError`` if there is no match.

  See Also
  --------
  Var.whichaxis
  '''

  from pygeode.axis import Axis
  # Case 1: a string was given
  if isinstance(id, str):
    for i,a in enumerate(axes):
      if a.has_alias(id): return i

  # Degenerate case: an integer index
  elif isinstance(id, int) and 0 <= id < len(axes):
    return id

  # An axis object?
  elif isinstance(id, Axis):
    for i,a in enumerate(axes):
      if a == id: return i

  # Other case: a class was given
  elif issubclass(id, Axis):
    for i,a in enumerate(axes):
      if isinstance(a, id): return i

  raise KeyError, "axis %s not found in %s"%(repr(id),axes)
# }}}

# Make an axis
# Inputs:
#   dimtypes - a dictionary mapping names to Axis classes / objects
#   valfunc - a function that can be called to give the values, if they're needed.  No parameters expected
#   atts - a dictionary of metadata to attach to the axis
#   length - expected length of the axis
#   plotatts - a dictionary of plot attributes (optional)

def make_axis (name, dimtypes, valfunc, atts, length, plotatts=None):
# {{{
  from pygeode.axis import Axis, NamedAxis

  axis = None

  dimclass = None
  dimargs = {}

  # if dimtypes is provided...
  if dimtypes:
    # check how the axis type is provided
    if type(dimtypes) is dict: # can be a dictionary or ...
      if name in dimtypes:
        dt = dimtypes[name]
    else: # ... a single axis instance or class/type is directly passed into dimtypes
      dt = dimtypes    
    # Determine axis type      
    if isinstance(dt, Axis):   # Axis instance
      if len(dt) != length: raise ValueError('Provided axis instance %s is the wrong length (expected length %d, got length %d)' % (dt,length,len(dt)))
      axis = dt 
    elif hasattr(dt, '__bases__') and issubclass(dt, Axis): # Axis class
      dimclass = dt
    elif hasattr(dt, '__len__'):
      if len(dt) != 2: raise ValueError('Got a list/tuple for dimtypes, but did not have 2 elements as expected (Axis class, parameters).  Instead, got %s.'%dt)
      dimclass, dimargs = dt
    #TODO: update this message
    else: raise ValueError('Unrecognized dimtypes parameter. Expected a dictionary, axis class, or axis instance.  Got %s instead.'%type(dt))

  # Axis instance not provided?
  if axis is None:
    # Values provided?
    if dimargs.has_key('values'): 
      dimargs = dimargs.copy()
      values = dimargs.pop('values')
      if len(values) != length: raise ValueError('%s, %s: Values provided for axis are the wrong length' % (f.filename, name))

    else: values = valfunc()

    # Create an axis instance
    if dimclass is None:  # Use name to determine the axis
      axis = NamedAxis(values, name, atts=atts, plotatts=plotatts)
#      axis = make_axis (name, atts, values)
    else:                 # Use provided axis class
      axis = dimclass(values, name=name, atts=atts, plotatts=plotatts, **dimargs)

  return axis
# }}}

# Resolve all input axes into a set of output axes
# (similar to an outer product, but each axis appears only once when matched)
# TODO: warn when there are 2 axes of the same type, but different values?
#       what should the behaviour be in that case?  Outer product, or intersection of values?
def combine_axes (axis_lists):
# {{{
  from pygeode.var import Var
  from pygeode.axis import Axis
  from warnings import warn

#  print 'combine_axes in:', axis_lists

  # Were we passed a list of vars?
  axis_lists = [v.axes if isinstance(v,Var) else v for v in axis_lists]
  for A in axis_lists:
    for a in A:
      assert isinstance(a,Axis)

  # Degenerate case - only one set of axes provided
  if len(axis_lists) == 1:
    return axis_lists[0]

  # Extend axes in derived variable, merging all common axes
  out_axes = []
  for A in axis_lists:
    for a in A:

      # Check if we already included this axis in the list
      if a in out_axes:
        # We won't append this axis, but we might want to use it to replace
        # an existing axis in the output list.
        i = out_axes.index(a)
        if a.isparentof(out_axes[i]):
          out_axes[i] = a

        continue  # We have now handled this axis for the output

#      print '**', repr(a), 'not in', out_axes

      # Otherwise, check for things in the output axes that are similar to
      # the axis we're looking at, and might be replaced
      handled = False
      for i,outa in enumerate(out_axes):
        # Check if we have a mapping (i.e. to climatology axis, etc.)
        # In that case, keep the axis which has the most information
        if outa.map_to(a) is not None:
#          print repr(outa), len(outa), 'maps to', repr(a), len(a)
          out_axes[i] = a
          handled = True
        elif a.map_to(outa) is not None:
#          print repr(a), len(a), 'maps to', repr(outa), len(outa)
          handled = True

        if handled: break  # no point in comparing against other output axes, already found a match

      # If nothing matched from output list, append to the end
      if not handled: out_axes.append(a)

  # Check if any of the input vars have all the axes
  basis_axes = [A for A in axis_lists if all(outa in A for outa in out_axes)]
  if len(basis_axes) > 0:
    # Use the axis order from this input instead of the derived order
    return basis_axes[0]

#  print 'combine_axes out:', out_axes
  return out_axes
# }}}

def shared_axes(axes, sets):
# {{{
  ''' shared_axes(axes, sets) - returns two lists, iex and ish, of indices to the provided list
  axes. iex indexes those which are exclusive to one or the other set of axes in sets; ish indexes
  those that are common to both.'''
  ish, iex = [], []
  for i, a in enumerate(axes):
    if (a in sets[0]) is not (a in sets[1]): # Logical exclusive or; a is not common to X and Y
      iex.append(i)
    else: ish.append(i)
  return iex, ish
# }}}

# Find the mapping from one list to another
# (very similar to np.searchsorted, but it includes an error tolerance)
def map_to (a, b):
# {{{
  import numpy as np
  from ctypes import c_int, byref
  A = np.ascontiguousarray(a, 'd')
  NA = c_int(len(A))
  B = np.ascontiguousarray(b, 'd')
  NB = c_int(len(B))
  ind = np.zeros(len(B), 'int32')
#  nind = c_int(0)
  ret = libmisc.map_to(NA, A.ctypes.data, NB, B.ctypes.data, ind.ctypes.data)
#  print A, "map_to", B, "=>", ind
  # Filter out any unmatched indices
  assert ret == 0
  ind = ind[ind>=0]  #ignore unmatched values
  return ind
# }}}

def order (a):
# {{{
  """
  Return the order of values in an axis.
  -1 = decreasing
   0 = no order
   1 = increasing
  """
  from pygeode.axis import Axis
  import numpy as np
  assert isinstance(a,Axis)
  diff = np.diff(a.values)
  if np.all(diff > 0): return 1
  if np.all(diff < 0): return -1
  return 0

# }}}

# Map between two arrays
# (Finds elements that can map between the two arrays, and returns the indices referencing them
# i.e. (1,3,5,7,9,11,13,17,19,23,29,31,27,41) and (1,2,3,5,8,13,21,34,55) give:
#  (0,1,2,6), (0,2,3,5)  - corresponding to elements 1,3,5, and 13.
# One requirement is that the elements are unique.
# Otherwise the mapping becomes ambiguous and/or combinatorially large (O(N^2))
def common_map (a, b):
# {{{
  import numpy as np
  from ctypes import c_int, byref
  a = np.asarray(a)
  b = np.asarray(b)
  na = len(a)
  nb = len(b)
  a_ind = np.argsort(a) # sorting order
  b_ind = np.argsort(b)
  a = np.ascontiguousarray(a[a_ind],dtype='d')  # do the sort
  b = np.ascontiguousarray(b[b_ind],dtype='d')
  nmap = max(na,nb)
  a_map = np.empty(nmap, 'int32')
  b_map = np.empty(nmap, 'int32')

  nmap = c_int(nmap)
  ier = libmisc.common_map(na, point(a), nb, point(b), byref(nmap), point(a_map), point(b_map))
  assert ier == 0
  nmap = nmap.value

  # filter out unmapped indices
  a_map = a_map[:nmap]
  b_map = b_map[:nmap]
  # convert the indices (they're still relative to the sorted order)
  a_map = a_ind[a_map]
  b_map = b_ind[b_map]
  return a_map, b_map
# }}}

"""
# Hash a numpy array (modular addition of the hash of all elements, since it's convenient to do in numpy)
def hasharray (x):
  import numpy as np
  h = np.frompyfunc(hash, 1, 1)
  y = np.asarray(h(x), int)
  return int(y.sum())
"""

"""
def npsum(a, axes):
  ''' npsum(a, axes) - alternative implementation. '''
  ret = [i for i in range(a.ndim) if i not in axes]
  rshape = [a.shape[i] for i in ret]
  return np.sum(a.transpose(ret + axes).reshape(rshape + [-1]), -1, 'd')"""

# Define a version of numpy 'sum' which can handle multiple axes
# (I don't know why you can't do this natively)
# (axes are a list of integers)
def npsum (data, axes, keep_degenerate=False):
# {{{
  import numpy as np
  # loop over axes from right to left, so the intermediate reduction doesn't
  #   change the indices of the next one.
  for i in sorted(axes,reverse=True):
    data = data.sum(i)
    if keep_degenerate: data = np.expand_dims(data,i)
  return data
# }}}
# Similar to above, but ignore 'nan' values
def npnansum (data, axes, keep_degenerate=False):
# {{{
  import numpy as np
  # loop over axes from right to left, so the intermediate reduction doesn't
  #   change the indices of the next one.
  for i in sorted(axes,reverse=True):
    data = np.nansum(data,i)
    if keep_degenerate: data = np.expand_dims(data,i)
  return data
# }}}
def npmin (data, axes):
# {{{
  import numpy as np
  for i in sorted(axes,reverse=True): data = np.amin(data, axis=i)
  return data
# }}}
def npmax (data, axes):
# {{{
  import numpy as np
  for i in sorted(axes,reverse=True): data = np.amax(data, axis=i)
  return data
# }}}

def loopover (vars, outview, inaxes=None, pbar=None):
# {{{
  ''' Loop over a variable 
    In: input variable, view of reduced variable
    Out: slices into an accumulation array, chunks of the input variable that will go into that part of
    the accumulation array'''

  # Make vars a list if it isn't already
  if not hasattr(vars, '__len__'): vars = [vars]

  # clip the output view so there is nothing 'outside' of the selected region
  # (so we can use the slices of the current view chunk as a 1:1 correspondence to
  #  the slices into the accumulation array)
  outview = outview.clip()

  # Get the corresponding view for the input var(s)
  # (get entire axis for all reduced axis)
  if inaxes is None:
    assert len(vars) == 1, 'Implicit reduction axes (inaxes=None) can only be used when looping over one variable.'
    inaxes = vars[0].axes

  inview = outview.map_to(inaxes, strict=False)

  # Break the input view up into memory-friendly chunks
  loop = list(inview.loop_mem())
  for i, inv in enumerate(loop):
    # Get same view, but in output space (drop the reduced axes)
    outv = inv.map_to(outview.axes)
#    print '??', repr(str(inv))
    subpbar = pbar.part(i,len(loop))
    data = []
    for j,v in enumerate(vars):
      vpbar = subpbar.part(j,len(vars))
      data.append(inv.get(v, pbar=vpbar))
#      data.append(inv.get(v))
    yield outv.slices, data
# }}}

# Partial sum along an axis
# parameters:
#  bigarr: input array
#  sl: what slice of the input array to accumulate to (slicing over non-reduction axes, i.e., when done in a loop over a large dataset)
#  out: output array
#  count: output count (number of values accumulated into each output bin)
#  iaxis: the axis to do the partial sum over
#  outmap: the list of output bins to put each input into
def partial_sum (arr, sl, bigout, bigcount, iaxis, outmap):
# {{{
  import numpy as np

#  out = np.zeros(arr.shape[:iaxis] + (bigout.shape[iaxis],) + arr.shape[iaxis+1:], dtype=bigout.dtype)
  out = np.zeros(arr.shape[:iaxis] + (bigout.shape[iaxis],) + arr.shape[iaxis+1:], dtype=arr.dtype)
  count = np.zeros(arr.shape[:iaxis] + (bigcount.shape[iaxis],) + arr.shape[iaxis+1:], dtype='int32')


  assert arr.ndim == out.ndim
#  assert arr.shape[:iaxis] == out.shape[:iaxis]
#  assert arr.shape[iaxis+1:] == out.shape[iaxis+1:]
  assert len(outmap) == arr.shape[iaxis]
#  uoutmap = np.unique(outmap)
  #assert len(uoutmap) == out.shape[iaxis], "%d != %d"%(len(uoutmap),out.shape[iaxis])
  assert count.shape == out.shape
  assert outmap.min() >= 0
  assert outmap.max() < out.shape[iaxis]

#  assert arr.dtype.name == out.dtype.name  # handled in new definition of out??
  assert count.dtype.name == outmap.dtype.name == 'int32', '? %s %s'%(count.dtype,outmap.dtype)
  nx = int(np.product(arr.shape[:iaxis]))
  nin = arr.shape[iaxis]
  nout = out.shape[iaxis]
  ny = int(np.product(arr.shape[iaxis+1:]))
  func = getattr(libmisc,'partial_sum_'+arr.dtype.name)
  ier = func (nx, nin, nout, ny, point(arr), point(out), point(count), point(outmap))
  assert ier == 0

  bigout[sl] += out
  bigcount[sl] += count
# }}}

#TODO: remove these, once Var I/O can efficiently handle concurrent reading & caching
# Merge some coefficient arrays together, so they can be operated on a a single entity
from pygeode.var import Var
class merge_coefs(Var):
# {{{
  def __init__ (self, *coefs):
    from pygeode.axis import Coef
    from pygeode.var import Var
    assert len(set(c.shape for c in coefs)) == 1
    #TODO: more checks?
    axes = list(coefs[0].axes)
    axes.append(Coef(len(coefs)))
    self.coefs = coefs
    Var.__init__(self, axes, coefs[0].dtype)
  def getview (self, view, pbar):
    import numpy as np
    cind = view.integer_indices[-1]
    N = len(cind)
    data = [view.get(self.coefs[ci], pbar=pbar.part(i,N)) for i,ci in enumerate(cind)]
    data = np.concatenate(data, axis=-1)
    return data
# }}}
# Split coefficients
class SplitCoefs(Var):
# {{{
  def __init__ (self, var, c):
    from pygeode.axis import Coef
    from pygeode.var import Var
    self.var = var
    self.c = c
    self.ci = ci = var.whichaxis(Coef)
    self.caxis = var.axes[ci]
    axes = list(var.axes)
    axes = axes[:ci] + axes[ci+1:]
    Var.__init__(self, axes, dtype=var.dtype)
    if var.name != '': self.name = var.name + "_coef%i"%c
  def getview (self, view, pbar):
    inview = view.add_axis(0, self.caxis, [self.c])
    data = inview.get(self.var, pbar=pbar)
    return data.reshape(view.shape)
# }}}
def split_coefs (coef):
  from pygeode.axis import Coef
  return [SplitCoefs(coef, i) for i in range(len(coef.getaxis(Coef)))]
del Var

# Cartesian product of iterators
def product (A, *B):
# {{{
  A = tuple(A)
  # Base case: single array given
  if len(B) == 0:
    for a in A: yield (a,)
    return
  for a in A:
    for tail in product(*B):
      yield (a,)+tail
# }}}

# Test if something is a list-like construct
def islist (x):
  from types import GeneratorType
  return isinstance(x,(list,tuple,GeneratorType))

"""
# This function takes a list as an input.
# If the list is of length 1, and the single element is itself a list, then
# return that inner list.
# Otherwise, return the original list.
# This can be used in functions that can take a variable number of parameters,
# but can also support taking a single list of parameters (or a generator) as input.
def unwrap (x):
# {{{
  assert islist(x)
  x = list(x)
  assert len(x) > 0, "no parameters given!"
  if len(x) == 1 and islist(x[0]): return list(x[0])
  return x
# }}}
"""

# Modify a 'getview' method so that certain axes are guaranteed to be complete.
# Note: this is only a temporary workaround to deal with limitations in the view.get / var.getview structure
def need_full_axes (*iaxes):
  def wrap (old_getview):
    def getview (self, view, pbar):
      from pygeode.view import View
      import numpy as np
      # Indices of the full axes
      fullaxis_ind = [self.whichaxis(a) for a in iaxes]
      # Prepend the other axes
      ind = [i for i in range(self.naxes) if i not in fullaxis_ind] + fullaxis_ind
#      print "ind:", ind
      # Reverse order
      rind = [-1] * len(ind)
      for i,I in enumerate(ind):
        rind[I] = i
      assert len(ind) == self.naxes and len(set(ind)) == self.naxes
      # Construct a view with this new order of axes, and with the specified axes unsliced.
      axes = tuple([view.axes[i] for i in ind])
      slices = tuple([view.slices[i] for i in ind])
      bigview = View(axes, slices = slices)
      bigview = bigview.unslice(*fullaxis_ind)
      viewloop = list(bigview.loop_mem())
      out = np.empty(view.shape, self.dtype)

      for i,smallview in enumerate(viewloop):
#        print '??', i
        for I in fullaxis_ind:
          assert smallview.shape[I] == bigview.shape[I], "can't get all of axis '%s' at once"%view.axes[I].name

        # Slicing relative to the original view
        outsl = tuple(smallview.map_to(bigview.clip()).slices)

        # Reorder the axes to the original order
        axes = tuple([smallview.axes[I] for I in rind])
        assert axes == self.axes
        slices = tuple([smallview.slices[I] for I in rind])
        smallview = View (axes, slices = slices)

        # fudge outsl for this new order
        outsl = tuple([outsl[I] for I in rind])

        # Slicing the 'full' axes to get what we originally needed
        insl = [slice(None)] * self.naxes
        for I in fullaxis_ind: insl[I] = view.slices[I]



        # Get the data
        tmp = old_getview (self, smallview, pbar = pbar.part(i,len(viewloop)) )

#        print '??', out.shape, '[', outsl, ']', ' = ', tmp.shape, '[', insl, ']'
        out[outsl] = tmp[insl]

      return out

    return getview
  return wrap
