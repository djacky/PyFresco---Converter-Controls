UI Parameters (ObCD)
====================
This section contains all of the parameters and keys that PyFresco uses to synthesize controllers
for the ObCD package. These parameters are UI inputs that should be stored as class attributes.
The regulation rate is used to determine some of the UI parameter limits; the regulation rate is defined as:

.. math::
   :label: Fs

   F_s =(\text{FGC.ITER_PERIOD} \times \text{REG.I/B.PERIOD_ITERS[x]})^{-1}

See `FGC.ITER_PERIOD <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyFGC.htm#FGC.ITER_PERIOD>`__ ,
`REG.I.PERIOD_ITERS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.I.PERIOD_ITERS>`__ and
`REG.B.PERIOD_ITERS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.B.PERIOD_ITERS>`__ 
for more information on these properties.

ObCD Keys
----------

.. _control_mode:

**Control Mode:** 

    :keyword: 
        :code:`control_mode`

        Desired control loop to regulate.

        ``V``: Design controller for damping and voltage loop.

        ``I``: Design RST and ILC controllers for current loop.

        ``B``: Design RST and ILC controllers for field loop.

    :Type: 
        ``str``
        
    :Default: 
        Not applicable.
        
    :Recommended: 
        Not applicable.
        
    :Feasible values: 
        [``I``, ``B``, ``V``]

Current/Field Keys
~~~~~~~~~~~~~~~~~~

.. _test_select:

**Test Select:** 

    :keyword: 
        :code:`test_select`

        Property value to set if the user wants to enable RST test parameters. 
        ``False`` disables the test parameters; ``True`` enables the test parameters.

    :Type: 
        ``bool``
        
    :Default: 
        ``False``
        
    :Recommended: 
        Not applicable.
        
    :Feasible values: 
        [``True``, ``False``]

----

**Debug:**

    :keyword:
        :code:`debug`

        Property value to set if the user wants to show the ObCD parameters on the console.
        ``False`` disables the parameter output; ``True`` enables the parameter output.

    :Type:
        ``bool``

    :Default:
        ``False``

    :Recommended:
        Not applicable.

    :Feasible values:
        [``True``, ``False``]

----

.. _des_bw:

**Bandwidth:** 

    :keyword: 
        :code:`des_bw`

        Desired closed-loop bandwidth :math:`f_{ib}` [Hz].

    :Type: 
        ``float``
        
    :Default: 
        :math:`F_s/15`
        
    :Recommended: 
        :math:`F_s/25 \leq f_{ib} \leq F_s/8`

        Note that that closed-loop bandwidth is limited by the amount of delay in the open-loop
        system. 
        
    :Feasible values: 
        :math:`(0,10^6]`

----

.. _des_z:

**Damping:**

    :keyword: 
        :code:`des_z`
    
        Desired closed-loop damping :math:`\zeta_{ib}` [-].

    :Type: 
        ``float``
          
    :Default: 
        :math:`0.8`
          
    :Recommended: 
        :math:`0.8`
          
    :Feasible values: 
        :math:`(0,1)`

----

.. _des_mm:

**Modulus Margin:**

    :keyword: 
        :code:`des_mm`
    
        Desired modulus margin :math:`\Delta M_{ib}` [-].

    :Type: 
        ``float``
          
    :Default: 
        :math:`0.5`
          
    :Recommended*: 
        :math:`0.5`

        A higher value will increase the system robustness to uncertainties, but will degrade the tracking performance.
        Conversly, a lower value will decrease the system robustness to uncertainties, but will enhance the tracking performance.
          
    :Feasible values: 
        :math:`(0,1)`

----

.. _ref_delay:

**Reference Delay:**

    :keyword: 
        :code:`ref_delay`
    
        Value of delay :math:`d_r` [s] to add on the desired second-order system.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0`
          
    :Recommended: 
        In general, :math:`d_r=0` is sufficient for the desired performance. For high performance systems, set :math:`d_r` equal to the open-loop delay.
          
    :Feasible values: 
        :math:`[0,10]`

----

.. _n_integrators:

**Integrators:**

    :keyword: 
        :code:`n_integrators`
    
        Desired number of integrators :math:`n_I` in the :math:`S(z)` polynomial.

    :Type: 
        ``int``
          
    :Default: 
        :math:`2`
          
    :Recommended: 
        :math:`2`
        
        For systems with large open-loop delays, :math:`n_I=1` may be prefered.
          
    :Feasible values: 
        :math:`[1,3]`

----

.. _opt_method:

**Optimization Method:**
          
    :keyword: 
        :code:`opt_method`
    
        Desired optimization method. The string ``Hinf`` refers to :math:`\mathcal{H}_\infty` control, 
        ``H2`` refers to :math:`\mathcal{H}_2` control, and ``H1`` refers to :math:`\mathcal{H}_1` control.

    :Type: 
        ``str``
          
    :Default: 
        ``Hinf``
          
    :Recommended: 
        Depends on the type of desired performance. See :ref:`Current/Field Control` for more information.
          
    :Feasible values: 
        [``Hinf``, ``H2``, ``H1``]

----

.. _n_r:

**Num. Coefficients (R):**

    :keyword: 
        :code:`n_r`
    
        Desired number of coefficients :math:`n_r` in the :math:`R(z)` polynomial.

    :Type: 
        ``int``
          
    :Default: 
        :math:`6`
          
    :Recommended: 
        :math:`6`
        
        A larger value can be used for high performance systems.
          
    :Feasible values: 
        :math:`[4,16]`

----

.. _n_s:

**Num. Coefficients (S):**

    :keyword: 
        :code:`n_s`
    
        Desired number of coefficients :math:`n_s` in the :math:`S(z)` polynomial.

    :Type: 
        ``int``
          
    :Default: 
        :math:`6`
          
    :Recommended: 
        :math:`6`
        
        A larger value can be used for high performance systems.
          
    :Feasible values: 
        :math:`[4,16]`

----

.. _n_t:

**Num. Coefficients (T):**

    :keyword: 
        :code:`n_t`
    
        Desired number of coefficients :math:`n_t` in the :math:`T(z)` polynomial.

    :Type: 
        ``int``
          
    :Default: :math:`6`
          
    :Recommended: 
        :math:`6`
        
        A larger value can be used for high performance systems. If ``opt_method`` is set 
        to :math:`H_1`, set this parameter greater than ``n_r`` and ``n_s``.
          
    :Feasible values: 
        :math:`[4,16]`

----

.. _noise_rej:

**Noise Rejection:**

    :keyword: 
        :code:`noise_rej`
    
        A list of lists that contains the desired frequencies and attenuation values for rejecting noise
        for the sensitivity function :math:`|\mathcal{S}_{d_v y}|` (where :math:`y` can be the current or field.) The
        format of the list is as follows: :math:`[[f_1, A_1], [f_2, A_2],\ldots]` where :math:`f_i` [Hz] refers
        to the frequency to apply the desired attenuation :math:`A_i` [dB]. For example, :math:`[[100, -20]]` 
        signifies that the user desires an attenuation of -20 dB at 100 Hz. 

    :Type: 
        ``list of lists``
          
    :Default: 
        [ ]
          
    :Recommended: 
        Application dependent. Usually, enabeling noise attenuation will degrade performance and/or can 
        require a higher order RST controller.
          
    :Feasible values: 
        :math:`(0, F_s / 2]`

----

.. _n_ilc:

**L-Filter Order**

    :keyword: 
        :code:`n_ilc`
    
        Order :math:`n_{ilc}` of the L-filter used for the ILC algorithm.

    :Type: 
        ``int``
          
    :Default: 
        :math:`5`
          
    :Recommended: 
        Application dependent. In general, a value :math:`n_{ilc}>4` is sufficient.
          
    :Feasible values: 
        :math:`[1,12]`

----

.. _n_q:

**Q-Filter Order:**

    :keyword: 
        :code:`n_q`
    
        Order :math:`n_{q}` of the Q-filter (non-causal FIR) used for the ILC algorithm.

    :Type: 
        ``int``
          
    :Default: 
        :math:`5`
          
    :Recommended: 
        Application dependent. In general, a value :math:`n_{q}>4` is sufficient.
          
    :Feasible values: 
        :math:`[1,12]`

----

.. _q_bw:

**Q-Filter Bandwidth:**

    :keyword: 
        :code:`q_bw`
    
        Desired bandwidth :math:`f_q` [Hz] of the ILC Q-filter.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0`
          
    :Recommended: 
        Application dependent. A value :math:`f_q>0` will enable the Q-filter optimization. 
        A value of :math:`f_q = 0` will set the Q-filter equal to :math:`1` (i.e., disable the
        Q-filter).
          
    :Feasible values: 
        :math:`(0,10^6)`

----

.. _ilc_only:

**ILC Only Flag:**

    :keyword:
        :code:`ilc_only`

        Flag which enables the design of an ILC filter without the RST optimization.
        A ``False`` boolean will enable both an RST and ILC synthesis. A ``True`` boolean
        will synthesize the ILC filters only.
        Note that if this flag is enabled, the RST values will be read from the property
        `REG.I.EXTERNAL.OP <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.I.EXTERNAL.OP>`__
        or
        `REG.B.EXTERNAL.OP <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.B.EXTERNAL.OP>`__ .
        Additionally, ensure that the external RST is working correctly prior to the synthesis by
        running the converter with
        `REG.I.EXTERNAL_ALG <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.I.EXTERNAL_ALG>`__
        or
        `REG.B.EXTERNAL_ALG <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyREG.htm#REG.B.EXTERNAL_ALG>`__
        set to ``ENABLED``.

    :Type:
        ``bool``

    :Default:
        ``False``

    :Recommended:
        N/A

    :Feasible values:
        [``True``, ``False``]

----

