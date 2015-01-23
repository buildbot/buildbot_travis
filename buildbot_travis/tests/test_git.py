from twisted.trial import unittest
from buildbot_travis.vcs import git


class GitUrlParser(unittest.TestCase):

    def test_simple(self):
        url = "git://github.com/tardyp/buildbot_travis"
        parsed = git.ParsedGitUrl(url)
        self.assertEqual(parsed.scheme, 'git')
        self.assertEqual(parsed.netloc, 'github.com')
        self.assertEqual(parsed.path, '/tardyp/buildbot_travis')

    def test_user(self):
        url = "git+ssh://bla@github.com/tardyp/buildbot_travis"
        parsed = git.ParsedGitUrl(url)
        self.assertEqual(parsed.scheme, 'git+ssh')
        self.assertEqual(parsed.netloc, 'github.com')
        self.assertEqual(parsed.user, 'bla')
        self.assertEqual(parsed.path, '/tardyp/buildbot_travis')

    def test_userpass(self):
        url = "git+ssh://bla:secrit::!@github.com/tardyp/buildbot_travis"
        parsed = git.ParsedGitUrl(url)
        self.assertEqual(parsed.scheme, 'git+ssh')
        self.assertEqual(parsed.netloc, 'github.com')
        self.assertEqual(parsed.user, 'bla')
        self.assertEqual(parsed.passwd, 'secrit::!')
        self.assertEqual(parsed.path, '/tardyp/buildbot_travis')
