'''
Created on Jun 20, 2017

@author: phass
'''
def abort(tagProvider):
    import system
    system.tag.writeToTag("%sData Pump/command" % (tagProvider), "Abort")