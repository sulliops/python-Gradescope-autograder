# python-Gradescope-autograder
Template repository for Gradescope autograders used in Clemson CPSC-1011 during the F22 and S23 semesters.

Also includes test files to simulate runtime errors. These can be used to test included runtime error exceptions and methods.

----

## Files/Directories:
Each autograder has a standard set of files and directories that are used as part of one large script process.

1. `results/`: Folder generated by Gradescope that will contain a generated `results.json` (holds results of autograder tests after each run).
2. `submission/`: Folder generated by Gradescope that will contain any student-uploaded program files. In this repository, `submission/` is used to hold sample program files for each full autograder.
3. `source/`: Folder that contains source code/scripts for the Gradescope autograder.
4. `source/requirements.txt`: Text file that contains the names of any `pip3` packages that are required to be installed for autograders to function as expected.
5. `source/run_autograder`: Bash script that copies student-uploaded `.c` and `makefile` files from `submission/`, then runs `source/run_tests.py` to start unit tests.
6. `source/run_tests.py`: Python script that starts the unit testing process.
7. `source/setup.sh`: Bash script that installs Python and any `pip3` packages listed in `source/requirements.txt`.
8. *(Optional)* `makefile`: Makefile that compiles/runs student submissions, if students are not supplying their own Makefile.
9. *(Optional)* `source/input/`: Folder which may contain any input files that can be passed as stdin to a given test.
10. *(Optional)* `source/reference/`: Folder which may contain any sample output files that can be compared against in a given test.
11. `source/tests/`: Folder which contains Python scripts used in unit testing.
12. `source/tests/utils.py`: Python script which contains helper functions/methods that improve the unit testing process.
13. `source/tests/timeout.py`: Modified Python script (originally from [timeout_decorator.py](https://github.com/pnpnpn/timeout-decorator/blob/master/timeout_decorator/timeout_decorator.py)) that handles timeouts for individual test cases.
14. `source/tests/test_subprocess.py`: Main unit testing Python script, where test cases are written.

----

## Universal test cases:

Each version of `source/tests/test_subprocess.py` in this repository contains tests that should be included in all autograder testing.

1. `test_checkFiles`: A test that checks that students have submitted all required files for an assignment, based on an array of file names (found immediately before this test in `source/tests/test_subprocess.py`).
2. `test_Compile`: A test that compiles student programs by running `make`. This test can be modified as needed.

----

## Misc methods:
The other methods that are used as part of these autograders are likely irrelevant to beginners, as they work behind the scenes and do not require any tinkering to work properly for most purposes not explored in this repository.

However, here's a brief overview of some standout functions:

1. `@timeout.timeout(seconds, exception_message)`: This decorator allows for individual test timeouts (which allows the script to continue if a certain input causes an infinite loop, as opposed to causing the entire autograder to hang). `exception_message` should be populated with a call to `wrap(string, max_length)`.
2. `wrap(string, max_length)`: This function wraps long error messages to a specified length to allow them to be shown cleanly in the Gradescope interface. The recommended value for `max_length` is `65` characters.
3. `checkRuntimeErrors(proc, utest, stdout, stderr)`: This function determines if the `returncode` of a `subprocess.Popen` call matches any of the most common C program runtime errors. If a match is found, the constructor for a custom exception is called (which, in turn, calls `kill_fail(proc, utest, msg)` (except for Makefile return codes, which are handled separately).
4. `kill_fail(proc, utest, msg)`: This function kills the child process spawned by `subprocess.Popen`, disables the default `unittest` behavior of limiting long error messages, and fails the test with a message supplied by the caller.

----

## Usage:
To test any of these autograders, zip the contents of `source/` (recursively) and upload the resulting zip file to a Gradescope Programming Assignment then upload the relevant files from within `submission/` to test.

Alternatively, copy the file structure of a given sample autograder (including `results/`, `source/`, and `submission/`) recursively to the root of a server running Linux (Ubuntu 22.04 recommended). Then, run the following:

```
cd source
chmod +x run_autograder
./run_autograder
```
