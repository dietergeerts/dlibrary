from unittest import TextTestRunner, TestLoader
from dlibrary_test.testing import VectorScript

VectorScript.initialize()
TextTestRunner(verbosity=2).run(TestLoader().discover('.', 'test_*.py'))
