Current/Field Control
=====================


The FGC can implement two types of control methods for the current and
field loops. One is the standard RST controller which is used for
general (non-repetitive) cycles. Some of the theory behind the RST
synthesis for power converters has already been addressed. It is thus
recommended that the user consults `this
document <https://edms.cern.ch/document/2001105/1>`__ before continuing
to read any further (as the theory presented here will be a brief
extension of that content).

The second type of control method used is Iterative Learning Control
(ILC). This method can only be run when the FGC is in cycling mode. This
is because ILC requires repetitive cycles to “learn” the required
reference signal in order to produce zero error between the output and
the desired output. More information on the ILC methodology can be found
`here <http://dx.doi.org/10.1049/iet-cta.2018.6446>`__; information on
the architecture of ILC within the FGC can be found
`here <https://wikis.cern.ch/pages/viewpage.action?pageId=148734841>`__.
Note that to run ILC, a stabilizing RST controller needs to be set in
the device.

PyFresco synthesizes both the RST and ILC filters for a particular loop.
Both of these control methods are discussed in detail below.

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
:math:`\zeta \:` is the *desired* :ref:`damping factor <des_z>`, :math:`d_r` is the
*desired* :ref:`reference delay <ref_delay>` and

.. math:: \omega_d = 2 \pi f_d \left[ 1-2\zeta^2 + \sqrt{2-4\zeta^2 + 4\zeta^4} \right]^{-0.5},

where :math:`f_{d}` [Hz] is the *desired* closed-loop :ref:`bandwidth <des_bw>` of the
system. Note that :math:`r` or :math:`y` can be either the current or field (depending
on the loop the user wants to regulate).

RST Synthesis
-------------

.. _rst:
.. figure:: pics/rst_block.png
   :alt: RST controller structure

   RST controller structure for the current and field loop. The voltage
   disturbance :math:`d_{v}` is depicted here at the input of the
   voltage source; this is done on purpose for uniformity in the case of
   data driven design where only the series :math:`V(s)M(s)` can be
   measured. This assumption has no relevant consequences though as
   :math:`V(s)` is assumed to have unity gain and :math:`M(s)` is
   assumed to be always slower than :math:`V(s)`.

:numref:`rst` shows the general power converter control system
configuration. In a model-driven setting, the `voltage source and
magnet <https://edms.cern.ch/document/2001105/1>`__ dynamics
:math:`V(s)` and :math:`M(s)` (along with the other components) are
approximated by using the FGC property values. In a data-driven setting,
the open-loop dynamics can be measured using the FRM tool (see XXX for
more information). Let us denote :math:`G(s)` as the system
corresponding to the open-loop dynamics (DAC/SPI, voltage source,
magnet, and feedback elements), and :math:`G_{f}(s)` as the system
corresponding to the dynamics in the forward path (DAC/SPI, voltage
source and magnet). Note that :math:`G(s)` includes the `moving average
filter <https://edms.cern.ch/document/2001105/1>`__ dynamics given by
the FGC property
`MEAS.I/B.FIR_LENGTHS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyMEAS.htm#MEAS.I.FIR_LENGTHS>`__.

The `RST controller <https://doi.org/10.1109/TCST.2017.2783346>`__ is a
2-degree-of-freedom controller which can be used to synthesize the
tracking and regulation requirements independently from each other. Each
controller is realized as a polynomial function as follows:

.. math::

   \begin{aligned}
   R(z^{-1},\rho) &= r_0 + r_1z^{-1} + \cdots + r_{n_r}z^{-n_r} \\
   S(z^{-1},\rho) &= 1 + s_1z^{-1} + \cdots + s_{n_s}z^{-n_s} \\
   T(z^{-1},\rho) &= t_0 + t_1z^{-1} + \cdots + t_{n_t}z^{-n_t},
   \end{aligned}

where :math:`\{n_r,n_s,n_t\}` [:ref:`n_r <n_r>`, :ref:`n_s <n_s>`, :ref:`n_t <n_t>`] are
the orders of the polynomials :math:`R,S` and :math:`T`, respectively.
For notation purposes, the :math:`z^{-1}` term will only be reiterated
when deemed necessary. The controller parameter vector
:math:`\rho \in \mathbb{R}^{n_{rst}}` (vector of decision variables) is
defined as

