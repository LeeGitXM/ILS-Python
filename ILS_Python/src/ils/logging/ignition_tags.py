'''
Classes to automatically translate between Ignition tags and Python attributes.

Created on 7/29/2020

@author: D. Webb

'''
import system, datetime
import ils.logging as logging
log = logging.xomGetLogger('xom.halobutyl.ignition_tags')

class IgnitionTagClass(object):
    '''
    Store a tag value and all the ancillary attributes from an Ignition tag.
    '''
    parent = None
    python_name = ''
    value = None
    type = ''
    direction = ''
    tagpath = ''
    debug = False
    starting_value = None
    always_write = False
    
    def __init__(self, parent, mapping, always_write=False, value=None, debug=False):
        self.parent = parent
        self.mapping = mapping
        self.python_name = mapping['python_name']   
        self.tagpath = mapping['tagpath']
        self.type = mapping['type']
        self.direction = mapping['direction'].upper()
        if self.type == 'datetime':
            java_datetime = value
            str_datetime = system.date.format(java_datetime, "yyyy-MM-dd HH:mm:ss")
            python_datetime = datetime.datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")
            self.value = python_datetime
        else:
            self.value = value
        self.name = 'IgnitionTagClass: [%s : %s]' % (self.python_name, self.tagpath)
        self.debug = debug
        self.always_write = always_write
        self.setStartingValue(self.value)

    def __setattr__(self, name, value):
        if hasattr(self, 'name') and (name == 'value'):
            log.tracef('setting %s.value = %s', str(self.name), str(value))
        super(IgnitionTagClass, self).__setattr__(name, value)
            
    def setStartingValue(self, value):
        # Set starting value
        if self.isArray(value):
            self.starting_value = []
            for i in range(len(value)):
                self.starting_value.append(value[i])
            log.tracef('%s: __init__: found value[] = %s', self.name, self.starting_value)
        else:
            self.starting_value = value                
            log.tracef('%s: __init__: found values = %s', self.name, self.starting_value)
    
    def isArray(self, val):
        t = '%s' % type(val)
        if t == "<type 'array.array'>":
            return True
        else:
            return False

    def hasChanged(self):
        if self.isArray(self.value):
            for i in range(len(self.value)):
                if self.starting_value[i] <> self.value[i]:
                    log.tracef('%s: hasChanged: found value[%d] changed from %s to %s', self.name, i, self.starting_value[i], self.value[i])
                    return True
        else:
            if self.starting_value <> self.value:
                log.tracef('%s: hasChanged: found value changed from %s to %s', self.name, self.starting_value, self.value)
                return True
        log.tracef('%s: hasChanged: value did not change', self.name)
        return False
    
    def write(self, force=False, debug=False):
        if self.always_write or force or self.hasChanged():
            if self.type == 'datetime':
                value = self.value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = self.value
            log.tracef('%s: Writing value = %s', self.name, value)
            from ils.io.api import writeWithNoCheck
            writeWithNoCheck(self.tagpath, value) 
            self.setStartingValue(value)
        else:
            if self.debug or debug:
                log.tracef('%s: Skipping writing value, it has not been written.', self.name)
     
class IgnitionTagsClass(object):
    '''
    '''
    _tag_mappings = []
    _tags = {}
    debug = False
        
    def __init__(self, tag_mappings, debug=False):
        '''
        Read all Ignition tags in the tag_mapping and assign them to class instance attributes.
        
        tag_mapping has format:
        [{'python_name':value, 'tagpath':value, 'type':value, 'direction':value, 'always_write':True/False},
        ...
        ]
        
        direction : 'READ'/'WRITE'/'READ/WRITE'
        type : 'integer', 'double', 'string', 'boolean', 'datetime'
            Note:  datetime type is stored in value attribute as a Python datetime object.
                   It is written out to Ignition tag using string format .strftime("%Y-%m-%d %H:%M:%S")
        [optional] always_write : True/False - always write values even if they haven't changed
        '''
        self._tag_mappings = tag_mappings
        self.debug = debug
        tag_paths = []
        for mapping in tag_mappings:
            direction = mapping['direction'].upper()
            if (direction == 'READ') or (direction == 'READ/WRITE'):
                tag_paths.append(mapping['tagpath'])
        try:
            qvs = system.tag.readAll(tag_paths)
        except Exception, e:
            raise Exception('Problem with tag paths:  "%s".  %s' % (tag_paths, e))
        index = 0
        for qv in qvs:
            if not(qv.quality.isGood()):
                tag_mapping = tag_mappings[index]
                error_msg = 'Error reading tag "%s", quality is not good.' % tag_mapping['tagpath']
                log.errorf(error_msg)
                raise ValueError(error_msg)
            index = index + 1
            
        index = 0
        self._tags = {}
        for mapping in tag_mappings:
            name = mapping['python_name']
            direction = mapping['direction'].upper()
            if (direction == 'READ') or (direction == 'READ/WRITE'):
                if self.debug:
                    log.tracef('name=%s, qvs[%d]=%s', name, index, qvs[index])
                value = qvs[index].value
                index = index + 1
            else:
                value = None
            always_write = False
            if mapping.has_key('always_write') and mapping['always_write']:
                always_write = True
            try:
                attr = IgnitionTagClass(self, mapping, value=value, always_write=always_write, debug=self.debug)
            except Exception, e:
                raise Exception('Error creating IgnitionTagClass(%s, %s, %s, %s):  %s' % (mapping, value, always_write, debug, e))
            setattr(self, name, attr)
            self._tags[name] = attr
                   
    def write(self, force=False, debug=False):
        '''
        Write values of 'WRITE' and 'READ/WRITE' variables to their Ignition tags using ILS output command.
        Passes to each tag's own write() method, which follows ILS write enabled settings.
        '''
        log.tracef('Writing all (force=%s, debug=%s)', str(force), str(debug))
        for tag in self._tags.itervalues():
            direction = tag.direction
            if (direction == 'WRITE') or (direction == 'READ/WRITE'):
                tag.write(force=force, debug=debug)
        
    def __del__(self):
        self.write()
        
        
def test_me():
    from ils.io.util import getProviderFromTagPath
    provider = getProviderFromTagPath('Site/Test/')

    tag_list = [
                {'python_name':'test_int1', 'tagpath':"[%s]Test/TestInt1" % (provider), 'type':'int', 'direction':'READ'},
                {'python_name':'test_int2', 'tagpath':"[%s]Test/TestInt2" % (provider), 'type':'int', 'direction':'READ/WRITE'},
                {'python_name':'test_float', 'tagpath':"[%s]Test/Test1" % (provider), 'type':'float', 'direction':'READ/WRITE'}
                ]
    try:
        tags = IgnitionTagsClass(tag_list)
    except Exception, e:
        log.exception('Exception: %s' % e)

    print 'test_int1 = %d' % tags.test_int1.value
    print 'test_int2 = %d' % tags.test_int2.value
    print 'test_float = %f' % tags.test_float.value
    
    tags.test_int2.value = tags.test_int2.value + 1
    import math
    tags.test_float.value = math.sqrt(tags.test_int2.value)
    tags.write()
    
    
    
    
    
    
    
    
    
