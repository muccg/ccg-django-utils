from setuptools import setup, find_packages

setup(name='ccg-django-utils',
      version='0.4.1',
      description='Extra CCG code for Django applications.',
      long_description='Extra code used by the Centre for Comparative Genomics in our Django applications.',
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Web Environment",
          "Framework :: Django",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
          "Topic :: Internet :: WWW/HTTP :: WSGI",
      ],
      keywords='ccg django wsgi utils',
      author='Centre for Comparative Genomics',
      author_email='web@ccg.murdoch.edu.au',
      url='https://github.com/muccg/ccg-django-utils',
      license='GNU General Public License, version 2',
      packages=find_packages(exclude=['examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['six'],
      )