.. math:: \rho^\top=[r_0,r_1,\ldots,r_{n_r},s_1,s_2,\ldots,s_{n_s},t_0,t_1,\ldots,t_{n_t}].

With PyFresco, :math:`\rho` can be obtained by minimizing either the
:math:`\mathcal{H}_\infty`, :math:`\mathcal{H}_2` and
:math:`\mathcal{H}_1` criterion. The methodology behind these criteria
is outlined below.

Initial stabilizing controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To successfully design a stabilizing low-order RST controller, the
`design
methodology <https://doi.org/10.1016/j.conengprac.2018.10.007>`__
requires an initial stabilizing controller :math:`R(\rho_0)` and
:math:`S(\rho_0)` (where the index :math:`i` denotes initial). In
general, the performance of this initial controller need not be close to
the performance of the final controller; however, experimentation shows
that a better initial controller will reduce the overall optimization
time of the algorithm. For the CERN power converter control system,
there are several constraints that are imposed to improve the controller
performance and system robustness; the following
:math:`\mathcal{H}_\infty` minimization problem can be considered to
produce the initial controller:

.. math::

   \begin{aligned}
       & \underset{ \rho_0}{\text{minimize}}
       & & \|W[1-\mathcal{S}_{ry}(\rho_0)] \|_\infty  \\
       & \text{subject to:} & & \| \Delta M_{ib} \mathcal{S}_{d_y y}(\rho_0) \|_\infty < 1  \\ 
       & & & \|A_k^{-1} \mathcal{S}_{d_v y}^{k}(\rho_0) \|_\infty < 1 \\
       & & & \Re\{S(\rho_0) \} > 0 \\
       & & & \forall \omega \in \Omega, \ k = \{1,2,\ldots, a\}
       \end{aligned}

where :math:`W = (1-\mathcal{S}_{ry}^d)^{-1}` and
:math:`\Omega := [0,\pi/T_s]`. The first constraint
ensures that the desired :ref:`modulus margin <des_mm>` is obtained (where
:math:`\Delta M_{ib}` is the modulus margin). The second constraint ensures 
that the desired :ref:`noise attenuation <noise_rej>` 
of :math:`A_k` [-] on :math:`|\mathcal{S}_{d_v y}^k|` is obtained; the subscript :math:`k`
denotes the k-th index of a frequency vector. The third 
constraint ensures the stability of the open-loop
controller. Note that :math:`S(\rho_0)` contains :math:`n_I`
[:ref:`n_integrators <n_integrators>`] integrators that can
be set by the user. As it stands, this problem is non-convex and the
solution does not guarantee the stability of the initial controller.
However, `this problem can be
convexified <https://doi.org/10.1109/TCST.2017.2783346>`__ as follows:

.. math::
   :label: opt_init

   \begin{aligned}
       & \underset{ \gamma, \rho_0}{\text{minimize}}
       & & \gamma  \\
       & \text{subject to:} & & \gamma^{-1} \left| W [\psi(\rho_0) - G_f T(\rho_0)] \right|< \Re\{\psi(\rho_0) \}  \\ 
       & & & \left| \Delta M_{ib} S(\rho_0) \right| < \Re\{\psi(\rho_0) \}  \\ 
       & & & \left| A_k^{-1} G_f^k S^k(\rho_0) \right| < \Re\{\psi^k(\rho_0) \}  \\        
       & & & \Re\{S(\rho_0) \} > 0 \\
       & & & \forall \omega \in \Omega, \ k = \{1,2,\ldots, a\}
       \end{aligned}

where :math:`\psi(\rho_0) = GR(\rho_0) + S(\rho_0)`. The classical
solution to this problem is to implement a bisection algorithm in order
to obtain the global solution.

-  For a model-driven design, the optimization problem is solved in a
   semi-definite programming (SDP) approach where a frequency array of
   finite values is defined *a-priori*. PyFresco contains an algorithm that
   automatically calculates this array.

-  For a data-driven design, the same SDP approach is taken. However,
   the frequency array does not need to be arbitrarily constructed (as
   in the model-driven design) since the frequency values from the FRM
   experiments are already available with the corresponding gain and
   phase values.

