import json, os, datetime, uuid, logging

import issues_conf as conf

logger = logging.getLogger(__name__)

def timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

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
        
        self.obj_dir = "{0}/objs".format(self.directory)
        if not os.path.isdir(self.obj_dir):
            os.makedirs(self.obj_dir)
        
        self.issues_file = "{0}/issues.db".format(directory)
        self.issues_data = load_data(self.issues_file)
        self.dirty = False
    
    def close(self):
        if self.issues_data and self.dirty:
            logger.debug("Saving database...")
            save_data(self.issues_file, self.issues_data)
            self.issues_data = None
            self.dirty = False
            
    def filter(self, sort=None, filter_method=None):
        items = [ Issue.expand_index(x, self.issues_data[x]) for x in self.issues_data ]
        if sort:
            reverse = False
            if sort[0] == '-':
                sort = sort[1:]
                reverse = True
            items = sorted(items, key=lambda x: x[sort], reverse=reverse)
            
        if filter_method:
            return [ x for x in items if filter_method(x) ]
        
        return items
    
    def match(self, uuid):
        '''
        Match a single file from a uuid stub so we dont have to type full uuids.
        Returns the full file path or throws an error if none or multiple matches.
        '''
        import glob
        matches = glob.glob('{0}/{1}*'.format(self.obj_dir, uuid))
        
        if not matches:
            raise Exception("No match for uuid: {0}".format(uuid))
        
        if len(matches) > 1:
            print [ os.path.basename(x) for x in matches ]
            raise Exception("Multiple matches for {0} - be more specific".format(uuid))
        
        return matches[0]
    
    def get(self, uuid):
        with open(self.match(uuid)) as bob:
            data = json.load(bob)
            
        return Issue(**data)
    
    def index(self, issue):
        i = [ getattr(issue, x) for x in self.INDEX[:-2] ]
        i.append(len(issue.comments))
        i.append(len(issue.attachments))
        return i
    
    def delete(self, uuid):
        f = self.match(uuid)
        issue = self.get(uuid)
        
        del self.issues_data[issue.uuid]
        os.unlink(f)
        
        self.dirty = True
    
    def update(self, issue):
        issue.updated = timestamp()
        
        self.issues_data[issue.uuid] = issue.index()
        
        with open('{0}/{1}'.format(self.obj_dir, issue.uuid), 'w') as bob:
            issue.write(bob)
            
        self.dirty = True
        
    def rebuild(self):
        self.issues_data = {}
        c = 0
        for uuid in os.listdir(self.obj_dir):
            issue = self.get(uuid)
            self.issues_data[issue.uuid] = issue.index()
            c += 1
        return c
        
class Issue(object):
    
    def __init__(self, **kwargs):
        data = dict(conf._fields)
        data.update(kwargs)
        
        for key in data:
            setattr(self, key, data[key])
            
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())
            
        if self.created is None:
            self.created = timestamp()
    
    def index(self):
        return [ getattr(self, x) for x in conf._index ]
    
    @classmethod
    def expand_index(cls, uuid, index):
        d = dict(zip(conf._index, index))
        d['uuid'] = uuid
        return d
    
    def add_comment(self, comment, user):
        self.comments.append('{0}\n\t[ {1} {2} ]'.format(comment, user, timestamp()))
        
    def write(self, stream):
        json.dump(self.__dict__, stream, indent=2)
                
    def __repr__(self):
        return "<Issue {0}>".format(self.uuid[:6]) 