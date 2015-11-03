from twisted.trial import unittest
from buildbot_travis.important import ImportantManager


class fakeChange(object):
    def __init__(self, files):
        self.files = files


class ImportantManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.i = ImportantManager(["a", "b*", "Readme.md"])

    def assertImportant(self, files):
        self.assertTrue(self.i.fileIsImportant(fakeChange(files)))

    def assertNotImportant(self, files):
        self.assertFalse(self.i.fileIsImportant(fakeChange(files)))

    def test_AllImportant(self):
        self.i = ImportantManager([])
        self.assertImportant(["file.c"])

    def test_basic(self):
        self.assertImportant(["file.c"])

    def test_basic2(self):
        self.assertNotImportant(["Readme.md"])

    def test_basic3(self):
        self.assertNotImportant(["a", "basic", "Readme.md"])

    def test_basic4(self):
        self.assertImportant(["a", "basic", "Readme.md", "file.c"])
