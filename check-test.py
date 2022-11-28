#!/usr/bin/python3

from optparse import OptionParser
import sys
import fileinput
import yaml
from yaml import load, dump
import os.path

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

usage = "usage: %prog [options] TEST"
parser = OptionParser(usage=usage)
parser.add_option('-t', '--tests', dest='test_file', metavar='FILE', default='tests.yml', help='Get tests from the given file.')
parser.add_option('-l', '--log', dest='log_file', metavar='FILE', help='Log file to test.')
(options, args) = parser.parse_args()

if (not os.path.isfile(options.test_file)):
    sys.exit("The file %s does not exist. Define a test file (where the expected output of the tests are defined) with the option -t" % options.test_file)


with open(options.test_file, 'r') as stream:
    try:
        tests_yaml=yaml.load(stream, Loader=Loader)
    except yaml.YAMLError as exc:
        print(exc)

def searchTest(i,n):
    return i['name']==n

if len(args) != 1:
    sys.exit("The name of the case to test is missed. It can be any of the followings:\n"+'\n'.join([ i['name'] for i in tests_yaml ]))

ts = [ i for i in tests_yaml if searchTest(i,args[0]) ]

if len(ts) != 1:
    sys.exit("The name of the case to test is not found. It can be any of the followings:\n"+'\n'.join([ i['name'] for i in tests_yaml ]))


if (options.log_file is not None and not os.path.isfile(options.log_file)):
    sys.exit("The file %s does not exist. Define the log file to analyse with -l or pipe it to the stdin." % options.log_file)

t=ts[0]['to_pass']
t.reverse()
l= [] if options.log_file is None else [options.log_file]

result='Failed!'
to_match=t.pop()

logfile = open(l[0], 'r')
Lines = logfile.readlines()

for line in Lines:
    ls=line.split()
    print(ls)

    if ('evadroid:' not in ls):
        continue

    if to_match not in ls:
        continue

    if len(t)==0:
       result='Pass!'
       break
    to_match=t.pop()

print(result)
