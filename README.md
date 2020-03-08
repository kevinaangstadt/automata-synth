# AutomataSynth

AutomataSynth is a framework for converting certain classes of functions to a
format that can be executed by modern hardware accelerators, such as FPGAs.
AutomataSynth dynamically observes and statically analyzes program behavior to
learn a behaviorally-equivalent finite automaton that can be transformed into a
hardware description.

Currently, there is support for C Boolean string kernels (i.e., functions with a
high-level type signature `String -> bool`).  For kernels deciding a regular
language, the theoretical AutomataSynth algorithm can learn a fully-equivalent
model.  In the general case, AutomataSynth will learn an approximate model that
is correct up to some fixed input length.

## Requirements

AutomataSynth requires the following software:

- Python 2
- Java 9 or 11
- Ant

Additionally, see `requirements.txt` for a list of required python packages.

## Getting Started

AutomataSynth has been tested on Ubuntu 18.04.  Your mileage on other platforms
will vary.

**Note:** Run `setup.sh` to automatically install all required packages and
*build the required submodules.

### Prepare to Run
Either run `setup.sh` or use the following steps.

1. Install the required software packages (see above).

2. Clone this repository

  ```
  git clone https://github.com/kevinaangstadt/automata-synth
  ```

3. Initialize the repository's submodules

  ```
  cd automata-synth
  git submodule update --init
  ```

4. Build CPAChecker.

  ```
  cd cpachecker
  ant
  ```

### Basic Usage

We assume that the code to be transformed lives in some "kernel directory".
When specifying a kernel file, this should be relative to this directory.

The entry point of AutomataSynth is `cpabmcseq-test-driver.py`.  Run this script
without any arguments to see a help message describing the various command line
arguments.

### Example

You may try AutomataSynth on one of the provided test kernels.  For example:

```bash
./cpabmcseq-test-driver.py --time-limit 5m --kernel-file kernel.c \
  --kernel-function kernel --return-int --max-inp-length 5 test_kernels/astarb \
  test-output
```

## Publications

The following publications are associated with AutomataSynth:

- Kevin Angstadt, Jean-Baptiste Jeannin, and Westley Weimer. Accelerating Legacy
  String Kernels via Bounded Automata Learning. In _Proceedings of the 25th
  International Conference on Architectural Support for Programming Languages
  and Operating Systems_, ASPLOS '20. Lausanne, Switzerland, 2020. ACM.

## Acknowledgements

This work is funded in part by: NSF grants CCF-1629450, CCF-1763674,
CCF-1908633; AFRL Contract No. FA8750-19- 1-0501; and the Jefferson Scholars
Foundation. We also wish to thank Kevin Skadron and Lu Feng for their
suggestions, encouragement, and expertise in the early stages of this project as
well as the anonymous reviewers for their helpful comments and feedback.
