#!/usr/bin/env python3

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL $
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

import csv
import sys
import os 
import re

from csv import DictReader, DictWriter
# to preserve order of dictionary - do not delete 
from collections import OrderedDict

def main(args):
    # Creating the csv file.
    # Processing raw strings.

    if args.template : 
       if not os.path.isfile(args.template): 
           print("Error: " + args.template + " does not exist!")
           sys.exit(1)

       with open(args.template,'r') as csvfile:
          reader = DictReader(csvfile, delimiter=',', lineterminator="\n")
          output = OrderedDict.fromkeys(reader.fieldnames)
          
    header_list = args.name.lower().replace('-', '_').split('\n')
    header_type = args.headertemp.lower().split(' ')
    # Creating Fields
    table_header = ""
    for l in header_list:
        for col in header_type:
            if col != "":
                table_header = "{0}{1}_{2},".format(table_header, l, col)
 
    # get rid of the last comma 
    table_header=table_header[:-1]

    if args.measurevalue:
        measurevalue = args.measurevalue.lower().replace('\n', ',')
        add_values = ",".join([measurevalue, args.table[:-1]])

        measureheader_final = ""
        for field in args.measureheader.lower().split('\n'):
            field_norm = field.replace('-', '_')
            measureheader_final = "{0}measure_{1},".format(measureheader_final,field_norm)

        add_header=",".join([measureheader_final[:-1],table_header])
    else:
        add_values = args.table[:-1]
        add_header = table_header

    # Processing Rows - only writes out two rows 
    header = [",".join(['subject,arm,visit',add_header])]
    table = [",".join([args.subject, args.arm, args.visit, add_values])]
    
    # only works for one line 
    if args.template : 
       for name,value in zip(header[0].split(','), table[0].split(',')):
           if name in output.keys():
               output[name] = value
           else:
             print(name,'not found')
            
    else :
        output=[header,table] 

    with open(args.filename, 'w', newline='') as csvfile:
         if args.template :   
            writer = DictWriter(csvfile,output.keys(),lineterminator="\n")
            writer.writeheader()
            writer.writerow(output)

         else :
            writer = csv.writer(csvfile, delimiter='\n', lineterminator="\n")
            for row in output:
                writer.writerow(row) 

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--template', help='template file', action="store")
    parser.add_argument('--headertemp', help='column names for values of --table', action="store")
    parser.add_argument('--table', action="store",
                        help="values extracted from stats table.")
    parser.add_argument('--name', action="store",
                        help="Where Name is stored.")
    parser.add_argument('--filename', action="store",
                        help="Where the file name is stored.")
    parser.add_argument('--subject', action="store",
                        help="name of subject")
    parser.add_argument('--arm', action="store",
                        help="arm")
    parser.add_argument('--visit', action="store",
                        help="visit")
    parser.add_argument('--measurevalue', action="store",
                        help="values from stats file that were not part of table")
    parser.add_argument('--measureheader', action="store",
                        help="column names associated with values from --measurevalue")
    argv = parser.parse_args()
    sys.exit(main(args=argv))
