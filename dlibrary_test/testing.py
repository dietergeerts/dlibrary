import pydoc
from unittest import TestLoader, TextTestRunner

TextTestRunner().run(TestLoader().discover('.', '*_test.py'))