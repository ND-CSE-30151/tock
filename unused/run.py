import formats
import automata

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Simulate an automaton.')
    parser.add_argument('machine_filename', metavar='file', help='CSV or TGF file specifying automaton.')
    parser.add_argument('input_string', metavar='input', nargs='?', help='input string (optional).')
    parser.add_argument('--show-rules', help='show compiled rules', action="store_true", dest="show_rules")
    args = parser.parse_args()

    if args.machine_filename.lower().endswith(".csv"):
        machine = formats.read_csv(open(args.machine_filename))
    elif args.machine_filename.lower().endswith(".tgf"):
        machine = formats.read_tgf(open(args.machine_filename))
    else:
        sys.stderr.write("couldn't recognize filename extension: %s" % args.machine_filename)

    if args.show_rules:
        print machine

    deterministic = automata.is_deterministic(machine)
    if deterministic:
        print "machine is deterministic"
    #if automata.is_finite_state(machine):
    #    print "machine is finite-state"

    if args.input_string is not None:
        if deterministic:
            run = automata.run_deterministic(machine, args.input_string)
        else:
            run = automata.run_bfs(machine, args.input_string)
        print run
    else:
        while True:
            try:
                input_string = raw_input("> ")
            except EOFError:
                print ""
                break
            if deterministic:
                print automata.run_deterministic(machine, input_string)
            else:
                print automata.run_bfs(machine, input_string)
