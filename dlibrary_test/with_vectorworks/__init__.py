"""Package for handling testing of DLibrary from within Vectorworks, without mocks.

Execute the testing_run.py file in order to run all tests.

Tests will be added on issue basis, so when there is an issue/bug, first a test will be added with what is expected,
then the issue/bug can be resolved. Writing tests to unit test from within Vectorworks is not trivial because we can't
control everything that's happening inside Vectorworks, so we'll have to write extra stuff to check things out, or do
stuff automatically instead of manually. That the reason why we'll add test and build out the mocks on issue basis.
"""

__author__ = 'Dieter Geerts <dieter@dworks.be>'
__license__ = 'MIT'
