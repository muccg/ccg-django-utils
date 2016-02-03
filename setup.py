from setuptools import setup, find_packages

setup(name='ccg-django-utils',
      version='0.4.0',
      description='Extra CCG code for Django applications.',
      long_description='Extra code used by the Centre for Comparative Genomics in our Django applications.',
      classifiers=[], # see http://pypi.python.org/pypi?:action=list_classifiers
      keywords='',
      author='Centre for Comparative Genomics',
      author_email='web@ccg.murdoch.edu.au',
      url='https://bitbucket.org/ccgmurdoch/ccg-django-extras',
      license='GNU General Public License, version 2',
      packages=find_packages(exclude=['examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['six'],
      )
