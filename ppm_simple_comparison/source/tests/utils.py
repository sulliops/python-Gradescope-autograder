import os
from shutil import copyfile
from time import sleep
import subprocess
import signal
import re
import textwrap
import difflib
from pathlib import Path
import os

# Gets the location of the `autograder` folder
# Isn't actually necessary to run on Gradescope, but it allows for easier testing on local machines
# where /autograder/ may not be a valid path.
def getAutograderDir() -> str:
    return '/'.join(__file__.split('/')[:-3])

# Checks if all the expected files are present, and raises an error if any of them are missing
# Is used by the `test_checkFiles` test case
def checkFiles(files: list):
    autograderDir = getAutograderDir()
    submissionDir = autograderDir + '/submission/'

    # Array containing the full path location for every submitted file. Typically is `/autograder/submission/myFile`,
    # but this is written to be more robust to allow for easier local testing
    allFiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(submissionDir) for f in filenames]

    # Array containing the full path to every file that the student submitted that was *expected*
    # In other words, this array discards any files submitted that weren't expected to be submitted
    submittedFiles = [i for i in allFiles if i.split('/')[-1] in files]

    # This seems weird - it should yield the exact same array as `submittedFiles`, unsure why this exists lol
    filesSubmitted = list()
    for file in files:
        for fileDir in submittedFiles:
            if fileDir.split('/')[-1] == file:
                filesSubmitted.append(fileDir.split('/')[-1])

    # Get list of expected files that are missing from submission
    filesMissing = [file for file in files if file not in filesSubmitted]

    # If any files are missing, throw an error and display the missing files
    if len(filesMissing) != 0:
        raise AssertionError("\n" + wrap("You are missing the following files:\n{}".format(', '.join(filesMissing)), 65))

# Function that uses checkFiles to determine whether the compile test should continue
def checkSourceFiles(utest, files: list):
    try:
        checkFiles([file for file in files if file.endswith('.c') or file == 'Makefile' or file == 'makefile'])
    except (AssertionError):
        utest.assertTrue(False, msg=wrap(filesMissingErrorMessage, 65))
        
# Function that checks for the existence of executables to determine whether an output test should continue
def checkExecutables(utest, executables: list):
    if not executables:
        utest.assertTrue(False, msg=wrap(compileFailedErrorMessage, 65))
    
    for executable in executables:
        if not Path(executable).is_file():
            utest.assertTrue(False, msg=wrap(compileFailedErrorMessage, 65))

# Series of functions that handle extra lines when comparing output with 
# reference files
# Thanks Eliza Sorber
def nonEmptyLine(s):
    return len(s.strip()) != 0
    
def stripstr(s):
    return re.sub(' +', ' ', s.strip())

def removeEmptyLines(text):
    lst = filter(nonEmptyLine, list(map(stripstr, text.split("\n"))))
    return "\n".join(list(lst)) + "\n"

decodeErrorMessage = 'Your program printed a character that the autograder cannot decode. Ensure your program prints valid characters.'
uninitializedCharacterMessage = 'Your program printed an uninitialized char variable, which the autograder cannot decode. Ensure your program prints valid characters.'
compileDecodeErrorMessage = 'The compiler failed to read a character in your source code. This is most likely caused by submitting a compiled executable, as opposed to source code. Ensure you are submitting code, and not an executable.'
compileTimeoutErrorMessage = 'The autograder timed out while trying to compile your program. If your program is compiled using a makefile, ensure your makefile is not malformed.'
programTimeoutErrorMessage = 'Your program timed out while running this test case, likely due to an infinite loop or an issue accepting inputs. Ensure your program does not loop infinitely, and make sure the test inputs are handled correctly.'
compileFailedErrorMessage = 'The test cannot be run because the submitted program did not compile successfully. Ensure your program compiles without warnings.'
filesMissingErrorMessage = 'Compilation cannot continue because the submission does not include all of the required files. Ensure you\'re submitting all of the correct files.'

findLastExecutableCommand = "find -type f -executable ! -name 'run_autograder' -printf '%T@ %p\n' | sort -n | tail -1 | awk '{print $2}'"
removeLastExecutableCommand = "find -type f -executable ! -name 'run_autograder' -printf '%T@ %p\n' | sort -n | tail -1 | awk '{print $2}' | xargs rm -r"

# Function that kills the process that runs the student's program,
# then fails the test with a pre-defined message
def kill_fail(proc, utest, msg):
    proc.kill()
    utest.assertTrue(False, wrap(msg, 65))

