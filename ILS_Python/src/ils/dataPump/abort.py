'''
Created on Jun 20, 2017

@author: phass
'''
def abort(tagProvider):
    import system
    system.tag.writeToTag("%sConfiguration/Data Pump/command" % (tagProvider), "Abort")