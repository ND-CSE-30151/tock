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


