from unittest import TextTestRunner, TestLoader

TextTestRunner(verbosity=2).run(TestLoader().discover('.', 'test_*.py'))
