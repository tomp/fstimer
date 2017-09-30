#!/usr/bin/env python
#
#  Take a registration file (CSV or JSON)
#  and write a JSON timing dictionary for fstimer.
#
#  Required fields in the registration file:
#  First name, Last name, Gender, Grade, School, ID
#
import os, sys
import os.path
import json
import csv
import argparse

req_fields = set(["ID", "First name", "Last name", "Gender", "Grade", "School"])

def load_registration(regfile):
    """
    Loads a registration file.  A list of dicts is returned.
    Each dict includes all of the required keys.
    """
    name, ext = os.path.splitext(regfile)
    if ext == '.json':
        return load_json_regfile(regfile)
    elif ext == '.csv':
        return load_csv_regfile(regfile)
    else:
        raise ValueError("Unrecognized file type '{}'".format(ext))

def load_json_regfile(regfile):
    with open(regfile, "rU") as fp:
        runners = json.load(fp)
    fields = set()
    fields.update([r.keys() for r in runners])
    return runners, fields

def load_csv_regfile(regfile):
    with open(regfile, "rU") as reg:
        reader = csv.DictReader(reg)
        fields = reader.fieldnames
        runners = list(reader)
    return runners, fields

def write_json_regfile(regfile, runners):
    with open(regfile, "wb") as fp:
        json.dump(runners, fp, sort_keys=True, indent=4)
    print("Wrote {} runners to regfile '{}'".format(len(runners), regfile))
    
def write_timing_dict(timingfile, runners):
    timing_dict = dict([(r['ID'], r) for r in runners])
    with open(timingfile, "wb") as fp:
        json.dump(timing_dict, fp, sort_keys=True, indent=4)
    print("Wrote {} runners to timing file '{}'".format(len(runners), timingfile))

def parse_args(args):
    parser= argparse.ArgumentParser(
            description="Convert a registration CSV file into a JSON registration file and a timing dictionary")
    parser.add_argument("infile",
            help="input CSV file, with all participants for a given race")
    parser.add_argument("-debug", action="store_true",
            help="Produce debugging output")
    opt = parser.parse_args(args)
    return opt

def main(args):
    opt = parse_args(args)

    if os.path.isdir(opt.infile):
        name = os.path.basename(opt.infile)
        infile = os.path.join(opt.infile, name+".csv")
    else:
        infile = opt.infile
    print("Registration info from", infile)

    runners, fields = load_registration(infile)
    if not req_fields.issubset(fields):
        raise KeyError("required fields are missing")

    name, ext = os.path.splitext(infile)
    regfile = "{}_registration_prereg.json".format(name)
    timingfile = "{}_timing_dict.json".format(name)

    write_json_regfile(regfile, runners)
    write_timing_dict(timingfile, runners)

if __name__ == '__main__':
    main(sys.argv[1:])
