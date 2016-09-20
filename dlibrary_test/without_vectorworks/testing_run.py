import os
from unittest import TextTestRunner, TestLoader

TextTestRunner(verbosity=2).run(TestLoader().discover(os.path.dirname(__file__), 'test_*.py'))
