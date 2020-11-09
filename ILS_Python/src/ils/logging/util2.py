import system

class ModeAttrEnum(object):
    none = 0
    Operator = 1
    Program = 2
        
class ModeEnum(object):
    Manual = 0
    Automatic = 1
    Cascade = 2
    BCascade = 3
    
class ExecStateEnum(object):
    Inactive = 0
    Active = 1
    
class ARWEnum(object):
    Normal = 0
    Hi = 1
    Lo = 2
    HiLo = 3

def ARWString(ARW):
    '''
    Return a string corresponding to the ARWEnum status
    '''
    if   ARW == ARWEnum.Normal: return 'Normal'
    elif ARW == ARWEnum.Hi: return 'Hi'
    elif ARW == ARWEnum.Lo: return 'Lo'
    elif ARW == ARWEnum.HiLo: return 'HiLo'
    else:
        raise Exception('Invalid value for ARW (%d)' % ARW)

class ROVEnum(object):
    Close = 0
    Open = 1

def combineARW_OR(ARW1, ARW2):
    '''
    Return the OR combination of the two anti-reset-windup values (most restrictive)
    '''
    has_lo = False
    has_hi = False
    result = ARWEnum.HiLo
    
    # If either input is low limited, the output is low limited
    if ARW1 == ARWEnum.Lo or ARW1 == ARWEnum.HiLo or ARW2 == ARWEnum.Lo or ARW2 == ARWEnum.HiLo:
        has_lo = True

    # If either input is high limited, the output is high limited
    if ARW1 == ARWEnum.Hi or ARW1 == ARWEnum.HiLo or ARW2 == ARWEnum.Hi or ARW2 == ARWEnum.HiLo:
        has_hi = True

    # Convert low and high limit booleans into ARWEnum
    if not has_lo and not has_hi:
        result = ARWEnum.Normal
    elif has_lo and has_hi:
        result = ARWEnum.HiLo
    elif has_lo:
        result = ARWEnum.Lo
    elif has_hi:
        result = ARWEnum.Hi
    return result

def combineARW_AND(ARW1, ARW2):
    '''
    Return the AND combination of the two anti-reset-windup values (least restrictive)
    '''
    can_move_lo = False
    can_move_hi = False
    result = ARWEnum.HiLo

    # If either input can move low, the output can move low
    if ARW1 == ARWEnum.Normal or ARW1 == ARWEnum.Hi or ARW2 == ARWEnum.Normal or ARW2 == ARWEnum.Hi:
        can_move_lo = True

    # If either input can move high, the output can move high
    if ARW1 == ARWEnum.Normal or ARW1 == ARWEnum.Lo or ARW2 == ARWEnum.Normal or ARW2 == ARWEnum.Lo:
        can_move_hi = True

    # Convert low and high limit booleans into ARWEnum
    if can_move_lo and can_move_hi:
        result = ARWEnum.Normal
    elif not can_move_lo and not can_move_hi:
        result = ARWEnum.HiLo
    elif can_move_lo:
        result = ARWEnum.Hi
    elif can_move_hi:
        result = ARWEnum.Lo
    return result

def canMove(ARW, move_direction):
    '''
    Return True if the control with anti-reset-windup status ARW can move in the move_direction (down if Lo, up if Hi)
    (all below are from type ARWEnum)
    '''
    can_move = False
    if move_direction == ARWEnum.Lo:
        if ARW == ARWEnum.Normal or ARW == ARWEnum.Hi:
            can_move = True
    elif move_direction == ARWEnum.Hi:
        if ARW == ARWEnum.Normal or ARW == ARWEnum.Lo:
            can_move = True
    else:
        raise Exception("I'm confused - canMove was sent a move_direction other than Hi or Lo.")
    return can_move

from UserList import UserList
class xom1DDataSet(UserList):
    '''
    Our own version of the Ignition dataSet type, but better.
    This version is for DataSets with a single column.
    Use the first column if column_name is not given.
    '''
    def __init__(self, ds=(), column_name=''):
        if ds == ():
            self.ds = None
            self.data = []
            self.column_name = column_name
        else:
            self.ds = ds
            if not column_name:
                self.column_name = ds.getColumnName(0)
            self.data = []
            for row in range(ds.getRowCount()):
                self.data.append(ds.getValueAt(row, self.column_name))
        
    def updateDataSet(self):
        l = []
        for item in self.data:
            l.append([item])
        print 'l = %s' % str(l)
        self.ds = system.dataset.toDataSet([self.column_name], l)
        return self.ds
    
    def getMean(self):
        '''
        Returns the mean of the values in the data.
        '''
        return sum(self.data) / len(self.data)
    
    def getStandardDeviation(self):
        '''
        Returns the standard deviation of the values in the data.
        '''
        z = 0.0
        avg = float(self.getMean())
        for d in self.data:
            z += (float(d) - avg)**2.0
        return (z / float(len(self.data)-1))**0.5
        
        
def testxom1DDataSet():
    ds = system.dataset.toDataSet(['colname'], [['1'],['2'],['3']])
    xds = xom1DDataSet(ds)
    print xds
    xds.append('yo')
    print xds.updateDataSet()

    ds = system.dataset.toDataSet(['colname'], [[1],[2],[3]])
    xds = xom1DDataSet(ds)
    print 'avg = %f' % xds.getMean()
    print 'standard deviation = %f' % xds.getStandardDeviation()
    
    
    
    