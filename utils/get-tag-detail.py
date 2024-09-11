import re
import argparse

parser = argparse.ArgumentParser(description='Get Tag Detail.')
parser.add_argument('tag', metavar='tag', nargs=1,
                    help='tag')

args = parser.parse_args()

m = re.match(r"(\w*-[0-9a-z]*)-(.*)-v(.*)", args.tag[0])

print(m.group(1) + "###" + m.group(2) + "###" + m.group(3))