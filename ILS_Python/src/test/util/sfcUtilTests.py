'''
Created on Oct 10, 2014

@author: rforbes
'''

import unittest
from testutil import FakeDataSet
from ils.sfc.util import *
from ils.sfc.steps import *
from com.inductiveautomation.ignition.common.config import BasicProperty, BasicPropertySet
from java.lang import String
exampleRef = '{local:selected-emp.val}'
exampleRef2 = '{local:selected-emp.age}'

class SfcUtilTests(unittest.TestCase):
    def createProperties(self):
        chartProperties = dict()
        stepProperties = BasicPropertySet()
        stepName = 'step'
        self.setStepProperty(NAME, stepName, stepProperties)
        chartProperties[BY_NAME] = dict()
        return chartProperties, stepProperties
        
    def setStepProperty(self, name, value, stepProperties):
        prop = BasicProperty(name, String)
        stepProperties.set(prop, value)
        
    def testSubstituteScopeReferences(self):
        chartProperties, stepProperties = self.createProperties()
        localScope = getLocalScope(chartProperties, stepProperties)
        selectedEmp = dict()
        selectedEmp['val'] = 5
        selectedEmp['age'] = 55
        localScope['selected-emp'] = selectedEmp
        sql = 'select * where val = ' + exampleRef + ' or val = ' + exampleRef2
        result = substituteScopeReferences(chartProperties, stepProperties, sql)
        expected = 'select * where val = 5 or val = 55'
        assert expected == result
    
    def testParseBracketedScopeReference(self):        
        location, key = parseBracketedScopeReference(exampleRef)
        assert location == 'local'
        assert key == 'selected-emp.val'

    def testFindBracketedScopeReference(self):     
        assert None == findBracketedScopeReference('asdfasdf')
        ref = findBracketedScopeReference('asdf' + exampleRef + 'yadda yadda')
        assert exampleRef == ref

    def testSimpleQueryProcessRowsStaticKey(self):
        chartProperties, stepProperties = self.createProperties()
        self.setStepProperty(RESULTS_MODE, UPDATE_OR_CREATE, stepProperties)
        self.setStepProperty(FETCH_MODE, SINGLE, stepProperties)
        self.setStepProperty(RECIPE_LOCATION, LOCAL, stepProperties)
        self.setStepProperty(KEY, 'value', stepProperties)
        self.setStepProperty(KEY_MODE, STATIC, stepProperties)
        dbRows = FakeDataSet(['a', 'b'], [['avalue', 'bvalue']])
        simpleQueryProcessRows(chartProperties, stepProperties, dbRows)
        localScope = getLocalScope(chartProperties, stepProperties)
        result = localScope['value']
        assert 'avalue' == result['a']
        assert 'bvalue' == result['b']
        
    def testSimpleQueryProcessRowsDynamicKey(self):
        chartProperties, stepProperties = self.createProperties()
        self.setStepProperty(RESULTS_MODE, UPDATE_OR_CREATE, stepProperties)
        self.setStepProperty(FETCH_MODE, SINGLE, stepProperties)
        self.setStepProperty(RECIPE_LOCATION, LOCAL, stepProperties)
        self.setStepProperty(KEY, 'dkey', stepProperties)
        self.setStepProperty(KEY_MODE, DYNAMIC, stepProperties)
        dbRows = FakeDataSet(['dkey', 'val'], [['key1', 'avalue'], ['key2', 'bvalue']])
        simpleQueryProcessRows(chartProperties, stepProperties, dbRows)
        localScope = getLocalScope(chartProperties, stepProperties)
        obj1 = localScope['key1']
        obj2 = localScope['key2']
        assert 'avalue' == obj1['val']
        assert 'bvalue' == obj2['val']
        
    def testPrint(self):
        obj= dict();
        obj['msg'] = 'Hi rob'
        obj2 = dict()
        obj['dict'] = obj2
        obj2['key'] = 'val'
        printObj(obj, 0)
    
        
