import unittest
import os, shutil, sys, getpass

import pyissues
from pyissues import PyIssues, PyIssuesException

class TestPyIssues(unittest.TestCase):
    
    TEST_DIR = '/tmp/issues'
    
    def setUp(self):
        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)
        os.makedirs(self.TEST_DIR)
        self.issues = PyIssues(self.TEST_DIR) 
        
    def tearDown(self):
        shutil.rmtree(self.TEST_DIR)
    
    def assertFieldEqual(self, result, field, expected):
        self.assertEqual([ x[field] for x in result ], expected)
    
    def test_empty(self):
        
        self.assertEqual(self.issues.filter(), [])
        
        # no match
        with self.assertRaisesRegexp(PyIssuesException, "No match for uuid: 123"):
            self.issues.match('123')
            
    def test_create(self):
        with self.assertRaisesRegexp(PyIssuesException, "Missing required field: description"):
            self.issues.create()
        
        now = pyissues.timestamp()
        
        issue = self.issues.create(description="Test 1")
        self.issues.update(issue)
        
        self.assertEqual(issue.description, "Test 1")
        self.assertEqual(issue.owner, getpass.getuser())
        self.assertEqual(issue.created, now)
        self.assertEqual(issue.updated, now)
        
        uuid = issue.uuid
        path = "{0}/objs/{1}".format(self.TEST_DIR, uuid)
        
        self.assertTrue(os.path.exists(path))
        
        # check we can lookup a partial
        self.assertEqual(self.issues.match(uuid[0:3]), path)
        
        # check for errors if multiple matches
        open(path + "_", 'w').close()
        with self.assertRaisesRegexp(PyIssuesException, "Multiple matches for {0} - be more specific".format(uuid[0:3])):
            self.issues.match(uuid[0:3])
            
    def test_index(self):
        issue = self.issues.create(description='Test 1')
        self.issues.update(issue)
        
        index = self.issues.filter({'uuid': issue.uuid})[0]
        self.assertEqual(index['comments'], 0)
        self.assertEqual(index['assigned'], 'no-one')
            
    def test_filters(self):
        for i in [ 'AA', 'AB', 'BC' ]:
            self.issues.update(self.issues.create(description="Test {0}".format(i)))
        
        filter_a = lambda x: 'Test A' in x['description']
        
        # test sorting direction
        self.assertFieldEqual(self.issues.filter(sort='description'), 'description',
                              ['Test AA', 'Test AB', 'Test BC'])
        self.assertFieldEqual(self.issues.filter(sort='-description'), 'description',
                              ['Test BC', 'Test AB', 'Test AA'])
        
        # test function based filtering
        self.assertFieldEqual(self.issues.filter(filter_a, 'description'), 'description',
                              ['Test AA', 'Test AB'])
        
        # test dict based filtering
        self.assertFieldEqual(self.issues.filter({'description': 'Test AB'}, 'description'), 'description',
                              ['Test AB'])
        self.assertFieldEqual(self.issues.filter({'description': 'Test'}, 'description'), 'description',
                              [])
        self.assertFieldEqual(self.issues.filter({'foo': 'bar'}, 'description'), 'description',
                              [])
        
        # test both
        self.assertFieldEqual(self.issues.filter(filter_a, 'description'), 'description',
                              ['Test AA', 'Test AB'])
        self.assertFieldEqual(self.issues.filter(filter_a, '-description'), 'description',
                              ['Test AB', 'Test AA'])
        
        
    def test_update(self):
        # switch to
        orig = pyissues.DATETIME_FORMAT
        pyissues.DATETIME_FORMAT = "%S.%f"
        
        self.assertFalse(self.issues.flush())
        
        issue = self.issues.create(description='Test 1')
        self.issues.update(issue)
        self.assertTrue(self.issues.flush())
        
        updated = issue.updated
        
        issue.status = 'closed'
        self.assertEqual(issue.updated, updated)
        
        self.issues.update(issue)
        self.assertTrue(self.issues.flush())
        
        # check the timestamp was updated
        self.assertGreater(issue.updated, updated)
        
    def test_persistence(self):
        issue = self.issues.create(description='Test 1')
        self.issues.update(issue)
        
        uuid = issue.uuid
        
        self.issues.close()
        
        self.issues = PyIssues(self.TEST_DIR)
        
        self.assertEqual(self.issues.filter()[0]['uuid'], uuid)
        
        issue = self.issues.get(uuid)
        self.assertEqual(issue.description, 'Test 1')
        
if __name__ == '__main__':
    unittest.main()