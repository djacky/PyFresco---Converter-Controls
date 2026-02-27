.. pyfresco documentation master file, created by
   sphinx-quickstart on Wed Jun 24 16:42:57 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Python Frequency RESponse-based Controller Optimization (PyFresco)
==================================================================

Welcome to the PyFresco documentation page! This document will outline the basic functions and methods used in PyFresco. 
This toolbox is used to design controllers for the voltage, current and field loops in the CERN power converter 
control system. The toolbox also offers several methods for measuring the frequency response function (FRF) 
of the open-loop and closed-loop responses. The FRF's for the open-loop responses can be used to synthesize 
controllers in cases where the dynamics of the converter/magnet are unknown or where high robustness/performance 
is needed. 

A tutorial on the functions used by PyFresco can be accessed by clicking on the Tutorial link on the left pane. 
The API Documentation displays the main objects and methods to call in order to execute the controller synthesis 
commands or frequency response measurements. There is also an Examples section to help the user understand the 
main functionality of PyFresco. 

Installation
------------

PyFresco can be easily installed with PyPI by calling

.. code-block:: console
   
   pip install pyfresco

PyFresco has the following dependencies:

- Python 3.6 or 3.7
- PyFGC :math:`\geq` 1.4.1
- NumPy :math:`\geq` 1.18.5
- CVXPY :math:`\geq` 1.1.1
- CVXOPT :math:`\geq` 1.2.5
- Control :math:`\geq` 0.8.3
- Pandas :math:`\geq` 1.0.5
- Tabulate :math:`\geq` 0.8.7
- SciPy :math:`\geq` 1.5.2


Contents:

.. toctree::
   :maxdepth: 1

   tutorial/main.rst
   api_doc/main.rst
   examples/main.rst
