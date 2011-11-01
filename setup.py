from setuptools import setup, find_packages
import sys, os

setup(name='ccg-django-extras',
      version='0.1.1',
      description='Extra CCG code for Django applications.',
      long_description='Extra code used by the Centre for Comparative Genomics in our Django applications.',
      classifiers=[], # see http://pypi.python.org/pypi?:action=list_classifiers
      keywords='',
      author='Centre for Comparative Genomics',
      author_email='',
      url='http://code.google.com/p/ccg-django-extras/',
      license='GNU General Public License, version 2',
      namespace_packages=['ccg'],
      packages=find_packages(exclude=['examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      entry_points="",
      )
