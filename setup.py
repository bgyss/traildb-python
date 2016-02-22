from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(name='traildb',
      version='0.0.1',
      description='TrailDB stores and queries cookie trails from raw logs.',
      author='AdRoll.com',
      packages=['traildb'],
      ext_modules=cythonize([Extension('traildb.ctraildb', ['traildb/ctraildb.pyx'],
                                       libraries=['traildb'])]))
