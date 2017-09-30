#!/usr/bin/env python
#
#  Split a master roster for a XC meet into separate rosters for each
# of the four standard divisions: Fun-run, 3-4, 5-6, and 7-8.
#
import os, sys
import os.path
import csv
import argparse

def parse_args(args):
    parser= argparse.ArgumentParser(
            description="Split a master roster into event rosters")
    parser.add_argument("master",
            help="input roster, with all meet participants")
    parser.add_argument("--by-school", action='store_true',
            help="Sort roster by school and last name.")
    parser.add_argument("--by-name", action='store_true',
            help="Sort roster last name and grade.")
    parser.add_argument("--ids", action='store_true',
            help="Replace existing ID numbers")
    parser.add_argument("-debug", action="store_true",
            help="Produce debugging output")
    opt = parser.parse_args(args)
    return opt

def write_roster(filename, runners, fields):
    with open(filename, "w") as roster:
        writer = csv.DictWriter(roster, fields)
        writer.writeheader()
        count = 0
        errors = 0
        for runner in runners:
            try:
                writer.writerow(runner)
                count += 1
            except Exception as exc:
                errors += 1
                print("## ID={} : {}".format(runner.get('ID', '??'), str(exc)))
    if errors > 0:
        print("Wrote {} runners to {}  ({} errors)".format(count, filename, errors))
    else:
        print("Wrote {} runners to {}".format(count, filename))

def order_by_school(a):
    return (a['School'], a['Last name'], a['Grade'])

def order_by_race(a):
    return (group(a), a['Last name'], a['Grade'])

def order_by_name(a):
    return (a['Last name'], a['Grade'])

def group(r):
    if r['Grade'] in '34' and r['Gender'] == 'M':
        return "g34_boys"
    elif r['Grade'] in '34' and r['Gender'] == 'F':
        return "g34_girls"
    elif r['Grade'] in '56' and r['Gender'] == 'M':
        return "g56_boys"
    elif r['Grade'] in '56' and r['Gender'] == 'F':
        return "g56_girls"
    elif r['Grade'] in '78' and r['Gender'] == 'M':
        return "g78_boys"
    elif r['Grade'] in '78' and r['Gender'] == 'F':
        return "g78_girls"
    else:
        return "fun"

def main(args):
    opt = parse_args(args)
    print("Master roster:", opt.master)

    all_runners = []
    with open(opt.master, "r") as master:
        reader = csv.DictReader(master)
        fields = reader.fieldnames
        for row in reader:
            all_runners.append(row)

    if opt.by_school:
        all_runners.sort(key=order_by_school)
    else:
        all_runners.sort(key=order_by_name)
    schools = set([r['School'] for r in all_runners])
    races = set([group(r) for r in all_runners])

    print(len(all_runners), "runners loaded from", opt.master)
    print(len(schools), "schools represented")
    print(len(races), "races will be run")

    max_id = 0
    missing_ids = 0
    if 'ID' in fields:
        for runner in all_runners:
            try:
                runner['ID'] = int(runner['ID'])
                if runner['ID']:
                    if runner['ID'] > max_id:
                        max_id = runner['ID']
            except:
                missing_ids += 1
        print("({} missing IDs)".format(missing_ids))
    else:
        fields.insert(0, 'ID')
        for runner in all_runners:
            runner['ID'] = None

    if opt.ids:
        # re-assign ID numbers
        max_id = 0
    
    for runner in all_runners:
        if opt.ids or not runner['ID']:
            max_id = max_id + 1
            runner['ID'] = max_id

    print("Fields: ", ", ".join(fields))

    name, ext = os.path.splitext(os.path.basename(opt.master))

    master_roster = "{}_master.csv".format(name)
    write_roster(master_roster, all_runners, fields)

    for race in races:
        roster = "{meet}_{race}.csv".format(meet=name, race=race)
        runners = [r for r in all_runners if group(r) == race]
        runners.sort(key=order_by_name)
        write_roster(roster, runners, fields)

    for school in schools:
        roster = "{meet}_{school}.csv".format(meet=name, school=school)
        runners = [r for r in all_runners if r['School'] == school]
        runners.sort(key=order_by_race)
        write_roster(roster, runners, fields)

if __name__ == '__main__':
    main(sys.argv[1:])
