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
    sheet.set_column(0, 0, 40)
    sheet.set_column(1, 1, 5)
    sheet.set_column(2, 2, 30)
    sheet.set_column(3, 3, 30)
    sheet.set_column(4, 4, 60)
    sheet.set_column(5, 6, 15)

    title_style = workbook.add_format(
        {"bold": True, "bg_color": "#FFFFCC", "bottom": 1}
    )

    # Output a set of rows for a header providing general information
    sheet.write_row(0, 0, ['Source:', net.getSource()])
    sheet.write_row(1, 0, ['Date:', net.getDate()])
    sheet.write_row(2, 0, ['Tool:', net.getTool()])
    sheet.write_row(3, 0, ['Generator:', sys.argv[0]])
    sheet.write_row(4, 0, ['Component Count:', len(net.components)])
    sheet_title = ["Ref", "Qnty", "Value", "Cmp name", "Footprint", "Manufacturer", "Vendor"
    ]
    sheet.write_row(5, 0, sheet_title, title_style)

    # Get all of the components in groups of matching parts + values
    # (see ky_generic_netlist_reader.py)
    grouped = net.groupComponents()

    i = 6

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
        
        outList.append({"refs": refs, "num": num, "value": c.getValue()})

        sheet.write(i, 0, refs, cell_format)
        sheet.write(i, 1, str(num), cell_format)
        sheet.write(i, 2, c.getValue(), cell_format)
        sheet.write(i, 3, c.getPartName(), cell_format)
        sheet.write(i, 4, c.getFootprint(), cell_format)
        sheet.write(i, 5, c.getField("Manufacturer"), cell_format)
        sheet.write(i, 6, c.getField("Vendor"), cell_format)

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
                    sheet.write(j + 6, 0, item["refs"], cell_format)
                    sheet.write(j + 6, 1, str(item["num"]), cell_format)
                j += 1

            if valueMatch == 0:
                sheet.write(i, 0, ref + ", ", cell_format)
                sheet.write(i, 1, str(1), cell_format)
                sheet.write(i, 2, component.getValue(), cell_format)
                sheet.write(i, 3, component.getPartName(), cell_format)
                sheet.write(i, 4, component.getFootprint(), cell_format)
                sheet.write(i, 5, component.getField("Manufacturer"), cell_format)
                sheet.write(i, 6, component.getField("Vendor"), cell_format)
                outList.append({"refs": ref + ", ", "num": 1, "value": component.getValue()})
                i += 1
    i += 1
    sheet.write(i, 1, str(1), cell_format)
    sheet.write(i, 2, brdSize, cell_format)
    sheet.write(i, 3, "PCB", cell_format)
    i += 1

workbook.close()