Voltage Keys
~~~~~~~~~~~~

.. _damp_bw:

**Damping-loop Bandwidth:**

    :keyword: 
        :code:`damp_bw`
    
        Desired closed-loop bandwidth :math:`f_d` [Hz] for the damping loop.

        Note that that closed-loop bandwidth is limited by the amount of delay in the open-loop
        system.

    :Type: 
        ``float``
          
    :Default: 
        :math:`1.5 f_{bw}^d`, where :math:`f_{bw}^d` is the open-loop bandwidth. This is calculated
        from the FGC properties.
          
    :Recommended: 
        Application dependent.
          
    :Feasible values: 
        :math:`(0,10^6)`

----

.. _damp_z:

**Damping-loop Damping:**

    :keyword: 
        :code:`damp_z`
    
        Desired closed-loop damping :math:`\zeta_d` [-] for the damping loop.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0.8`
          
    :Recommended: 
        :math:`0.8`
          
    :Feasible values: 
        :math:`(0,1)`

----

.. _volt_bw:

**Voltage-loop Bandwidth:**

    :keyword: 
        :code:`volt_bw`
    
        Desired closed-loop bandwidth :math:`f_v` [Hz] for the voltage loop.

        Note that that closed-loop bandwidth is limited by the amount of delay in the open-loop
        system.

    :Type: 
        ``float``
          
    :Default: 
        :math:`f_{bw}^d`, where :math:`f_{bw}^d` is the open-loop bandwidth. This is calculated
        from the FGC properties.
          
    :Recommended: 
        Application dependent.
          
    :Feasible values: 
        :math:`(0,10^6)`

----

.. _volt_z:

**Voltage-loop Damping:**

    :keyword: 
        :code:`volt_z`
    
        Desired closed-loop damping :math:`\zeta_v` [-] for the voltage loop.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0.8`
          
    :Recommended: 
        :math:`0.8`
          
    :Feasible values: 
        :math:`(0,1)`

----

.. _damp_mm:

**Damping Modulus Margin:**

    :keyword: 
        :code:`damp_mm`
    
        Desired modulus margin :math:`\Delta M_d` [-] for the damping loop.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0.4`
          
    :Recommended: 
        :math:`0.4`

        A higher value will increase the system robustness to uncertainties, but will degrade the tracking performance.
        Conversely, a lower value will decrease the system robustness to uncertainties, but will enhance the tracking performance.
          
    :Feasible values: 
        :math:`(0,1)`

----

.. _volt_mm:

**Voltage Modulus Margin:**

    :keyword:
        :code:`volt_mm`

        Desired modulus margin :math:`\Delta M_v` [-] for the voltage loop.

    :Type:
        ``float``

    :Default:
        :math:`0.5`

    :Recommended:
        :math:`0.5`

        A higher value will increase the system robustness to uncertainties, but will degrade the tracking performance.
        Conversely, a lower value will decrease the system robustness to uncertainties, but will enhance the tracking performance.

    :Feasible values:
        :math:`(0,1)`

----

.. _ref_delay_v:

**Reference Delay:**

    :keyword: 
        :code:`ref_delay`
    
        Value of delay :math:`d_r` [s] to add on the desired second-order system.

    :Type: 
        ``float``
          
    :Default: 
        :math:`0`
          
    :Recommended: 
        In general, :math:`d_r=0` is sufficient for the desired performance. For high performance systems, set :math:`d_r` equal to the open-loop delay.
          
    :Feasible values: 
        :math:`[0,10]`

----

.. _opt_method_v:

**Optimization Method:**
          
    :keyword: 
        :code:`opt_method`
    
        Desired optimization method. The string ``Hinf`` refers to :math:`\mathcal{H}_\infty` control, 
        and ``H2`` refers to :math:`\mathcal{H}_2` control.

    :Type: 
        ``str``
          
    :Default: 
        ``Hinf``
          
    :Recommended: 
        Depends on the type of desired performance. See :ref:`Voltage Control` for more information
          
    :Feasible values: 
        [``Hinf``, ``H2``]

----

.. _positive_coeff:

**Positive Coefficients:**
          
    :keyword: 
        :code:`positive_coeff`
    
        A constraint to enable all voltage loop and damping loop parameters to be positive. ``True``
        will enable the constraint; ``False`` will disable the constraint.

    :Type: 
        ``bool``
          
    :Default: 
        ``False``
          
    :Recommended: 
        For optimal performance, this constraint should be disabled.
          
    :Feasible values: 
        [``True``, ``False``]

----

.. _kd_0:

**Remove Kd:**
          
    :keyword: 
        :code:`kd_0`
    
        A constraint to set the damping loop parameter :math:`k_d=0`. ``True``
        will enable the constraint; ``False`` will disable the constraint.

    :Type: 
        ``bool``
          
    :Default: 
        ``False``
          
    :Recommended: 
        For optimal performance, this constraint should be disabled.
          
    :Feasible values: 
        [``True``, ``False``]