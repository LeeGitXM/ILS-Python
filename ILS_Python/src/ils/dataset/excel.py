'''
Methods useful for exporting a python dataset as XML
in a format conducive for import by MSExcel. All methods
return a string.

Created on Nov 26, 2014
'''
import java.text.SimpleDateFormat as SimpleDateFormat

# This is the comprehensive writer. Accept a dictionary of
# datasets keyed by worksheet name. Return the string equivalent
# as Excel XML.
def toExcel(datasets):
    s = []
    s.append(header())
    for key in datasets.keys():
        s.append(sheetHeader(key))
        data = datasets.get(key)
        s.append(sheetData(data))
        s.append(sheetTrailer())
    s.append(trailer())
    return ''.join(s)

# Column type of a dataset is a Java class. Convert it to an 
# appropriate string for Excel.
def columnTypeToString(ctype):
    ans = "String"
    cname = ctype.getSimpleName()
    if cname == 'String':
        ans = "String"
    elif cname == 'Boolean':
        ans = "String"
    elif cname == 'Double':
        ans = "Number"
    elif cname == 'Float':
        ans = "Number"
    elif cname == 'Long':
        ans = "Number"
    elif cname == 'Integer':
        ans = "Number"
    elif cname == 'Short':
        ans = "Number"
    elif cname == 'Date':
        ans = "DateTime"
    else:
        print "WARNING: ils.dataset.excel.columnTypeToString: Unknown column type: "+cname
    return ans

# Boilerplate XML header
def header():
    text = '<?xml version="1.0"?>\n'\
            '<?mso-application progid="Excel.Sheet"?>\n'\
            '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\n'\
            '          xmlns:o="urn:schemas-microsoft-com:office:office"\n'\
            '          xmlns:x="urn:schemas-microsoft-com:office:excel"\n'\
            '          xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\n'\
            '          xmlns:html="http://www.w3.org/TR/REC-html40">\n'\
            '<DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">\n'\
            '</DocumentProperties>\n'\
            '<ExcelWorkbook xmlns="urn:schemas-microsoft-com:office:excel"><WindowHeight>600</WindowHeight><WindowWidth>800</WindowWidth><WindowTopX>0</WindowTopX><WindowTopY>0</WindowTopY><ProtectStructure>False</ProtectStructure><ProtectWindows>False</ProtectWindows></ExcelWorkbook>\n'\
            '<Styles><Style ss:ID="Default" ss:Name="Normal"><Alignment ss:Vertical="Bottom"/><Borders/><Font/><Interior/><NumberFormat/><Protection/></Style><Style ss:ID="s21"><NumberFormat ss:Format="General Date"/></Style><Style ss:ID="s23"><Alignment ss:Horizontal="Right" ss:Vertical="Bottom"/><Font x:Family="Swiss" ss:Bold="1"/></Style></Styles>\n'
    return text

# Accumulate the string representation of an entire dataset.
def sheetData(data):
    ISO_FORMAT = "yyyy-MM-dd'T'HH:mm:ss.SSS";
    sdf = SimpleDateFormat(ISO_FORMAT)
    s = []
    s.append(tableHeader(data))
    for row in range(data.rowCount):
        s.append("<Row>\n")
        for col in range(data.columnCount):
            ctype = data.getColumnType(col)
            dtype = columnTypeToString(ctype)
            if dtype=='DateTime':
                value = sdf.format(data.getValueAt(row,col))
                s.append('<Cell ss:StyleID="s21"><Data ss:Type="'+dtype+'">'+value+'</Data></Cell>\n')
            else:
                value= str(data.getValueAt(row,col))
                s.append('<Cell><Data ss:Type="'+dtype+'">'+value+'</Data></Cell>\n')
        s.append('</Row>\n')
    s.append(tableTrailer())
    return ''.join(s)
# Boilerplate header for a worksheet.
# Argument is the sheet name
def sheetHeader(sheetName):
    text = '<Worksheet ss:Name="'+sheetName+'">\n'
    return text

# This version adds a header row
def tableHeader(data):
    text = '<Table ss:ExpandedColumnCount="'+str(data.columnCount)+'" ss:ExpandedRowCount="'+str(data.rowCount+1)+'" x:FullColumns="1" x:FullRows="1"\n'\
            '      ss:DefaultColumnWidth="65" ss:DefaultRowHeight="15">\n'\
            '<Column ss:Width="75.75"/>\n'
    s = []
    s.append(text)
    s.append('<Row>\n')
    for col in range(data.columnCount):
        title = data.getColumnName(col)
        s.append('<Cell ss:StyleID="s23"><Data ss:Type="String">'+title+'</Data></Cell>\n')
    s.append('</Row>\n')
    return ''.join(s)

    
# Boilerplate closing elements for a worksheet.
def sheetTrailer():
    text =  '<WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">\n'\
            '<Panes></Panes>\n'\
            '<ProtectObjects>False</ProtectObjects>\n'\
            '<ProtectScenarios>False</ProtectScenarios>\n'\
            '</WorksheetOptions>\n'\
            '</Worksheet>\n' 
    return text

def tableTrailer():
    text = '</Table>\n'
    return text

# Boilerplate closing elements for the workbook.
def trailer():
    text = '</Workbook>\n' 
    return text