# Series of exception classes that allow raising runtime exceptions
# All of these just call kill_fail function
class RuntimeAbort(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

class RuntimeSegFault(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

class RuntimeFPE(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

class RuntimeBusError(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

class RuntimeIllegalInstruction(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

class MakefileError(Exception):
    def __init__(self, proc, utest, msg):
        kill_fail(proc, utest, msg)

# Function to check subprocess process for common runtime error signals
# Raises exceptions with custom messages for test failures
def checkRuntimeErrors(proc, utest, stdout, stderr):
    if ((abs(proc.returncode) % 128) == int(signal.SIGABRT)):
        raise RuntimeAbort(proc, utest, 'Your program triggered runtime error SIGABRT. Check for compilation warnings, use GDB to track down the cause of this error, or Google this error for more information.')
    elif ((abs(proc.returncode) % 128) == int(signal.SIGSEGV)):
        raise RuntimeSegFault(proc, utest, 'Your program encountered a segmentation fault. Check for compilation warnings, use GDB to track down the cause of this error, or Google this error for more information.')
    elif ((abs(proc.returncode) % 128) == int(signal.SIGFPE)):
        raise RuntimeFPE(proc, utest, 'Your program triggered runtime error SIGFPE (typically caused by dividing by zero). Check for compilation warnings, use GDB to track down the cause of this error, or Google this error for more information.')
    elif ((abs(proc.returncode) % 128) == int(signal.SIGBUS)):
        raise RuntimeBusError(proc, utest, 'Your program triggered runtime error SIGBUS. Check for compilation warnings, use GDB to track down the cause of this error, or Google this error for more information.')
    elif ((abs(proc.returncode) % 128) == int(signal.SIGILL)):
        raise RuntimeIllegalInstruction(proc, utest, 'Your program triggered runtime error SIGILL (typically caused by stack smashing). Check for compilation warnings, use GDB to track down the cause of this error, or Google this error for more information.')
    elif ((abs(proc.returncode) % 128) == int(signal.SIGINT)):
        raise MakefileError(proc, utest, stderr.strip().decode('utf-8'))

# Function to wrap strings for cleaner output in Gradescope
def wrap(string, width):
    return textwrap.fill(string, width)

# safe_repr copied from unittest utils library
def safe_repr(obj, short=False):
    try:
        result = repr(obj)
    except Exception:
        result = object.__repr__(obj)
    if not short or len(result) < 80:
        return result
    return result[:80] + ' [truncated]...'

# Custom formatMessage from unittest library
def formatMessage(self, msg, standardMsg):
    if not self.longMessage:
        return msg or standardMsg
    if msg is None:
        return standardMsg
    try:
        # don't switch to '{}' formatting in Python 2.X
        # it changes the way unicode input is handled
        return '%s:%s' % (standardMsg, msg)
    except UnicodeDecodeError:
        return '%s:%s' % (safe_repr(standardMsg), safe_repr(msg))

# Custom version of unittest assertMultiLineEqual tailored to make
# diff checks more readable
def customAssertMultiLineEqual(self, first, second, msg=None):
    """(Custom) Assert that two multi-line strings are equal."""
    self.assertIsInstance(first, str, 'First argument is not a string')
    self.assertIsInstance(second, str, 'Second argument is not a string')

    if first != second:
        # don't use difflib if the strings are too long
        if (len(first) > self._diffThreshold or
            len(second) > self._diffThreshold):
            self._baseAssertEqual(first, second, msg)
        firstlines = first.splitlines(keepends=True)
        secondlines = second.splitlines(keepends=True)
        if len(firstlines) == 1 and first.strip('\r\n') == first:
            firstlines = [first + '\n']
            secondlines = [second + '\n']
        # standardMsg = '%s != %s' % _common_shorten_repr(first, second)
        standardMsg = ''
        diff = '\n' + ''.join(difflib.ndiff(firstlines, secondlines))
        standardMsg = self._truncateMessage(standardMsg, diff)
        self.fail(formatMessage(self, standardMsg, msg).rstrip('\n'))
        
# Custom exception for use when uninitialized characters are detected
class UninitializedCharError(Exception):
    pass
        
# Function that checks for uninitialized characters in program output
# This should check for '\u0000', which is not caught by UnicodeDecodeError
def checkForUninitializedChars(str):
    if '\u0000' in str:
        raise UninitializedCharError
    else:
        return str