A feasible solution to :eq:`opt_init` ensures the stability of the closed-loop
system, and thus produces stabilizing (initial) controllers. With PyFresco,
the initial order for all RST polynomials are selected as
:math:`n_r=n_s=n_t=5`. If the problem is infeasible for this order, then
the PyFresco algorithm will increase the order until feasibility is
achieved.

Note that if :math:`d_r` is set too large (greater than the open-loop
delay), the :math:`T(z^{-1})` polynomial may contain unstable zeros
(which is not desired since the FGC control loop implements
back-calculations needed for anti wind-up control). If this instability
in :math:`T(z^{-1})` occurs, PyFresco will re-optimize and add the
constraint :math:`\Re\{T(\rho_0)\} > 0` to the optimization problem (and
to the :math:`\mathcal{H}_\infty, \mathcal{H}_2` and
:math:`\mathcal{H}_1` optimization problems discussed below); this
constraint is a sufficient condition to ensure that the zeros of
:math:`T(z^{-1})` remain inside the unit circle. Note that this
additional constraint may impact the final performance of the
controller. It is thus recommended to modify :math:`d_r` only if the
open-loop delay of the system is (approximately) known.

In summary, here is the basic PyFresco RST synthesis methodology:

-  Implement the `stabilizing
   method <https://doi.org/10.1109/TCST.2017.2783346>`__ to design a
   large order controller (where no initialization is needed and the
   controllers are stabilizing). The optimization constraints will
   automatically be modified based on the solutions obtained.

-  Use the controller in the previous step as the initialization for the
   `low-order optimization
   problem <https://doi.org/10.1016/j.conengprac.2018.10.007>`__ (which
   ensures the closed-loop stability and performance for low-order
   controllers).

The second step to this problem is now addressed below. It is now
assumed that the initial stabilizing polynomials :math:`R(\rho_0)` and
:math:`S(\rho_0)` are available.

.. _rst_hinf_control:

:math:`\mathcal{H}_\infty` control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method>`]

In the :math:`\mathcal{H}_\infty` sense, the objective is to minimize
:math:`\|W(1 - \mathcal{S}_{ry}(\rho)) \|_\infty`; an equivalent
representation of this objective is to minimize :math:`\gamma` such that
:math:`\|W(1 - \mathcal{S}_{ry})  \|_\infty^2 < \gamma` (which is the
epigraph form of the minimization criterion). This criterion is
satisfied if the following optimization problem is considered:

.. math::

   \begin{aligned}
           & \underset{ \rho,\gamma}{\text{minimize}}
           & & \gamma  \\
           & \text{subject to:} & & \left[W(1-\mathcal{S}_{ry}(\rho)) \right]^{\star} \left[W(1-\mathcal{S}_{ry}(\rho)) \right] < \gamma \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`(\cdot)^\star` denotes the complex conjugate of the
argument. The constraint in the above optimization problem can be
expressed as

.. math:: \left[W(\psi(\rho)-G_{f} T(\rho)) \right]^{\star} \gamma^{-1} \left[W(\psi(\rho)-G_{f} T(\rho)) \right] - \psi^{\star}(\rho)\psi(\rho)<0.

where :math:`\psi(\rho) = GR(\rho) + S(\rho)`. This constraint is
convex-concave (due to the :math:`- \psi^{\star}(\rho)\psi(\rho)` term).
To convexify this constraint, the term
:math:`\psi^{\star}(\rho)\psi(\rho)` can be linearized around an initial
controller parameter vector :math:`\rho_0`. With the Shur Complement
Lemma, the optimization problem can be transformed to a `linear matrix
inequality <https://doi.org/10.1016/j.conengprac.2018.10.007>`__ (LMI).
However, large LMI’s are not solved efficiently with Python. Thus the
optimization constraint is left in its linear form; the final
optimization problem to solve (with the additional modulus margin and
controller stability constraint) can be expressed as follows:

