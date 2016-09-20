"""Package for handling testing of DLibrary from outside of Vectorworks, with mocks.

Execute the testing_run.py file in order to run all tests.

Tests will be added on issue basis, so when there is an issue/bug, first a test will be added with what is expected,
then the issue/bug can be resolved. Writing test to unit test outside of Vectorworks is not trivial because of the vs
calls that need to be done, so we'll have to mock the behaviour of Vectorworks to do that, and that mocking is a hugh
task, that the reason why we'll add test and build out the mocks on issue basis.
"""

__author__ = 'Dieter Geerts <dieter@dworks.be>'
__version__ = '2016.12.0'
__license__ = 'MIT'
