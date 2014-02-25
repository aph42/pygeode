#!/usr/bin/env python

from distutils.core import setup, Extension
import numpy as np

interpcore = Extension ('pygeode.interpcore', sources=['pygeode/interp.c'], libraries=['gsl','gslcblas'])
timeaxiscore = Extension ('pygeode.timeaxiscore', sources=['pygeode/timeaxis.c'], extra_compile_args=['-std=c99'])
quadrulepy = Extension ('pygeode.quadrulepy', sources=['pygeode/quadrule.c','pygeode/quadrulepy.c'])
toolscore = Extension ('pygeode.toolscore', sources=['pygeode/tools.c'], extra_compile_args=['-std=c99'])
svdcore = Extension ('pygeode.svdcore', sources=['pygeode/svd.c'], extra_compile_args=['-std=c99'])
eofcore = Extension ('pygeode.eofcore', sources=['pygeode/eof.c'], libraries=['lapack'], extra_compile_args=['-std=c99'])
opendapcore = Extension ('pygeode.formats.opendapcore', sources=['pygeode/formats/opendap.c'], extra_compile_args=['-std=c99'])
gribcore = Extension ('pygeode.formats.gribcore', sources=['pygeode/formats/grib.c'], extra_compile_args=['-std=c99'])

# PyGeode installation script

setup (	name="python-pygeode",
	version="1.0.0~alpha2",
        description = "Gridded data manipulator for Python",
	long_description = """\
PyGeode is a software library intended to simplify the management, analysis,
and visualization of gridded geophysical datasets such as those generated by
climate models. The library provides three main advantages. Firstly, it can
define a geophysical coordinate system for any given dataset, and allows
operations to be carried conceptually in this physical coordinate system, in
a way that is independent of the native coordinate system of a particular
dataset. This greatly simplifies working with datasets from different
sources. Secondly, the library allows mathematical operations to be performed
on datasets which fit on disk but not in memory; this is useful for dealing
with the extremely large datasets generated by climate models, and permits
operations to be performed over networks. Finally, the library provides tools
for visualizing these datasets in a scientifically useful way. The library is
written in Python, and makes use of a number of existing packages to perform
the underlying computations and to create plots.
""",
        license = "GPL-3",
        author="Peter Hitchcock, Andre Erler, Mike Neish",
        author_email="pygeode-users@googlegroups.com",
        url="http://pygeode.bitbucket.org/",
	requires=['numpy','matplotlib','progressbar'], # NOTE: distutils doesn't ever check this!
        # Note: When building Windows version, pre-compile the libraries
        # in the 'pygeode' subdirectory.
	package_data={'pygeode': ['*.dll'], 'pygeode.formats': ['*.dll']},
	packages=["pygeode", "pygeode.formats", "pygeode.server", "pygeode.plugins", "pygeode.plot"],
	include_dirs = [np.get_include()],
	ext_modules=[interpcore, timeaxiscore, quadrulepy, toolscore, svdcore, eofcore, opendapcore, gribcore]
)

