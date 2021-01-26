'''
Created on Jan 19, 2021

'''
import system

def setChartsForExport(charts):
    projectName = system.util.getProjectName()
    filename = system.file.saveFile(projectName, "sproj", "SFC and Recipe data project")
    print filename
    for path in charts:
        print "Chart: ", path
        xml = charts.get(path)
        print xml
        print "======================"