.. math::
   :label: opt_hinf

   \begin{aligned}
           & \underset{ \rho,\gamma}{\text{minimize}}
           & & \gamma  \\
           & \text{subject to:} & & \gamma^{-1} \left|W(\psi(\rho)-G_fT(\rho)) \right|^2   < 2\Re \left\{\psi(\rho) \psi^{\star}(\rho_0) \right\} - \left|\psi(\rho_0) \right|^2 \\
           & & & 
           \left| \Delta M_{ib} S(\rho) \right|^2   < 2\Re \left\{\psi(\rho) \psi^{\star}(\rho_0) \right\} - \left|\psi(\rho_0) \right|^2 \\
           & & & 
           \left| A_k^{-1} G_f^k S^k(\rho) \right|^2   < 2\Re \left\{\psi^k(\rho) \psi^{\star,k}(\rho_0) \right\} - \left|\psi^k(\rho_0) \right|^2 \\
           & & & \Re\{S(\rho) \} > 0 \\
           & & &\forall \omega \in \Omega, \ k = \{1,2,\ldots, a\}
       \end{aligned}

where :math:`\psi(\rho_0) = GR(\rho_0) + S(\rho_0)`. *For a stabilizing
RST controller*, :math:`R(\rho_0)` *and* :math:`S(\rho_0)` *must be
stabilizing*. For a fixed :math:`\gamma`, this optimization problem is
convex. Thus the optimal solution can be obtained by performing a
bisection algorithm [1]_ over :math:`\gamma`. This optimal solution,
however, is the solution for one iteration of a given
:math:`\psi(\rho_0)`. The converged true local solution can be obtained
by solving the above optimization problem and replace
:math:`\psi(\rho_0)` with the solution of the previous problem. The
final solution is then obtained within a given tolerance level of
:math:`\gamma`.

Here is a basic summary of the optimization process for
:math:`\mathcal{H}_\infty` performance:

-  Obtain an initial stabilizing controller :math:`R(\rho_0)` and
   :math:`S(\rho_0)` from the convex optimization problem in :eq:`opt_init`.

-  Use this solution as the initializing controller in
   :math:`\psi(\rho_0)` (i.e.,
   :math:`\psi(\rho_0) = GR(\rho_0) + S(\rho_0)`).

-  Solve the optimization problem in :eq:`opt_hinf` using a bisection algorithm.
   Use the solution as the new :math:`\psi(\rho_0)`.

-  Repeat the above step until convergence is achieved with respect to
   :math:`\gamma`.

