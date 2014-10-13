'''
Created on Sep 16, 2014

@author: rforbes
'''

FACTOR = 'FACtor'
ALIAS = 'ALIas'
BASEUNIT = 'BASEUNIT'

if __name__ == '__main__':
    import emc.units
    unitfile = 'C:/root/repo/svn/EMChemicals/G2Artifacts/Unit Conversion/Standard.units'
    emc.units.parseUnitFile(unitfile)

# Read a unit file and convert it into Unit objects
def parseUnitFile(unitfile):
    import ils.common.units
    
    unitsByName = dict()

    for line in open(unitfile, 'r').xreadlines():
        isFactor = line.find(FACTOR) != -1
        isAlias = line.find(ALIAS) != -1
        isComment = line[0] == '*'
        
        if isComment or not(isFactor | isAlias):
            continue
        description = ''
        
        # extract the description, if there is one (ignore alias descriptions tho)
        exclamIndex = line.find('!')
        if exclamIndex != -1: # trailing description
            description = line[exclamIndex+1 : len(line)].strip()
            line = line[0 : exclamIndex]
        
        quotedToken = None
        tokens = []
        for token in line.split():
            if quotedToken != None:
                if token.endswith('"'):
                    quotedToken = quotedToken + token
                    tokens.append(quotedToken[1 : len(quotedToken)-1])
                    quotedToken = None
            elif token.startswith('"'):
                quotedToken = token
            else :
                tokens.append(token)
                
        name1 = tokens[1]
        name2 = tokens[2]
        if isFactor:
            unit = ils.common.units.Unit()
            unit.isBaseUnit = tokens[3] == BASEUNIT
            unit.name = name1
            unit.type = name2
            unit.description = description
            unitsByName[unit.name] = unit
            if not unit.isBaseUnit:
                unit.m = float(tokens[3].replace('D', 'E'))
                unit.b = float(tokens[4].replace('D', 'E'))
 
        elif isAlias:
            realUnit = unitsByName[name2]
            if realUnit != None:
                unitsByName[name1] = realUnit       
            else:
                errMsg = "unit " + name2 + " for alias " + name1 + " not found"
    
    return unitsByName
    
