#!/usr/bin/env python3

import re
import os
import sys
import time

import parsers
import outputs
import utils

def compile(file, out_c, out_h):
    text = utils.strip_comments(file.read())

    try:
        active_parsers = [parsers.FileParser(outputs.FileOutput(out_c), outputs.FileOutput(out_h))]

        offset = 0
        stuck = False

        while offset < len(text) and active_parsers:
            active_parser = active_parsers[0]

            diff = active_parser.ends(text[offset:])
            if diff >= 0:
                offset += diff
                active_parsers.pop(0)
                stuck = False
                continue

            for child_class in active_parser.children():
                diff, child = child_class.starts(text[offset:], active_parser)
                if child is not None:
                    offset += diff
                    active_parsers.insert(0, child)
                    stuck = False
                    break
            else:
                diff = active_parser.parse(text[offset:])
                if diff > 0:
                    offset += diff
                elif stuck:
                    raise Exception("Stucked parsing in %s." % (active_parser.__class__.__name__))
                else:
                    stuck = True

        if not active_parsers and offset < len(text):
            raise Exception("Failed to parse.")

        while active_parsers:
            diff = active_parsers[0].ends(text[offset:])
            if diff >= 0:
                offset += diff
                active_parsers.pop(0)
                continue
            else:
                break

        if offset >= len(text) and active_parsers:
            raise Exception("Reached end of file unexpectedly while in [%s]." % ", ".join(map(lambda x: x.__class__.__name__, active_parsers)))
    except Exception as e:
        tmp_file = "tmp"
        if os.path.isfile("%s.alg" % tmp_file):
            i = 0
            while os.path.isfile("%s_%d.alg" % (tmp_file, i)):
                i += 1
            tmp_file = "%s_%d" % (tmp_file, i)

        with open("%s.alg" % tmp_file, "w") as file:
            file.write("# Generated with AlgoCompile\n")
            file.write("#             by Aurélien Garnier\n")
            file.write("#\n")
            file.write("# Failed to compile the following file.\n")
            file.write("# Comments and empty lines were stripped.\n")
            file.write("#\n")
            file.write("# %s\n" % str(e).replace("\\", "\\\\").replace("\n", "\\n"))
            file.write("# Position: %d\n" % offset)
            file.write(text)

        raise e

def main():
    if len(sys.argv) <= 1:
        print("Usage: %s <file> [parse/compile/run]" % sys.argv[0])
        return

    if len(sys.argv) >= 3 and not sys.argv[2].lower() in ["run", "true", "1", "yes", "y", "parse", "false", "0", "no", "n", "build", "compile"]:
        print("Usage: %s <file> [parse/compile/run]" % sys.argv[0])
        return

    if not os.path.isfile(sys.argv[1]):
        print("Error: File does not exist at %s" % sys.argv[1])
        return

    if not os.access(sys.argv[1], os.R_OK):
        print("Error: You don't have read permission for %s" % sys.argv[1])
        return

    bin_file = re.sub(r"^(.*)\.alg$", r"\1", sys.argv[1])
    c_file = "%s.cpp" % bin_file
    h_file = "%s.h" % bin_file

    with open(sys.argv[1], "r") as file:
        with open(c_file, "w") as out_c:
            with open(h_file, "w") as out_h:
                start = time.time()

                out_c.write("// Generated with AlgoCompile\n")
                out_c.write("//             by Aurélien Garnier\n")
                out_c.write("\n")
                out_c.write("#include \"%s\"\n" % h_file)
                out_c.write("\n")

                out_h.write("// Generated with AlgoCompile\n")
                out_h.write("//             by Aurélien Garnier\n")
                out_h.write("\n")
                out_h.write("#include <cmath>\n")
                out_h.write("#include <string>\n")
                out_h.write("#include <iostream>\n")
                out_h.write("\n")

                compile(file, out_c, out_h)

                end = time.time()
                print("Successfully parsed in %f seconds." % (end - start))

    if len(sys.argv) >= 3 and sys.argv[2].lower() in ["run", "true", "1", "yes", "y", "build", "compile"]:
        start = time.time()
        if os.system("c++ %s -o %s" % (c_file, bin_file)) == 0:
            end = time.time()
            print("Successfully compiled in %f seconds." % (end - start))
        else:
            return

    if len(sys.argv) >= 3 and sys.argv[2].lower() in ["run", "true", "1", "yes", "y"]:
        print("Running...")
        os.system("./%s" % bin_file)

if __name__ == "__main__":
    main()