:math:`\mathcal{H}_2` control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method>`]

A similar linearization process can be used to obtain
:math:`\mathcal{H}_2` performance. An optimization problem can be
formulated for minimizing the square of the :math:`\mathcal{H}_2`
model-reference objective (i.e., minimizing
:math:`\|W_2(\mathcal{S}_{ry}(\rho) - \mathcal{S}_{ry}^d) \|_2^2`); the
optimization problem for this criteria can be expressed as follows:

.. math::

   \begin{aligned}
           & \underset{ \rho, \gamma,\Gamma}{\text{minimize}} & & \gamma=\int_{-\pi / {T_s}}^{\pi / {T_s}} \Gamma(\omega) d\omega  \\
           & \text{subject to:} & & \left[W_2(\mathcal{S}_{ry}(\rho) - \mathcal{S}_{ry}^d)\right]^{\star} \left[W_2(\mathcal{S}_{ry}(\rho) - \mathcal{S}_{ry}^d) \right] < \Gamma(\omega) \\
           & & &\forall \omega \in \Omega
       \end{aligned}

where :math:`\Gamma(\omega) \in \mathbb{R}_+` is an unknown function of
:math:`\omega` and :math:`W_2 = 2 \pi \cdot` :ref:`des_bw <des_bw>`
:math:`\cdot s^{-1}`. By using the Shur
complement lemma, the above problem can be transformed into an LMI. Note
that in contrast to the :math:`\mathcal{H}_\infty` problem above, we
cannot leave this problem in linear form and solve it with a bisection
algorithm because :math:`\gamma` here is a variable function, not simply
a constant. Thus we are forced to use the LMI method to solve the
problem. With the added modulus margin and controller stability
constraint, the :math:`\mathcal{H}_2` optimization problem to solve is
given as follows:

.. math::
   :label: opt_h2

   \begin{aligned}
       & \underset{ \rho, \gamma, \Gamma}{\text{minimize}} & &  \gamma=\int_{-\pi / {T_s}}^{\pi / {T_s}} \Gamma(\omega) d\omega  \\
       & \text{subject to:} 
       & &
       \begin{bmatrix}
       \psi^{\star}(\rho)\psi_0 + \psi_0^{\star}\psi(\rho) - \psi_0^{\star}\psi_0 & \phantom{xx} \left[W_2(G_fT(\rho) - \psi(\rho)\mathcal{S}_{ry}^d) \right]^{\star} \\
       W_2(G_fT(\rho) - \psi(\rho)\mathcal{S}_{ry}^d) & \phantom{xx} \Gamma (\omega)
       \end{bmatrix} \succ 0  \\
       & & &
       \begin{bmatrix}
       \psi^{\star}(\rho)\psi_0 + \psi_0^{\star}\psi(\rho) - \psi_0^{\star}\psi_0 & \phantom{xx} \left[\Delta M_{ib}S(\rho) \right]^{\star} \\ 
       \Delta M_{ib}S(\rho) & \phantom{xx} 1
       \end{bmatrix} \succ 0  \\
       & & & 
       \left| A_k^{-1} G_f^k S^k(\rho) \right|^2   < 2\Re \left\{\psi^k(\rho) \psi^{\star,k}(\rho_0) \right\} - \left|\psi^k(\rho_0) \right|^2 \\
       & & & \Re\{S(\rho)\} > 0 \\
       & & & \forall \omega \in \Omega, \ k = \{1,2,\ldots,a \}
       \end{aligned}

where :math:`\psi_0 = \psi(\rho_0)`. With PyFresco, the constraints are
evaluated at a finite number of frequencies (i.e.,
:math:`\omega \in \Omega_\eta=\{ \omega_1,\ldots,\omega_\eta \}`), thus
:math:`\Gamma(\omega)` can be replaced by an optimization variable
:math:`\Gamma_k` at each frequency :math:`\omega_k` for
:math:`k=1,\ldots,\eta`. To better approximate the integral function,
a trapezoidal approximation of the objective function is used, i.e.,
:math:`\gamma \approx \sum_{k=1}^{\eta} \left(\frac{\Gamma_{k} + \Gamma_{k+1}}{2}\right)(\omega_{k+1} - \omega_{k})`.

Here is a basic summary of the optimization process for
:math:`\mathcal{H}_2` performance:

-  Obtain an initial stabilizing controller :math:`R(\rho_0)` and
   :math:`S(\rho_0)` from the convex optimization problem in :eq:`opt_init`.

-  Use this solution as the initializing controller in
   :math:`\psi(\rho_0)` (i.e.,
   :math:`\psi(\rho_0) = GR(\rho_0) + S(\rho_0)`).

-  Solve the optimization problem in :eq:`opt_h2`. Use the solution as the new
   :math:`\psi(\rho_0)`.

-  Repeat the above step until convergence (within a fixed tolerance) is
   achieved with respect to :math:`\gamma`.

:math:`\mathcal{H}_1` control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[:ref:`opt_method <opt_method>`]

In some applications, minimizing the :math:`\mathcal{H}_1` norm of the
model-reference objective may be desired. This is because for a given
bounded discrete-time signal :math:`x[k]`, and its frequency response
:math:`X(e^{j\omega T_s})`, the relationship between :math:`\| X \|_1`
and :math:`\| x \|_\infty` is given as
:math:`\|x \|_\infty \leq \| X\|_1`. Therefore, if one is interested in
minimizing the peak error between the output and desired output (i.e.,
minimize :math:`\| y[k] - y_d[k]\|_\infty`) in the time-domain, then
minimizing
:math:`\|W_2(\mathcal{S}_{ry}(\rho) - \mathcal{S}_{ry}^d) \|_1` can be
considered.

Unlike the :math:`\mathcal{H}_\infty` and :math:`\mathcal{H}_2`
algorithms, the :math:`\mathcal{H}_1` minimization problem is handled in
two steps. This is because the :math:`\mathcal{H}_1` problem cannot
easily be linearized to obtain convex constraints. In the first step, a
simple feasibility problem is solved to stabilize the closed-loop
system, stabilize the open-loop controller, and obtain a desired modulus
margin:

.. math::

   \begin{aligned}
   & \text{find}
   & & \rho  \\
   & \text{subject to:} & & \left| \Delta M_{ib} S(\rho) \right|<\Re \left\{ \psi(\rho) \right\} \\
   & & & \left| A_k^{-1} G_f^k S^k(\rho) \right| < \Re\{\psi^k(\rho) \}  \\ 
   & & & \Re\{S(\rho) \} > 0 \\
   & & & \forall \omega \in \Omega, \ k = \{1,2,\ldots,a \}
   \end{aligned}

Note that a feasible solution to this problem generates
:math:`R(\rho^*)` and :math:`S(\rho^*)` (i.e., there is no :math:`T`
polynomial to optimize in the above problem). The remaining polynomial
to compute is :math:`T(\rho)` in order to obtain the desired tracking
preformance; this polynomial is computed by solving the following
optimization problem:

.. math::

   \begin{aligned}
           & \underset{ \rho}{\text{minimize}} & & \|W_2(\mathcal{S}_{ry}(\rho) - \mathcal{S}_{ry}^d) \|_1 \\
       \end{aligned}

where :math:`G_fT(\rho)[GR(\rho^*) + S(\rho^*) ]^{-1}`. Note that the
:math:`\mathcal{H}_1` optimization method does not require an initial
stabilizing controller to achieve the desired performance. However,
because the :math:`R` and :math:`S` polynomials are computed separately
from :math:`T`, a larger :math:`n_t` is typically needed to achieve
satisfactory performance.

.. _rst_perf_eval:

Performance Evaluation
~~~~~~~~~~~~~~~~~~~~~~

Once PyFresco completes the RST optimization (for either
:math:`\mathcal{H}_\infty`, :math:`\mathcal{H}_2` or
:math:`\mathcal{H}_1` control), the question now remains, how can the
performance of the controller be evaluated? The optimal solution for
each optimization method can be used for this purpose; these optimal
solutions are computed as follows:

-  :math:`\mathcal{H}_\infty` control:

   .. math::

      \begin{aligned}
              \gamma_\infty^*  &=  \sup_{\omega \in \Omega} |X_\infty(e^{-j\omega T_s})| \\
              X_\infty &= W(1 - \mathcal{S}_{ry}(\rho^*))
          \end{aligned}

-  :math:`\mathcal{H}_2` control:

   .. math::

      \begin{aligned}
              \gamma_2^*  &= \sqrt{\frac{T_s}{2\pi} \int_{- \pi/T_s}^{\pi/T_s} \left|X_2(e^{-j\omega T_s}) \right|^2 \: d\omega} \\
            X_2 &= W_2(\mathcal{S}_{ry}(\rho^*) - \mathcal{S}_{ry}^d)
          \end{aligned}

-  :math:`\mathcal{H}_1` control:

   .. math::

      \begin{aligned}
              \gamma_1^*  &= \frac{T_s}{2\pi} \int_{- \pi/T_s}^{\pi/T_s} |X_1(e^{-j\omega T_s})| \: d\omega \\
              X_1 &= W_2(\mathcal{S}_{ry}(\rho^*) - \mathcal{S}_{ry}^d)
          \end{aligned}

PyFresco displays these optimal solutions at the end of each optimization
session. Note that the displayed optimal solution is an approximation to
the true solution (since the frequency vector :math:`\omega` is discrete
and finite). :numref:`performance_index` shows a table which
depicts a basic “rule of thumb” for evaluating the RST controller
performance for each optimization method.


.. _performance_index:
.. table:: Performance index “rule of thumb” for different settings in :ref:`opt_method <opt_method>`.
   :align: center

   +--------------+----------------------------+--------------------------------------+
   |              |:math:`\mathcal{H}_\infty`  |:math:`\mathcal{H}_1 / \mathcal{H}_2` |
   +==============+============================+======================================+
   |Good          | :math:`[0,1.3)`            | :math:`[0,0.15)`                     |
   +--------------+----------------------------+--------------------------------------+
   |Satisfactory  | :math:`[1.3,1.8)`          | :math:`-`                            |
   +--------------+----------------------------+--------------------------------------+
   |Bad           | :math:`[1.8,\infty)`       | :math:`[0.15,\infty)`                |
   +--------------+----------------------------+--------------------------------------+



Below is a general interpretation of each control method and when to
implement them:

-  Use :math:`\mathcal{H}_\infty` control for general
   control demands. The :math:`\mathcal{H}_\infty` control method is the
   most common and general optimization criterion. A simple
   interpretation of minimizing the :math:`\mathcal{H}_\infty` criterion
   is to minimize :math:`\gamma` such that
   :math:`|E|\gamma^{-1} < |E_d|` for all :math:`\omega \in \Omega`
   (where :math:`E` and :math:`E_d` are the error and desired error
   transfer functions, respectively). From this condition, it can be
   observed that minimizing the :math:`\mathcal{H}_\infty` criterion is
   equivalent to shaping :math:`|E|` as close as possible to
   :math:`|E_d|` over all frequencies. The solution to this problem
   generally yields satisfactory performance.

-  Use :math:`\mathcal{H}_2` control when it is desired to minimize the
   average (time-domain) error. This is due to the fact that
   :math:`\|x[k] \|_2 \propto \|X(e^{-j\omega T_s}) \|_2` (i.e., from
   Parsavel’s theorem); this implies that minimizing the
   :math:`\mathcal{H}_2` criterion of the model reference objective in
   :eq:`opt_h2` is equivalent to minimizing :math:`\| (r[k] - y[k]) (r[k] - y_d[k])^{-1}\|_2`,
   (i.e., the weighted average error), where :math:`r[k], y[k], y_d[k]` are the time-domain
   reference, output, and desired output signals, respectively.

-  Use :math:`\mathcal{H}_1` control when it is desired to minimize the
   peak (time-domain) error. This is due to the fact that
   :math:`\|x[k] \|_\infty \leq \|X(e^{-j\omega T_s}) \|_1` (as
   explained in the previous section).

ILC Synthesis
-------------

.. _ilc:
.. figure:: pics/ilc_block.png
   :alt: ILC structure

   A basic block diagram of the ILC structure used for power converters.

The ILC structure used for the CERN power converters is shown in :numref:`ilc`.
ILC seeks to address the tracking problem by implementing a learning
algorithm where the desired performance is achieved by incorporating
past error information into the control structure. The control signal
(or reference signal in the case of closed-loop control) is modified to
attain a desired specification; with ILC, systems that perform the same
operations (i.e., repetitive tracking specifications) under the same
operating conditions are considered. Given a real-valued signal
:math:`x(k)` with a time index :math:`k`, the symbol :math:`q` will
denote the forward time-shift operator such that
:math:`qx(k) \equiv x(k+1)`. The output of the closed-loop control
system can be expressed as follows:

.. math:: y_l(k) = \mathcal{S}_{ry}(q)r_l(k)

where :math:`l` is the ILC iteration sequence, :math:`y_l(k)` is the
output, :math:`y_d(k)` is the desired output, and :math:`r_l(k)` is the
reference signal that is modified by the ILC algorithm in order to
acquire the desired output response. The transfer operator
:math:`\mathcal{S}_1(q)` is assumed to be stable (i.e., a stabilizing
RST controller is set).

Let us denote the error of the ILC closed-loop system as
:math:`e_l(k) \triangleq y_d(k)-y_l(k)`; the first-order ILC algorithm
can then be expressed as

.. math:: 
   :label: ilc_update

   r_{l+1}(k) = Q(q)[r_l(k) + L(q)e_l(k)],

where :math:`Q(q)` and :math:`L(q)` are known as the Q-filter and
learning filter, respectively. The question now remains, how can the
Q-filter and learning function be designed to produce the best tracking
performance? It can be shown that if

.. math:: \|Q(z)[1-L(z)\mathcal{S}_1(z)] \|_\infty < 1,

then the update equation in :eq:`ilc_update` will produce an output :math:`y_l(k)`
that is asymptotically stable.

The Q-filter can generally be set as a simply low-pass filter with a
particular bandwidth (and unity gain). The bandwidth represents the
frequency at which the ILC algorithm is no longer active. Thus
frequencies above the Q-filter bandwidth are not tracked. However,
setting a bandwidth too large will reduce the system robustness to
uncertainties from :math:`\mathcal{S}_{ry}`. Thus there is a trade-off
between robustness and tracking performance.

The FGC cannot implement an IIR low-pass for the Q-filter. Thus an FIR
is used to approximate the IIR response. PyFresco parameterizes the filters
as follows:

.. math::

   \begin{aligned}
       L(\alpha) &= \sum_{k=-n_l}^{n_l} \alpha_k z^k \\
       Q(\beta) &= \sum_{k=-n_q}^{n_q} \beta_k z^k, \quad \beta_i = \beta_{-i} \ \forall i
       \end{aligned}

where :math:`n_l` [:ref:`n_ilc <n_ilc>`] and :math:`n_q`
[:ref:`n_q <n_q>`] represent the orders of the filters. Note
that the Q-filter is symmetric (to produce zero-phase filtering). Given
this parameterization, the following optimization can be constructed:

.. math::
   :label: ilc_nonconvex

   \begin{aligned}
       & \underset{ \alpha, \beta, \gamma}{\text{minimize}}
       & & \gamma  \\
       & \text{subject to:} & & \left| Q(\beta)(1 - L(\alpha)S_{ry}) \right| < \gamma \\
       & & & \gamma < 1 \\
       & & & \forall \omega \in \Omega
       \end{aligned}

Any feasible solution will guarantee the asymptotically stability of the
ILC algorithm. However, the above optimization is non-convex (which
causes computational problems).

Q-Filter Optimization
~~~~~~~~~~~~~~~~~~~~~

PyFresco convexifies the problem in :eq:`ilc_nonconvex` by optimizing the Q-filter
separately from the learning function. The Q-filter can be obtained by
solving the following simple problem:

.. math::

   \begin{aligned}
           & \underset{\beta}{\text{minimize}} & & \||Q_d| - Q(\beta)  \|_1 \\
           & \text{subject to:} & & \sum \beta_k = 1
       \end{aligned}

where

.. math::

   Q_d = \frac{\omega_q^2}{s^2 + 2\omega_q s + \omega_q^2}, \quad
   \omega_q = 2 \pi f_{q} \left[ \sqrt{2}-1 \right]^{-0.5}

and :math:`f_{q}` [:ref:`q_bw <q_bw>`] is the *desired*
bandwidth of the Q-filter. The constraint in the problem ensures unity
gain. Experimentation shows that minimizing the :math:`\mathcal{H}_1`
criterion produces the most consistent results.

Learning Function Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With a feasible solution :math:`\beta^*` obtained from the Q-filter
optimization, the optimization problem in :eq:`ilc_nonconvex` can then efficiently be
solved:

.. math::

   \begin{aligned}
       & \underset{ \alpha, \gamma}{\text{minimize}}
       & & \gamma  \\
       & \text{subject to:} & & \left| Q(\beta^*)(1 - L(\alpha)S_{ry}) \right| < \gamma \\
       & & & \gamma < 1 \\
       & & & \forall \omega \in \Omega
       \end{aligned}

This problem is now convex and can efficiently be solved with CVXPY.
PyFresco calculates the optimal solution by increasing the filter order
:math:`n_l` (if needed) until feasibility is achieved.

-  If the ILC filter is designed based on a model-driven optimization,
   then the implementation of a filter :math:`Q \neq 1` is recommended
   (in order to achieve some robustness to model uncertainties). The
   lower the bandwidth of the Q-filter, the better the robustness (at
   the cost of tracking performance).

-  If the ILC filter is designed based on a data-driven optimization
   (with a frequency response that is not too noisy), then the
   implementation of a filter :math:`Q = 1` (or a filter with a large
   :math:`f_q`) may be implemented to achieve the best possible tracking
   performance. A higher order :math:`n_l` is recommended to increase
   the robustness. If the frequency response is noisy, a Q-filter with a
   lower bandwidth is recommended.

   [lastpage]

.. [1]
   The optimization problem, as stated, is not Disciplined Parametrized
   Programming (`DPP <https://www.cvxpy.org/tutorial/advanced/#disciplined-parametrized-programming>`__)
   compliant using the Python package CVXPY. To make it compliant, PyFresco
   implements a new variable :math:`\gamma_v = \gamma^{-1}` and performs
   the bisection to maximize :math:`\gamma_v` over all frequencies.