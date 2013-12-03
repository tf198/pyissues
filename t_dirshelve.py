import unittest
import dirshelve

import os, shutil

TEST_DIR = 'testing'

class DirShelveTest(unittest.TestCase):

    def setUp(self):
        self.shelf = dirshelve.open(TEST_DIR)
        
    def tearDown(self):
        shutil.rmtree(TEST_DIR)
        
    def test_set(self):
        self.shelf['test1'] = 'one'
        
        self.assertEqual(self.shelf._cache['test1'], 'one')
        self.assertEqual(os.listdir(TEST_DIR), ['test1'])
        
        self.assertEqual(self.shelf.sync(), [])
        
        self.shelf['test/test2'] = 'two'
        self.assertEqual(self.shelf._cache['test/test2'], 'two')
        self.assertEqual(os.listdir(TEST_DIR), ['test1', 'test'])
        self.assertEqual(os.listdir(TEST_DIR + '/test'), ['test2'])
    
    def test_get(self):
        self.shelf['test1'] = 'one'
        
        self.assertEqual(self.shelf['test1'], 'one')
        
        with self.assertRaises(KeyError):
            self.shelf['test2']
    
    def test_delete(self):
        self.shelf['test1'] = 'one'
        self.shelf.sync()
        
        del(self.shelf['test1'])
        self.assertFalse('test1' in self.shelf._cache)
        self.assertFalse('test1' in self.shelf._initial)
        self.assertFalse(os.path.exists(TEST_DIR + '/test1'))
        
        with self.assertRaises(KeyError):
            del(self.shelf['test2'])
            
    def test_keys(self):
        self.assertEqual(len(self.shelf), 0)
        
        self.shelf['test1'] = 'one'
        self.shelf['test/test2'] = 'two'
        
        self.assertEqual(len(self.shelf), 2)
        
        self.assertEqual(self.shelf.keys(), ['test1', 'test/test2'])
        self.assertEqual([ x for x in self.shelf ], ['test1', 'test/test2'])
        
        
class DirShelveWritebackTest(DirShelveTest):

    def setUp(self):
        self.shelf = dirshelve.open(TEST_DIR, writeback=True)
        
    def test_set(self):
        self.shelf['test1'] = 'one'
        
        self.assertEqual(self.shelf._cache['test1'], 'one')
        self.assertEqual(os.listdir(TEST_DIR), [])
        
        self.assertEqual(self.shelf.sync(), ['test1'])
        self.assertEqual(os.listdir(TEST_DIR), ['test1'])
    
    def test_delete(self):
        super(DirShelveWritebackTest, self).test_delete()
        
        # unsynced test
        self.shelf['test2'] = 'one'
        del(self.shelf['test2'])
        
    def test_keys(self):
        super(DirShelveWritebackTest, self).test_keys()
        
        # check union of synced and unsynced
        self.assertEqual(self.shelf.sync(), ['test1', 'test/test2'])
        self.shelf['test3'] = 'three'
        self.assertEqual(len(self.shelf), 3)
        
        self.assertEqual(self.shelf.keys(), ['test1', 'test/test2', 'test3'])
        
    def test_sync(self):
        self.shelf['test1'] = 'one'
        self.shelf.close()
        
        self.setUp()
        self.assertEqual(self.shelf['test1'], 'one')
        
        self.assertTrue('test1' in self.shelf._initial)
        self.assertEqual(self.shelf.sync(), [])
        
        self.shelf['test1'] = 1
        self.assertEqual(self.shelf.sync(), ['test1'])

        
if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
