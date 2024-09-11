#
# Example python script to generate a BOM from a KiCad generic netlist
#
# Example: Sorted and Grouped CSV BOM
#

"""
    @package
    Output: CSV (comma-separated)
    Grouped By: Value, Footprint
    Sorted By: Ref
    Fields: Ref, Qnty, Value, Cmp name, Footprint, Description, Vendor

    Command line:
    python "pathToFile/bom_csv_grouped_by_value_with_fp.py" "%I" "%O.csv"
"""

# Import the KiCad python helper module and the csv formatter
import kicad_netlist_reader
import kicad_utils
import csv
import sys
import xlsxwriter
import json
import copy
import re

def convertFootprint(category, footprint):
    fp = re.split(":", footprint)[1]

    conn_regex = re.compile(r'Conn_.*')
    
    if category == 'C' or category == 'R' or category == 'D' or category == 'L' or category == 'D_Zener' or category == 'Fuse':
        fp_short = re.split("_", fp)[1]
    elif category == 'C_Polarized':
        fp_short = re.split("_", fp)[2]
    elif category == 'Buzzer':
        fp_short = re.split("RM", re.split("_", fp)[1])[0]
    elif category == 'INDUCTOR':
        fp_short = re.split("_", fp)[2]
    elif category == 'L_Coupled_1213':
        fp_short = re.split("_", fp)[2]
    elif re.match(conn_regex, category):
        fp_short = ''
    else:
        fp_short = re.split("_", fp)[0]

    # print(fp_short)

    return fp_short

# A helper function to convert a UTF8/Unicode/locale string read in netlist
# for python2 or python3
def fromNetlistText( aText ):
    if sys.platform.startswith('win32'):
        try:
            return aText.encode('utf-8').decode('cp1252')
        except UnicodeDecodeError:
            return aText
    else:
        return aText

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
net = kicad_netlist_reader.netlist(sys.argv[1])
# Opening JSON file
try:
    jsonf = open(sys.argv[2])
    brds = json.load(jsonf)
except:
    brds = {"boards": [{"name": "default", "nc": ""}]}
brdSize = sys.argv[3]
workbook = xlsxwriter.Workbook(sys.argv[4])

for brd in brds['boards']:
    # print(brd)
    sheet = workbook.add_worksheet(brd['name'])

    try:
        funs = brds["refer"]["functions"]
        funsAdd = {}
        funsDelete = funs.copy()

        for fun in brd["functions"]:
            # print(fun)
            try:
                funsAdd[fun] = funsDelete.get(fun)
                funsDelete.pop(fun)
            except:
                print("do not have key %s" % fun)
        
        refsDelete = ""
        for key, value in funsDelete.items():
            refs = value["refs"]
            if refs[-1] != ",":
                refs += ","
            refsDelete += refs

        refsAdd = ""
        for key, value in funsAdd.items():
            refs = value["refs"]
            if refs[-1] != ",":
                refs += ","
            refsAdd += refs

            ncs = value["nc"]
            if ncs != "":
                print("add ncs")
                if ncs[-1] != ",":
                    ncs += ","
                refsDelete += ncs
        
        refsDeleteList = refsDelete[:-1].split(',')
        refsAddList = refsAdd[:-1].split(',')

        realRefsDeleteList = []
        for i in refsDeleteList:
            if i not in refsAddList:
                realRefsDeleteList.append(i)
        # print(refsDeleteList)
        # print(realRefsDeleteList)
        # print(refsAddList)
    except:
        realRefsDeleteList = []

    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)
    sheet.set_zoom(100)
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 1, 40)
    sheet.set_column(2, 2, 60)

    title_style = workbook.add_format(
        {"bold": True, "bg_color": "#FFFFCC", "bottom": 1}
    )

    # Output a set of rows for a header providing general information
    sheet_title = ["Comment", "Designator", "Footprint"]
    sheet.write_row(0, 0, sheet_title, title_style)

    # Get all of the components in groups of matching parts + values
    # (see ky_generic_netlist_reader.py)
    grouped = net.groupComponents()

    i = 1

    cell_format = workbook.add_format({'top': 1, 'bottom': 1})
    cell_format.set_text_wrap()
    cell_format.set_align('vcenter')
    cell_format.set_bold(False)

    outList = []
    componentsToModify = []
    # Output all of the component information
    for group in grouped:
        refs = ""

        # Add the reference of every component in the group and keep a reference
        # to the component so that the other data can be filled in once per group
        num = 0
        for component in group:
            ref = fromNetlistText(component.getRef())

            if ref not in realRefsDeleteList:
                if "modifies" in brd:
                    refMatch = 0
                    for item in brd["modifies"]:
                        if ref == item["ref"]:
                            cc = copy.deepcopy(component)
                            cc.setValue(item["value"])
                            componentsToModify.append(cc)
                            refMatch = 1

                    if refMatch == 0:
                        refs += ref + ", "
                        num +=1
                else:
                    refs += ref + ", "
                    num +=1

            c = component

        if num == 0:
            continue

        footprint = c.getFootprint().split(':')[1]
        val = c.getValue()

        if val.find('NC/') != -1 or val == 'NC' or footprint.find('TestPoint') != -1:
            continue  

        fp = convertFootprint(c.getPartName(), c.getFootprint())
        
        outList.append({"refs": refs, "num": num, "value": c.getValue()})

        sheet.write(i, 0, c.getValue(), cell_format)
        sheet.write(i, 1, refs, cell_format)
        sheet.write(i, 2, fp, cell_format)

        i += 1

    if componentsToModify != []:
        for component in componentsToModify:
            ref = fromNetlistText(component.getRef())
            value = component.getValue()
            j = 0
            valueMatch = 0

            for item in outList:
                if value == item["value"]:
                    valueMatch = 1
                    item["refs"] = item["refs"] + ref + ", "
                    item["num"] = item["num"] + 1
                    sheet.write(j + 1, 1, item["refs"], cell_format)
                j += 1

            if valueMatch == 0:
                sheet.write(i, 0, component.getValue(), cell_format)
                sheet.write(i, 1, ref + ", ", cell_format)
                sheet.write(i, 2, component.getFootprint(), cell_format)
                i += 1

    i += 1

workbook.close()
