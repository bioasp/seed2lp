from setuptools import setup, find_packages

exec(open('seed2lp/_version.py').read())
setup(
    name='seed2lp',
    version=__version__,
    description='Seed searching from network as SBML using Logic programming',
      url='http://github.com/*/*',
      author='Chabname Ghassemi Nedjad',
      author_email='chabname.ghassemi-nedjad@inria.fr',
      license='GPL',
      classifiers =[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: ASP",
      ],

      packages=find_packages(),
      package_data={
          "": ["*.yaml"],
      },
      entry_points = {
        'console_scripts': ['seed2lp=seed2lp.__main__:main'],
      },
      zip_safe=False,
      include_package_data = True
)