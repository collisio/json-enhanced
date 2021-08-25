Installation
============

Pip installation
----------------

This package can be installed via pip, by simply typing:

``pip install json-enhanced``

Docker's set up
---------------

Additionally, if you have Docker installed on your Linux system, we provide a bash script, called ``build.sh``,
which comes preloaded with the entire ecosystem of the library; the main modules and objects, and a predefined ``test`` variable with some json data.
You can access an Ipython terminal by entering the following command:

``bash build.sh``

Also, if you want to load a local resource from your host system into the container, you can point to it with an additional argument on the script's call:

``bash build.sh <resource_path>``

