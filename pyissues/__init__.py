import json, os, datetime, uuid, logging

import issues_conf as conf

logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def timestamp():
    return datetime.datetime.utcnow().strftime(DATETIME_FORMAT)

def load_data(filename, **kwargs):
    try:
        return json.load(open(filename, 'r'), **kwargs)
    except IOError:
        return {}
    
def save_data(filename, data, **kwargs):
    json.dump(data, open(filename, 'w'), indent=0)
        
class PyIssues(object):
    '''
    Simple issues collection, based on a directory.
    '''
    def __init__(self, directory):
        self.directory = directory
        self.settings = conf.__dict__.copy()
        
        # load local settings
        try:
            execfile("{0}/conf.py".format(self.directory), self.settings)
            logger.debug("Loaded custom settings")
        except IOError:
            logger.debug("No custom settings")
        
        self.obj_dir = "{0}/objs".format(self.directory)
        if not os.path.isdir(self.obj_dir):
            os.makedirs(self.obj_dir)
        
        self.issues_file = "{0}/issues.db".format(directory)
        self.issues_data = load_data(self.issues_file)
        self.dirty = False
    
    def flush(self):
        '''
        Writes out database if necessary.
        Returns whether the database was written or not
        '''
        if self.issues_data and self.dirty:
            logger.debug("Saving database...")
            save_data(self.issues_file, self.issues_data)
            self.dirty = False
            return True
        return False
    
    def close(self):
        '''
        Saves the database if necessary and cleans up.
        '''
        self.flush()
        self.issues_data = None
            
    def filter(self, filters=None, sort=None):
        '''
        Returns index items matching the criteria.
        
        filters can be a func or a dict of exact matches.
        sort is the name of a field, optionally prefixed with '-' for reverse.
        '''
        items = [ Issue.expand_index(x, self.issues_data[x], self.settings['_index']) for x in self.issues_data ]
        
        if filters:
            if hasattr(filters, '__iter__'):
                d = filters
                filters = lambda x: { i: x.get(i) for i in d } == d
            
            items = [ x for x in items if filters(x) ]
        
        if sort:
            reverse = False
            if sort[0] == '-':
                sort = sort[1:]
                reverse = True
            items = sorted(items, key=lambda x: x[sort], reverse=reverse)
            
        return items
    
    def match(self, uuid):
        '''
        Match a single file from a uuid stub so we dont have to type full uuids.
        Returns the full file path or throws an error if none or multiple matches.
        '''
        import glob
        matches = glob.glob('{0}/{1}*'.format(self.obj_dir, uuid))
        
        if not matches:
            raise PyIssuesException("No match for uuid: {0}".format(uuid))
        
        if len(matches) > 1:
            raise PyIssuesException("Multiple matches for {0} - be more specific".format(uuid))
        
        return matches[0]
    
    def get(self, uuid):
        '''
        Get a single issue.
        uuid can be a partial uuid.
        '''
        with open(self.match(uuid)) as bob:
            data = json.load(bob)
            
        return self.create(**data)
    
    def create(self, **params):
        return Issue(self.directory, self.settings['_fields'], self.settings['_required'], **params)
    
    def delete(self, uuid):
        f = self.match(uuid)
        issue = self.get(uuid)
        
        del self.issues_data[issue.uuid]
        os.unlink(f)
        
        self.dirty = True
    
    def update(self, issue):
        issue.updated = timestamp()
        
        self.issues_data[issue.uuid] = issue.index(self.settings['_index'])
        
        with open('{0}/{1}'.format(self.obj_dir, issue.uuid), 'w') as bob:
            issue.write(bob)
            
        self.dirty = True
        
    def rebuild(self):
        self.issues_data = {}
        self.dirty = True
        c = 0
        for uuid in os.listdir(self.obj_dir):
            issue = self.get(uuid)
            if issue.status != 'archived':
                self.issues_data[issue.uuid] = issue.index()
            c += 1
        return c
        
class Issue(object):
    
    def __init__(self, directory, fields, required, **kwargs):
        
        for f in required:
            if not f in kwargs:
                raise PyIssuesException("Missing required field: {0}.".format(f))        
        
        data = dict(fields)
        data.update(kwargs)
        
        for key in data:
            setattr(self, key, data[key])
            
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())
            
        if self.created is None:
            self.created = timestamp()
            
        self._data_dir = "{0}/files/{1}".format(directory, self.uuid)
    
    def index(self, fields):
        return [ getattr(self, x) for x in fields ] + [len(self.comments), len(self.attachments)]
    
    @classmethod
    def expand_index(cls, uuid, index, fields):
        d = dict(zip(fields + ('comments', 'attachments'), index))
        d['uuid'] = uuid
        return d
    
    def add_comment(self, comment, user):
        '''
        Add a comment.
        Comment is stored in the form (comment, user, timestamp)
        '''
        self.comments.append((comment, user, timestamp()))
    
    def remove_comment(self, index):
        '''
        Remove a comment (zero based index)
        '''
        del(self.comments[index])
    
    def attach_file(self, filename, user):
        '''
        Attach a file to the issue.
        
        Returns (original_name, stored_name, user, timestamp) as stored
        '''
        import shutil
        
        if not os.path.exists(filename):
            raise Exception("No such file: {0}".format(filename))
        
        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)
        
        f = os.path.basename(filename)
        
        i=0
        while os.path.exists("{0}/{1}_{2}".format(self._data_dir, f, i)):
            i += 1
        
        target = "{0}/{1}_{2}".format(self._data_dir, f, i)
        
        logger.debug("Storing {0} at {1}".format(f, target))
        shutil.copy(filename, target)
        
        data = (f, os.path.basename(target), user, timestamp())
        self.attachments.append(data)
        return data
    
    def remove_file(self, index):
        '''
        Remove an attached file (zero based index)
        '''
        _, f = self.get_file(index)
        os.unlink(f)
        del(self.attachments[index])
      
    def get_file(self, index):
        '''
        Get path information about an attached file (zero based index)
        
        returns (original, path)
        '''
        attachment = self.attachments[index]
        return (attachment[0], "{0}/{1}".format(os.path.realpath(self._data_dir), attachment[1]))
    
    def write(self, stream):
        stream.write(str(self))
    
    def __str__(self):
        return json.dumps({ x: self.__dict__[x] for x in self.__dict__ if not x[0] == '_' }, self.__dict__, indent=2)
                
    def __repr__(self):
        return "<Issue #{0}>".format(self.uuid[:8])
    
class PyIssuesException(Exception):
    pass