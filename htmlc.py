import optparse
import os.path
import subprocess
import sys
import re

cmd_start = "{"
cmd_end = "}"
esc = "\\"

yes = ["y", "yes"]

usage = "usage: %prog input [-o output] [-nva] [-e excluded1 [-e excluded2 [...]]]"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-o", "--output", action="store", dest="output", help="Write generated HTML to the given file or directory rather than stdout")
parser.add_option("-n", "--keep-newlines", action="store_true", dest="keep_newlines", help="Prevent trailing newline being stripped from command output", default=False)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Produce verbose output", default=False)
parser.add_option("-a", "--ask", action="store_true", dest="ask", help="Ask before overwriting file", default=False)
parser.add_option("-e", "--exclude", action="append", dest="excluded", help="Specify a regex matching files to exclude")

(opts, args) = parser.parse_args()

if (len(args) != 1):
    parser.error("expected 1 required positional argument: input")

def ask(msg):
    return input("[?] " + msg)

def info(msg):
    print("[i] " + msg)

def error(msg):
    print("[!] " + msg)
    exit()

def compile(in_path, out_path):
    if opts.verbose:
        if out_path == None:
            info("Compiling " + in_path)
        else:
            info("Compiling " + in_path + " -> " + out_path)

    contents = None

    fin = open(in_path, "r")
    contents = fin.read()
    fin.close()

    if contents == None:
        error("Failed to read " + in_path)

    if opts.ask and out_path is not None and os.path.exists(out_path):
        if ask("Overwrite " + out_path + "? [y/N] ").lower() not in yes:
            if opts.verbose:
                info("Skipping " + in_path + " (overwrite rejected manually)")
            return

    fout = (open(out_path, "w") if out_path is not None else sys.stdout)

    cmd = None
    escaped = False
    for c in contents:
        if c == cmd_start and not escaped and cmd == None:
            cmd = ""
        elif c == cmd_end and not escaped and cmd != None:
            out = subprocess.check_output(cmd, shell=True, text=True)
            if not opts.keep_newlines:
                out = out.rstrip("\n")
            fout.write(out)
            cmd = None
        elif c == esc and not escaped:
            escaped = True
        else:
            escaped = False
            if cmd != None:
                cmd += c
            else:
                fout.write(c)

    if out_path is not None:
        fout.close()

def traverse(in_path, out_path):
    if os.path.isfile(in_path):
        for ex in opts.excluded:
            if re.match(ex, in_path):
                if opts.verbose:
                    info("Skipping " + in_path + " (matched excluded regex " + ex + ")")
                return
        compile(in_path, out_path)
    elif os.path.isdir(in_path):
        if out_path is not None and not os.path.exists(out_path):
            os.mkdir(out_path)
        subs = os.listdir(in_path)
        for sub in subs:
            new_in = in_path + "/" + sub
            new_out = out_path + "/" + sub if out_path != None else None
            traverse(new_in, new_out)
    else:
        error("Could not find " + in_path)

in_path = args[0]
out_path = opts.output

in_f = os.path.isfile(in_path)
out_f = out_path is not None and os.path.isfile(out_path)
in_d = os.path.isdir(in_path)
out_d = out_path is not None and os.path.isdir(out_path)

if in_d:
    if out_f:
        error("Cannot compile directory into file")
    else:
        traverse(in_path, out_path)
else:
    if out_d:
        traverse(in_path, out_path + "/" + os.path.split(in_path)[1])
    else:
        traverse(in_path, out_path)
