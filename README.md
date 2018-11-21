# Installation

- You will need to be running an Unix-like operating system (works on macOS and most Linux distributions)
- You will need to have Python 3.7.0 or later installed
- You will need to have a C++ compiler installed

# Running

All the following commands assume your current working directory is the folder containing this README file.
To do that, run `cd path/to/folder`.

- To exclusively convert the algorithm to a C++ file, run `python3 compile.py FILE` replacing `FILE` with the path to the algorithm.
- To parse and compile the algorithm into a binary executable, run `python3 compile.py FILE compile` replacing `FILE` with the path to the algorithm.
- To parse, compile, and run the algorithm from the binary executable, run `python3 compile.py FILE run` replacing `FILE` with the path to the algorithm.

# Features

Currently, AlgoCompile supports:

- Global variables
- Main program function
- Additional functions

- Function calls
- Variable assignments
- In-line arithmetic (+, -, \*, /, %, =, ≠, <, >, ≥, ≤, and, or, |, &, ^)
- `if`, `else if`, `else` conditions
- `while` loops
- `do`...`while` loops
- `for` loops
- `switch`...`case` statements

AlgoCompile does NOT support:
- `while` loops directly inside `do`...`while` loops (requires changing `while condition` to `while condition do`)
- `if` conditions directly after `else` blocks (requires preventing line breaks inside `else if` keywords)

For example, this program will fail to parse (thus to compile or run too):
```
VAR: x: integer
BEGIN
  do
    Write("Please enter a number: ")
    Read(x)

    while x > 0
#   ^ problem is here
      Write(x, "\n")
      x <- x - 1
    end while
#       ^ error is located here
  while x < 0
END
```

Workaround:
```
VAR: x: integer
BEGIN
  do
    Write("Please enter a number: ")
    Read(x)

    if true then # Moving the while loop one block further down fixes the issue, here an always-true condition is used
      while x > 0
        Write(x, "\n")
        x <- x - 1
      end while
    end if
  while x < 0
END
```

The following program will also fail to parse (thus to compile or run too):
```
VAR: x: integer
BEGIN
  Write("Please enter a number: ")
  Read(x)

  if x > 0 then
    Write(x, " is positive.\n")
  else
    if x < 0 then
#   ^ problem is here
      Write(x, " is negative.\n")
    else
      Write(x, " is zero.\n")
    end if

    Write(x, " is not positive.\n")
  end if
#     ^ error is located here
END
```

Workaround:
```
VAR: x: integer
BEGIN
  Write("Please enter a number: ")
  Read(x)

  if x > 0 then
    Write(x, " is positive.\n")
  else
    Write("") # Adding a non-whitespace and non-comment character between the else and if fixes the issue, here a no-op function is used

    if x < 0 then
      Write(x, " is negative.\n")
    else
      Write(x, " is zero.\n")
    end if

    Write(x, " is not positive.\n")
  end if
END
```

# TODO

- Handle arrays/matrices
- Handle returns, breaks, and continues
- Remove useless parenthesis in formulas
- Fix changed arguments (pointer arithmetic)
