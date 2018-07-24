from setuptools import setup, find_packages

setup(name='qjira',
      version='0.99.18',
      description='Query JIRA Cloud REST API',
      author='Andrew Hamlin',
      author_email='andrew.hamlin@sailpoint.com',
      packages=find_packages(),
      include_package_data=True,
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
      ],
      entry_points={
          'console_scripts': [
              'qjira = qjira.__main__:main',
              'qjira_dump = qjira.__dump__:main'
          ]
      },
      test_suite='qjira.tests.suite',
      install_requires=[
          'requests',
          'python-dateutil',
          'keyring',
          'six',
      ],
      tests_require=['contextlib2;python_version<"3.4"']
)
     
