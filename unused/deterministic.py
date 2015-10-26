def run_deterministic(machine, input_string):
    # Initial configuration
    config = (Store([START]), Store(input_string, 0)) + tuple(Store() for s in xrange(2, machine.num_stores))
    run = Run(machine, config)

    warned = False
    while True:
        if trace:
            print config

        if config[0].values[0] == ACCEPT:
            return run
        elif config[0].values[0] == REJECT:
            return run

        found = None
        for rule in machine.transitions:
            if rule.match(config):
                if found:
                    if not warned:
                        sys.stderr.write("warning: machine is not deterministic\n")
                        sys.stderr.write("  %s\n" % found)
                        sys.stderr.write("  %s\n" % rule)
                        warned = True
                else:
                    found = rule

        if found:
            nconfig = found.apply(config)
            run.add(config, nconfig)
            config = nconfig
        else:
            return run # reject

def is_deterministic(machine):
    # naive quadratic algorithm
    for i, t1 in enumerate(machine.transitions):
        for t2 in machine.transitions[:i]:
            match = True
            for in1, in2 in zip(t1.inputs, t2.inputs):
                # to do: make more concise
                i = -min(in1.position, in2.position)
                while i+in1.position < len(in1) and i+in2.position < len(in2):
                    x1 = in1.values[i+in1.position]
                    x2 = in2.values[i+in2.position]
                    if x1 != x2:
                        match = False
                    i += 1
            if match:
                return False
    return True

