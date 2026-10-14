#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##  $HeadURL $
##  $Revision$
##  $LastChangedDate$
##  $LastChangedBy$
##

import sys
import csv


def main(args):
    form_name = args.formname.replace('.', '_')
    ### Creating the dictionary file
    headerdatadic = args.headerdatadic.lower().split('\n')
    name = args.name.split('\n')

    rows = [['Variable / Field Name,Form Name,Section Header,Field Type,'
             'Field Label,Choices Calculations OR Slider Labels,Field Note,'
             'Text Validation Type OR Show Slider Number,Text Validation Min,'
             'Text Validation Max,Identifier?,Branching Logic (Show field only '
             'if...),Required Field?,Custom Alignment,Question Number '
             '(surveys only),Matrix Group Name,Matrix Ranking?'],
            # First row.
            ['subject,{},,text,NCANDA Subject Identification Number,,,'
             'N-CANDA Subject ID,,,,,,,,,'.format(form_name)],
            # Second row.
            ['arm,{},,text,NCANDA Protocol,,,,,,,,,,,,'.format(form_name)],
            # Third row.
            ['visit,{},,text,Visit,,,Date (Y-M-D),,,,,,,,,'.format(
                form_name)]]

    if args.measuredatadic:
        measuredatadic = args.measuredatadic
        measuredatadic = measuredatadic.lower().replace(", ", ",").split("\n")

        for m in measuredatadic:
            m_list = m.split(",")
            field_label = m_list[1].title()
            rows.append(
                ["measure_{0},{3},,text,{1},,{2},Number,,,,,,,,,".format(
                    m_list[0], field_label, m_list[2], form_name)])

    for l in name:
        field_name = l.lower().replace('-', '_').replace('.', '_', )
        struct_label = l.replace('-',
                                 ' ').replace('_',
                                              ' ').replace('.', ' ').title()
        count = 0
        while count < len(headerdatadic):
            if headerdatadic[count][-1:] == " ":
                headerdatadic[count] = headerdatadic[count][:-1]
            if headerdatadic[count] != "structname":

                field_label = ' '.join([struct_label,
                                        headerdatadic[count + 1].title()])
                headerdatadic_final = [
                    "{0}_{1},{4},,text,{2},,{3},Number,,,,,,,,,".format(
                        field_name, headerdatadic[count], field_label,
                        headerdatadic[count + 2], form_name)]
                rows.append(headerdatadic_final)
            count += 3

    with open(args.datadicfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter='\n', lineterminator="\n")
        for row in rows:
            writer.writerow(row)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--measuredatadic', action="store",
                        help="Where the data dictionary for the measures is "
                             "stored.")
    parser.add_argument('--headerdatadic', action="store",
                        help="Where the data dationary for the header is "
                             "stored.")
    parser.add_argument('--datadicfile', action="store",
                        help="Where the datadic file name will be stored.")
    parser.add_argument('--name', action="store",
                        help="Where the names for the fields will be stored.")
    parser.add_argument('--formname', action="store",
                        help="Where the names for the fields will be stored.")
    argv = parser.parse_args()
    sys.exit(main(args=argv))
