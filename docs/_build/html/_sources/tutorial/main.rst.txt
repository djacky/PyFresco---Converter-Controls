Tutorial
========

PyFresco includes two packages that each perform different functions: 
the Optimization-based Controller Design (ObCD) package and the Frequency Response Measurement (FRM) package. 

ObCD
-----
    
The purpose of this tool is to synthesize controllers for the voltage, current,
and/or field loops in the power converter control system. The algorithms use advanced 
convex optimization methods to synthesize these controllers by using the frequency 
response of a given open-loop system. The ObCD package uses the Python convex optimization library
`CVXPY <https://www.cvxpy.org/>`__ to synthesize the controllers for all
the control loops. This library contains several free solvers that can
be used for obtaining an optimal solution. PyFresco uses the
`ECOS <https://web.stanford.edu/~boyd/papers/ecos.html>`__ and
`CVXOPT <https://cvxopt.org/>`__ solvers, as these solvers are needed
for the types of problems used by PyFresco (i.e., semi-definite programming
(SDP) problems).The desired performance is obtained by minimizing 
a weighted norm of the appropriate sensitivity function; the user will be able to 
select what kind of performance is desired in the advanced properties of the tool. In 
synthesizing these controllers, the user can provide a model (by setting the correct 
FGC properties) or by measuring the appropriate frequency response function (i.e., 
the open-loop dynamics). 

.. toctree::
   :maxdepth: 1

   current_field.rst
   voltage.rst

FRM
---

This tool enables a user to obtain the frequency response between two desired signals; this frequency 
response can be used for general analysis purposes (i.e., confirming the behavior of a load or the 
performance of a controller) or to design a regulator. This measurement tool is important in applications 
where the load dynamics are uncertain (i.e., uncertain magnet parameters or delay) or for applications where 
the effects of Eddy currents are significant. There are two methods that are implemented in the FGC for 
measuring these dynamics:

- A `sine-fit algorithm <https://www.sciencedirect.com/science/article/pii/S0019057811001182>`__ which calculates the magnitude 
  and phase of a system at user-defined frequency points.
- A method which injects a pseudorandom binary sequence (PRBS), which is a signal similar to white noise 
  and excites all frequencies.  

Each of these methods both have advantages and disadvantages (which will be discussed in this document).  
The measured frequency response of the open-loop system can also be used to design a regulator. With the 
frequency response data of a system, the data-driven methods in the ObCD package can be used to ensure the 
desired performance and robustness of a closed-loop power converter control system. If the user is interested 
in designing controllers for the voltage, current, and/or field loops, then the following frequency responses 
should be obtained (with either PRBS or sine-fit):

- For voltage control (:ref:`Control Mode <control_mode>` = ``V``):

  - :ref:`Input <ref_mode>`: F_REF_LIMITED
  - :ref:`Output <meas_mode>`: [I_CAPA, V_MEAS_REG, I_MEAS]

- For current control (:ref:`Control Mode <control_mode>` = ``I``):

  - :ref:`Input <ref_mode>`: V_REF
  - :ref:`Output <meas_mode>`: I_MEAS

- For field control (:ref:`Control Mode <control_mode>` = ``B``):

  - :ref:`Input <ref_mode>`: V_REF
  - :ref:`Output <meas_mode>`: B_MEAS

The measured frequency response represents the ratio of the Fourier transforms of the input and output signals 
(i.e., :math:`G(j\omega) = \mathcal{F}\{\text{Output} \} / \mathcal{F}\{\text{Input} \}`, 
where :math:`\mathcal{F}\{\cdot \}` signifies the Fourier transform of the argument).

Remark:
 When using the sine-fit or PRBS method, a stabilizing RST controller must be loaded into the FGC for both open-loop 
 and closed-loop experiments. This is due to the fact that the measurement algorithm is initialized in closed-loop mode 
 in order to obtain a proper DC gain measurement and reduce drift. If a stabilizing controller is not available and the 
 current or field loops are unstable, one can set the values below in the following properties:

 .. math::

   \begin{aligned}
      &\text{REG.I/B.EXTERNAL.OP.R }& \alpha \text{ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0} \\
      &\text{REG.I/B.EXTERNAL.OP.S }& \text{1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0} \\
      &\text{REG.I/B.EXTERNAL.OP.T }& \alpha \text{ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0} \\
      &\text{REG.I/B.EXTERNAL_ALG[x] }& \text{ENABLED} \\
   \end{aligned}

 where :math:`x` is selected using the property LOAD.SELECT, which can have a value between 0 and 3, and :math:`\alpha` is an 
 arbitrarily small (positive) constant. Since the open-loop system is stable for any load (assuming that the voltage source 
 is stable), there will always exist an arbitrarily small :math:`\alpha` that will stabilize the closed-loop system.

.. toctree::
   :maxdepth: 1

   prbs.rst
   sine.rst


