from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

def read(file_name):
    with open(os.path.join(here, file_name)) as f:
        text = f.read()

    return text
    
README = read('README.rst')
NEWS = read('NEWS.txt')


version = '0.7.5'

setup(name='pyeds',
    version=version,
    description='Python Event Driven System',
    long_description=README,
    classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development'
    ],
    keywords='fsm hsm state finite event machine',
    author='Nenad Radulovic',
    author_email='nenad.b.radulovic@gmail.com',
    url='https://github.com/nradulovic',
    license='LGPL',
    packages=find_packages('src'),
    package_dir = {'': 'src'},include_package_data=True,
    zip_safe=False,
    install_requires=[
        # Currently no dependencies
    ],
    entry_points={
        'console_scripts':
            ['pyeds=main:main']
    }
)
