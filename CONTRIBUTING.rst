
Ground Rules
============

Follow the code of conduct (CODE_of_CONDUCT.md) defined in this project.

Responsibilities
----------------

 * Ensure that new code passes current unittests.
 * If new code adds new features write additional unittests for that.
 * Ensure to follow Python Style Guide defined in this project.
 * Create issues for any major changes and enhancements that you wish to make. 
   Discuss things transparently and get community feedback.
 * Don't add any classes to the codebase unless absolutely needed. Err on the 
   side of using functions.
 * Keep feature versions as small as possible, preferably one new feature per 
   version.
 * Be welcoming to newcomers and encourage diverse new contributors from all 
   backgrounds. See the Python Community Code of Conduct.


Setting up development environment
==================================

It is recomended to use virtual environments. To create an virtual environment
use:

    python3 -m venv .

To activate it use:

    . bin/activate

Then install the requirements:

    pip install -r requirements/development.txt

To exit the virtual environment just execute:

    deactivate

Next time when you want to continue use virtual environment use:

    . bin/activate


Release HOWTO
=============

To make a release, 

  1) Update release date/version in:
      * setup.py
      * doc/conf.py
      * NEWS.txt 
  2) Run `python3 setup.py sdist`
  3) Test the generated source distribution in `dist/`
  4) Upload to PyPI: `python3 setup.py sdist upload`
  5) Tag the commit with following message: v{YY}.{MM}.{RR} where:
      * YY is the current year
      * MM is the current month (including zero)
      * RR number of release in this year/month (including zero/zeroes)
  6) Increase version (for next release) in:
      * setup.py
      * doc/conf.py
      * NEWS.txt 
