'''Recipe to create either a docker container or Singularity image
for a "machine" to prepare demo material on an HPC system.  It contains
tools like asciinema, demo-magic as well as Linux tools such as nano
and other software required for basic demos.

Usage:
    $ hpccm  --recipe demo_machine.py  --format docker
    $ hpccm  --recipe demo_machine.py  --format singularity
'''

from pathlib import Path


# Choose a base image
Stage0.baseimage('ubuntu:22.04')
 
# Install editor and other tools
Stage0 += apt_get(ospackages=['vim', 'less', 'ack', 'nano', ])

# Install archive and compression software and utitlies
Stage0 += apt_get(ospackages=['tar', 'gzip', 'bzip2', 'wget', 'ca-certificates', ])

# Install version control
Stage0 += apt_get(ospackages=['git', 'openssh-client', ])

# Install benchmarking tools
Stage0 += apt_get(ospackages=['hyperfine', ])

# Install screencast software
Stage0 += apt_get(ospackages=['asciinema', ])

# Install demo-magic
Stage0 += apt_get(ospackages=['pv', ])
Stage0 += copy(src='demo_magic/demo-magic.sh',
               dest='/demo-magic/demo-magic.sh',
               _mkdir=True)
