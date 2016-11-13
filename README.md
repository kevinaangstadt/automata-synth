## Getting Started

1. Make a docker image:

        $ cd klee
        $ docker build -t klee/klee .

2. Create a docker container:

        $ docker run -ti --name=automata-synth --ulimit='stack=-1:-1' klee/klee

3. `update-alternatives` messes up trying to install python2 for mercurial

        $ sudo update-alternatives --remove python /usr/bin/python3

4. Install `nano` and `mercurial`

5. Clone this repository
