Voltage Control
===============

The basic structure of the voltage loop is shown in
:numref:`voltage_block`. It is recommended that the user consult
`this document <https://edms.cern.ch/document/2001105/1>`__ before
continuing, as the discussion here will be an extension to that content.
For a more detailed diagram of the FGC implementation strategy, `click
here. <http://proj-fgc.web.cern.ch/proj-fgc/images/platforms/fgc3/vreg.png>`__

For the remaining portions of this documentation, the notation
:math:`\mathcal{S}_{xy}` will be used to represent the sensitivity
function from a signal :math:`x` to a signal :math:`y`. For all
controller designs within the FGC, the *desired* closed-loop transfer
function (technically the *complementary sensitivity function*) is
selected as a (delayed) standard second-order system:

.. math::

   \label{eq:2nd_order}
   \mathcal{S}_{ry}^d(s) = \frac{\omega_{d}^2}{s^2 + 2\zeta \omega_{d} s + \omega_{d}^2} e^{-sd_r},

where :math:`r` is the input reference, :math:`y` is the output,
:math:`\zeta \:` is the *desired* damping factor, :math:`d_r` is the
*desired* reference delay and

.. math:: \omega_d = 2 \pi f_d \left[ 1-2\zeta^2 + \sqrt{2-4\zeta^2 + 4\zeta^4} \right]^{-0.5},

where :math:`f_{d}` [Hz] is the *desired* closed-loop bandwidth of the
system.

From :numref:`voltage_block`, it can be observed that there are two
main loops to control; the damping loop :math:`\mathcal{S}_{v_d v_0}`
and the voltage loop :math:`\mathcal{S}_{v_r v_0}`. PyFresco implements an
optimization strategy which first calculates the damping loop parameters
:math:`\rho_d = \{k_i, k_d, k_u \}` and then uses those parameters to
formulate :math:`\mathcal{S}_{v_d v_0}` (note that
:math:`k_w = 1+k_u+D_mk_d`, where :math:`D_m` is the dc-gain of the
magnet :math:`M(s)`). With :math:`\mathcal{S}_{v_d v_0}`, the voltage
loop parameters :math:`\rho_v = \{k_{ff}, k_p, k_{int}\}` (with
:math:`C(z^{-1}) = k_p + k_{int}T_v(1-z^{-1})^{-1}`, and :math:`T_v` [s]
being the voltage loop sampling time) can then be efficiently
calculated. This two-step process is performed to convexify the
optimization constraints and avoid the problems that can occur with
bi-linear terms. As with the RST synthesis, the user will have the
option to minimize either the :math:`\mathcal{H}_\infty` or
:math:`\mathcal{H}_2` criterion. Both of these methods will now be
discussed for each loop.

.. _voltage_block:
.. figure:: pics/voltage_loop.png
   :alt: ILC structure

   Interconnection of the power converter control system (voltage
   source).

Damping Loop Design
-------------------

The (closed-loop) transfer function for the damping loop can be
expressed as
:math:`\mathcal{S}_{v_d v_0}(\rho_d) = Gk_w\psi_d^{-1}(\rho_d)` where

.. math:: \psi_d(\rho_d) = 1+G(k_iHe^{-s\tau_i} + k_dMe^{-s\tau_i} + k_ue^{-s\tau_v})

\ and :math:`G = G_0e^{-s\tau_b}` (where the ADC’s and sensors are
approximated as pure delays :math:`\tau_i` [s] and :math:`\tau_v` [s]).
The delay :math:`\tau_b` [s] represents the delay approximation of the
power block. Generally, for 6-pulse thyristor converters, this “delay”
can be approximated to have a value of :math:`1.6667`\ ms. For a
12-pulse converter, it would be half of this value. The value of
:math:`\tau_b` should be correctly set in the FGC property
`VS.FIRING.DELAY <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyVS.htm#VS.FIRING.DELAY>`__.

.. _mathcalh_infty-control-1:

:math:`\mathcal{H}_\infty` Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method_v>`]

In the :math:`\mathcal{H}_\infty` sense, the objective is to minimize
:math:`\|W_d(1 - \mathcal{S}_{v_dv_0}) \|_\infty`; an equivalent
representation of this objective is to minimize :math:`\gamma` such that
:math:`\|W_d(1 - \mathcal{S}_{v_dv_0})  \|_\infty^2 < \gamma` (which is
the epigraph form of the minimization criterion). This criterion is
satisfied if the following optimization problem is considered:

.. math::

   \begin{aligned}
           & \underset{ \rho_d,\gamma}{\text{minimize}}
           & & \gamma  \\
           & \text{subject to:} & & \left[W_d(1-\mathcal{S}_{v_dv_0}(\rho_d)) \right]^{\star} \left[W_d(1-\mathcal{S}_{v_dv_0}(\rho_d)) \right] < \gamma \\
           & & & \rho_d \geq 0 \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`W_d = (1-\mathcal{S}_{v_dv_0}^d)^{-1}` (with
:math:`\mathcal{S}_{v_dv_0}^d` being the desired second-order response).
The desired :ref:`bandwidth <damp_bw>`, :ref:`damping <damp_z>`, and
:ref:`reference delay <ref_delay_v>` are taken into account with :math:`W_d`.
The second constraint in the problem ensures that the damping loop gains
are all greater than zero (which is a desired requirement asserted by TE-EPC
to ensure that proper debugging can take place; each individual loop within
the damping loop can be tested without any phase inversion).
As was discussed in the :ref:`RST synthesis <rst_hinf_control>`,
the above problem is convexified as follows:

.. math::

   \begin{aligned}
           & \underset{ \rho_d,\gamma}{\text{minimize}}
           & & \gamma  \\
           & \text{subject to:} & & \gamma^{-1} \left|W_d(\psi_d(\rho_d)-Gk_w) \right|^2   < 2\Re \left\{\psi_d(\rho_d) \psi_d^{\star}(\rho_{d,0}) \right\} - \left|\psi_d(\rho_{d,0}) \right|^2 \\
           & & &  \Delta M_d^2 < 2\Re \left\{\psi_d(\rho_d) \psi_d^{\star}(\rho_{d,0}) \right\} - \left|\psi_d(\rho_{d,0}) \right|^2 \\
           & & & \rho_d \geq 0 \\
           & & & \forall \omega \in \Omega
       \end{aligned}

where :math:`\rho_{d,0}` is the initial stabilizing controller.
The second constraint in this problem ensures that the damping loop
possesses a minimum :ref:`modulus margin <damp_mm>` :math:`\Delta M_d`. For the
damping loop, PyFresco sets :math:`\rho_{d,0}` to small positive constants;
this is sufficient to ensure the stability of the damping loop. The same
iterative procedure (as detailed in :ref:`RST synthesis <rst_hinf_control>`) is then performed to obtain the
optimal solution.

.. _mathcalh_2-control-1:

:math:`\mathcal{H}_2` Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method_v>`]

A similar linearization process can be used to obtain
:math:`\mathcal{H}_2` performance for the damping and voltage loops. An
optimization problem can be formulated for minimizing the square of the
:math:`\mathcal{H}_2` model-reference damping loop objective (i.e.,
minimizing
:math:`\|W_{d_2}(\mathcal{S}_{v_dv_0}(\rho_d) - \mathcal{S}_{v_dv_0}^d) \|_2^2`);
the optimization problem for this criteria can be expressed as follows:

.. math::

   \begin{aligned}
           & \underset{ \rho_d, \gamma,\Gamma}{\text{minimize}} & & \gamma=\int_{-\pi / {T_v}}^{\pi / {T_v}} \Gamma(\omega) d\omega  \\
           & \text{subject to:} & & \left[W_{d_2}(\mathcal{S}_{v_dv_0}(\rho_d) - \mathcal{S}_{v_dv_0}^d)\right]^{\star} \left[W_{d_2}(\mathcal{S}_{v_dv_0}(\rho_d) - \mathcal{S}_{v_dv_0}^d)\right] < \Gamma(\omega) \\
           & & & \rho_d \geq 0 \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`\Gamma(\omega) \in \mathbb{R}_+` is an unknown function of
