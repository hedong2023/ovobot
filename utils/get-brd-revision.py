import pcbnew
import argparse

parser = argparse.ArgumentParser(description='Get Board Revision.')
parser.add_argument('file', metavar='file', nargs=1,
                    help='Board file')

args = parser.parse_args()

brd = pcbnew.LoadBoard(args.file[0])
tb = brd.GetTitleBlock()
ver = tb.GetRevision()
size = tb.GetComment(0)

layerCnt = brd.GetCopperLayerCount()

print(ver + "###" + size + "###" + str(layerCnt))