:math:`\omega` and :math:`W_{d_2} = 2 \pi \cdot` :ref:`damp_bw <damp_bw>`
:math:`\cdot s^{-1}`. As with the :ref:`RST synthesis <rst_hinf_control>`,
this :math:`\mathcal{H}_2` optimization problem can
be convexified and efficiently solved as follows:

.. math::

   \begin{aligned}
       & \underset{ \rho_d, \gamma, \Gamma}{\text{minimize}} & &  \gamma=\int_{-\pi / {T_v}}^{\pi / {T_v}} \Gamma(\omega) d\omega  \\
       & \text{subject to:} 
       & &
       \begin{bmatrix}
       \psi_d^{\star}(\rho_d)\psi_{d,0} + \psi_{d,0}^{\star}\psi_d(\rho_d) - \psi_{d,0}^{\star}\psi_{d,0} & \phantom{xx} \left[W_{d_2}(Gk_w - \psi_d(\rho_d)\mathcal{S}_{v_dv_0}^d) \right]^{\star} \\
       W_{d_2}(Gk_w - \psi_d(\rho_d)\mathcal{S}_{v_dv_0}^d) & \phantom{xx} \Gamma (\omega)
       \end{bmatrix} \succ 0  \\
       & & &
       \begin{bmatrix}
       \psi_d^{\star}(\rho_d)\psi_{d,0} + \psi_{d,0}^{\star}\psi_d(\rho_d) - \psi_{d,0}^{\star}\psi_{d,0} & \phantom{xx} \Delta M_d^{\star} \\
       \Delta M_d & \phantom{xx} 1
       \end{bmatrix} \succ 0  \\
       & & & \rho_d \geq 0 \\
       & & & \forall \omega \in \Omega
       \end{aligned}

where :math:`\psi_{d,0} = \psi_d(\rho_{d,0})`. As with the
:math:`\mathcal{H}_\infty` method, PyFresco sets the initial stabilizing
controller :math:`\rho_{d,0}` to small positive constants in order to
guarantee the stability of the final controller. To better approximate the integral function,
a trapezoidal approximation of the objective function is used, i.e.,
:math:`\gamma \approx \sum_{k=1}^{\eta} \left(\frac{\Gamma_{k} + \Gamma_{k+1}}{2}\right)(\omega_{k+1} - \omega_{k})`.


Voltage Loop Design
-------------------

Once PyFresco has obtained the optimal parameters for the damping loop
:math:`\rho_d^*`, the voltage loop synthesis can then commence. The
(closed-loop) transfer function for the voltage loop can be expressed as
:math:`\mathcal{S}_{v_r v_0}(\rho_v) = \mathcal{S}_{v_dv_0}(\rho_d^*)[k_{ff} + C(\rho_v)]\psi_v^{-1}(\rho_v)`
where
:math:`\psi_v(\rho_v) = 1+\mathcal{S}_{v_dv_0}(\rho_d^*)C(\rho_v)e^{-s\tau_v}`.
The next step is to then perform the necessary optimization to obtain
the optimal voltage loop parameters :math:`\rho_v^*`.

.. _mathcalh_infty-control-2:

:math:`\mathcal{H}_\infty` Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method_v>`]

With the optimal parameters :math:`\rho_d*` obtained from the damping
loop optimization above, the objective is to now minimize
:math:`\|W_v(1 - \mathcal{S}_{v_rv_0}) \|_\infty` where
:math:`W_v = (1-\mathcal{S}_{v_rv_0}^d)^{-1}` (with
:math:`\mathcal{S}_{v_rv_0}^d` being the desired second-order response).
The desired :ref:`bandwidth <volt_bw>`, :ref:`damping <volt_z>`, and
:ref:`reference delay <ref_delay_v>` are taken into account with :math:`W_v`. 
As with the damping loop, the
voltage loop optimization problem can then be convexified as follows:

.. math::
   :label: opt_hinf_v

   \begin{aligned}
           & \underset{ \rho_v,\gamma}{\text{minimize}}
           & & \gamma  \\
           & \text{subject to:} & & \gamma^{-1} \left| \mathcal{M}(\rho_v) \right|^2   < 2\Re \left\{\psi_v(\rho_v) \psi_v^{\star}(\rho_{v,0}) \right\} - \left|\psi_v(\rho_{v,0}) \right|^2 \\
           & & &  \Delta M_v^2 < 2\Re \left\{\psi_v(\rho_v) \psi_v^{\star}(\rho_{v,0}) \right\} - \left|\psi_v(\rho_{v,0}) \right|^2 \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`\rho_{v,0}` is the initial stabilizing controller and

.. math::

   \mathcal{M}(\rho_v) = W_v[\psi_v(\rho_v)-\mathcal{S}_{v_dv_0}(\rho_d^*)(k_{ff} + C(\rho_v))].

The second constraint in this problem ensures that the voltage loop
possesses a minimum :ref:`modulus margin <volt_mm>` :math:`\Delta M_v`. Unlike the damping loop
optimization, selecting this initial controller is not as trivial as
setting small constant values for the controller parameters. Therefore,
the methods in `here <https://doi.org/10.1109/TCST.2017.2783346>`__ are
first used to design the initial stabilizing controller. In this method,
the PI controller is represented as :math:`C = XY^{-1}`, where :math:`X`
and :math:`Y` are proper, stable transfer functions. Thus for a PI
controller represented as :math:`C(s) = k_{p_1} + k_{p_2}/s`, these
transfer functions can be formulated as

.. math::

   \label{eq:coprimes}
       X(s) = \frac{k_{p_1}s + k_{p_2}}{s+a} \quad ; \quad Y(s)\frac{s}{s+a},

where :math:`a>0` is a free parameter [1]_. The optimal choice of
:math:`a` is an open research topic; however, the methods
`here <https://doi.org/10.1109/TCST.2017.2783346>`__ can be used to
solve the :math:`\mathcal{H}_\infty` problem for several values of
:math:`a`. The value of :math:`a` which yields the best optimal solution
(i.e., the lowest value of
:math:`\|W_v (1-\mathcal{S}_{v_r v_0}) \|_\infty`) is then selected as
the initial stabilizing controller to be used in :eq:`opt_hinf_v`. The values of
:math:`a` can be chosen around the closed-loop bandwidth of the voltage
loop; in the PyFresco algorithm,

.. math:: a \in \{\omega_{0}/3, \omega_{0}, 3\omega_{0}\},

where
:math:`\omega_{0}=2\pi\cdot`:ref:`volt_bw <volt_bw>`.
Note that in obtaining the initial stabilizing controller,
:math:`k_{ff}=0` is assumed; however, when generating the final
controller, :math:`k_{ff}` is optimized. Also note that the methods
`here <https://doi.org/10.1109/TCST.2017.2783346>`__ ensure very good
performance for large order controllers; however, since the voltage-loop
uses a simple PI controller, the performance may not be optimal. This is
why the `linearization
methods <https://doi.org/10.1109/CCTA.2017.8062665>`__ are then used to
optimize the performance for low-order controllers.

.. _mathcalh_2-control-2:

:math:`\mathcal{H}_2` Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method_v>`]

For the voltage loop, the :math:`\mathcal{H}_2` model-reference
objective (i.e., minimizing
:math:`\|W_{v_2}(\mathcal{S}_{v_rv_0} - \mathcal{S}_{v_rv_0}^d) \|_2^2`)
can be constructed as follows:

.. math::

   \begin{aligned}
           & \underset{ \rho_v, \gamma,\Gamma}{\text{minimize}} & & \gamma=\int_{-\pi / {T_v}}^{\pi / {T_v}} \Gamma(\omega) d\omega  \\
           & \text{subject to:} & & \left[W_{v_2}(\mathcal{S}_{v_rv_0} - \mathcal{S}_{v_rv_0}^d)\right]^{\star} \left[W_{v_2}(\mathcal{S}_{v_rv_0} - \mathcal{S}_{v_rv_0}^d) \right] < \Gamma(\omega) \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`W_{v_2} = 2 \pi \cdot` :ref:`volt_bw <volt_bw>`
:math:`\cdot s^{-1}`. As with the RST
synthesis (see :ref:`Current/Field Control`), this :math:`\mathcal{H}_2` optimization problem can
be convexified and efficiently solved as follows:

.. math::
   :label: opt_hinf_v2

   \begin{aligned}
       & \underset{ \rho_v, \gamma, \Gamma}{\text{minimize}} & &  \gamma=\int_{-\pi / {T_v}}^{\pi / {T_v}} \Gamma(\omega) d\omega  \\
       & \text{subject to:} 
       & &
       \begin{bmatrix}
       \psi_v^{\star}(\rho_v)\psi_{v,0} + \psi_{v,0}^{\star}\psi_v(\rho_v) - \psi_{v,0}^{\star}\psi_{v,0} & \phantom{xx} Z^{\star}(\rho_v) \\ 
       Z(\rho_v) & \phantom{xx} \Gamma (\omega)
       \end{bmatrix} \succ 0  \\
       & & &
       \begin{bmatrix}
       \psi_v^{\star}(\rho_v)\psi_{v,0} + \psi_{v,0}^{\star}\psi_v(\rho_v) - \psi_{v,0}^{\star}\psi_{v,0} & \phantom{xx} \Delta M_v^{\star} \\ 
       \Delta M_v & \phantom{xx} 1
       \end{bmatrix} \succ 0 \\
       & & & \forall \omega \in \Omega
       \end{aligned}

where :math:`\psi_{v,0} = \psi_v(\rho_{v,0})` and

.. math:: Z(\rho_v)=W_{v_2}(\mathcal{S}_{v_dv_0}(\rho_d^*)(k_{ff}+C(\rho_v)) - \psi_v(\rho_v)\mathcal{S}_{v_rv_0}^2).

To set the initial stabilizing controller :math:`\rho_{v,0}`, the same
iterative procedure discussed in the previous section is used. Once a feasible solution
is found (for some given :math:`a`), that solution is used as
:math:`\psi_{v,0}`, and the problem in :eq:`opt_hinf_v2` can then be efficiently
solved my PyFresco.

.. _performance-evaluation-1:

Performance Evaluation (Voltage Control)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once PyFresco completes the design for both the damping and voltage loops
(for either :math:`\mathcal{H}_\infty` or :math:`\mathcal{H}_2`
performance), the question now remains, how can the performance of the
controller be evaluated? The optimal solution for each optimization
method can be used for this purpose; these optimal solutions are
computed as follows:

-  :math:`\mathcal{H}_\infty` control:

   .. math::

      \begin{aligned}
              \gamma_\infty^*  &=  \sup_{\omega \in \Omega} |X_\infty (e^{-j\omega T_s})|
          \end{aligned}

-  :math:`\mathcal{H}_2` control:

   .. math::

      \begin{aligned}
              \gamma_2^*  &= \sqrt{\frac{T_s}{2\pi} \int_{- \pi/T_s}^{\pi/T_s} \left|X_2(e^{-j\omega T_s}) \right|^2 \: d\omega}
          \end{aligned}

where

   .. math::

      \begin{aligned}
        \text{Damping Loop: }&X_\infty = W_d(1 - \mathcal{S}_{v_dv_0}(\rho_d^*)) \\
                             &X_2 = W_{d_2}(\mathcal{S}_{v_dv_0}(\rho_d^*) - \mathcal{S}_{v_dv_0}^d) \\
        \text{Voltage Loop: }&X_\infty = W_v(1 - \mathcal{S}_{v_rv_0}(\rho_v^*)) \\
                             &X_2 = W_{v_2}(\mathcal{S}_{v_rv_0}(\rho_v^*) - \mathcal{S}_{v_rv_0}^d).
        \end{aligned}

PyFresco displays these optimal solutions at the end of each optimization
session. Note that the displayed optimal solution is an approximation to
the true solution (since the frequency vector :math:`\omega` is discrete
and finite). See :ref:`rst_perf_eval` for evaluating the controller
performance for each optimization method and for general details on using
each of the optimization methods.




[lastpage]


.. [1]
   Note that for the initial stabilizing controller, optimizing in the
   continuous-time domain is sufficient to guarantee the stability using
   the discrete-time controller
