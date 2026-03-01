# PyFresco

**Python Frequency RESponse-based Controller Optimization**

PyFresco is a Python toolbox for designing and commissioning controllers for power converter control systems, developed in the context of CERN's accelerator infrastructure. It provides two core packages:

- **ObCD** — Optimization-based Controller Design
- **FRM** — Frequency Response Measurement

Together, these tools allow engineers to measure the open-loop dynamics of a power converter and use that data to synthesize robust, high-performance RST and ILC controllers via convex optimization.

---

## Features

### ObCD — Optimization-based Controller Design

Synthesizes RST and Iterative Learning Control (ILC) filters for the **voltage**, **current**, and **field** control loops of a power converter. Key capabilities:

- **Model-driven and data-driven** controller synthesis — works with FGC property values or measured frequency response data.
- Supports three optimization criteria:
  - **H∞** — minimizes the worst-case tracking error across all frequencies (general-purpose, recommended default).
  - **H₂** — minimizes the average time-domain tracking error.
  - **H₁** — minimizes the peak time-domain tracking error.
- Automatically determines an initial stabilizing RST controller and iteratively refines it to a low-order solution.
- ILC synthesis with Q-filter and learning function optimization, guaranteeing asymptotic stability of the learning algorithm.
- Results are written directly back to the FGC device via `pyfgc`.

### FRM — Frequency Response Measurement

Measures the frequency response function (FRF) between two signals on a live FGC device. Supports two excitation methods:

- **Sine-fit** — injects sinusoidal signals at user-defined frequency points and computes magnitude/phase via a sine-fit algorithm.
- **PRBS** (Pseudorandom Binary Sequence) — injects a broadband noise-like signal to excite all frequencies simultaneously.

The measured FRF can be fed directly into ObCD for data-driven controller synthesis.

---

## Installation

```bash
pip install pyfresco
```

### Dependencies

| Package   | Version    |
|-----------|------------|
| Python    | 3.6 or 3.7 |
| PyFGC     | ≥ 1.4.1    |
| NumPy     | ≥ 1.18.5   |
| CVXPY     | ≥ 1.1.1    |
| CVXOPT    | ≥ 1.2.5    |
| Control   | ≥ 0.8.3    |
| Pandas    | ≥ 1.0.5    |
| Tabulate  | ≥ 0.8.7    |
| SciPy     | ≥ 1.5.2    |

---

## Quick Start

### ObCD — Current/Field Loop Controller Design

```python
import pyfresco

# 1. Load default UI parameters for current control
params = pyfresco.obcd.UiParams.get_default_i(device='MY_FGC_DEVICE', rbac_token='...')

# 2. Customize parameters (optional)
params.des_bw = 100       # Desired closed-loop bandwidth [Hz]
params.des_z = 0.8        # Desired damping factor
params.des_mm = 0.5       # Desired modulus margin
params.opt_method = 'Hinf'  # Optimization criterion: 'Hinf', 'H2', or 'H1'
params.n_r = 6            # RST polynomial orders
params.n_s = 6
params.n_t = 6

# 3. Build the plant model from FGC properties
model = pyfresco.obcd.build_model(params, device='MY_FGC_DEVICE', rbac_token='...')

# 4. Run the optimization
result = pyfresco.obcd.solve(model, params)

# 5. Write results back to FGC
pyfresco.obcd.FgcProperties.to_fgc_ib(result, params, device='MY_FGC_DEVICE', rbac_token='...')
```

### ObCD — Voltage Loop Controller Design

```python
params = pyfresco.obcd.UiParams.get_default_v(device='MY_FGC_DEVICE', rbac_token='...')
params.volt_bw = 50       # Voltage loop bandwidth [Hz]
params.damp_bw = 75       # Damping loop bandwidth [Hz]
params.opt_method = 'Hinf'

model = pyfresco.obcd.build_model(params, device='MY_FGC_DEVICE', rbac_token='...')
result = pyfresco.obcd.solve(model, params)
pyfresco.obcd.FgcProperties.to_fgc_v(result, params, device='MY_FGC_DEVICE', rbac_token='...')
```

### FRM — Frequency Response Measurement (PRBS)

```python
# Load default PRBS measurement parameters
frm_params = pyfresco.frm.UiParams.get_default_prbs()

# Customize
frm_params.ref_mode = 'V_REF'
frm_params.meas_mode = 'I_MEAS'
frm_params.k_order = 12
frm_params.amplitude_pp = 0.5

# Run measurement (connects to live FGC)
frf = pyfresco.frm.meas.run(frm_params, device='MY_FGC_DEVICE', rbac_token='...')
```

### FRM — Frequency Response Measurement (Sine-fit)

```python
frm_params = pyfresco.frm.UiParams.get_default_sine()
frm_params.ref_mode = 'V_REF'
frm_params.meas_mode = 'I_MEAS'
frm_params.num_freq = 200

frf = pyfresco.frm.meas.run(frm_params, device='MY_FGC_DEVICE', rbac_token='...')
```

---

## Control Modes

PyFresco supports three control loop configurations:

| Mode | Description | Typical Input | Typical Output |
|------|-------------|---------------|----------------|
| `I`  | Current control | `V_REF` | `I_MEAS` |
| `B`  | Field (magnetic) control | `V_REF` | `B_MEAS` |
| `V`  | Voltage control | `F_REF_LIMITED` | `V_MEAS_REG`, `I_MEAS`, `I_CAPA` |

---

## Optimization Methods

| Method | Criterion | Best Used When |
|--------|-----------|----------------|
| `Hinf` | Minimizes worst-case tracking error (H∞ norm) | General-purpose — recommended default |
| `H2`   | Minimizes average time-domain error (H₂ norm) | Minimizing RMS tracking error |
| `H1`   | Minimizes peak time-domain error (H₁ norm) | Minimizing overshoot / peak error |

### Performance Index (H∞)

| Rating | H∞ value | H₁ / H₂ value |
|--------|----------|----------------|
| Good | [0, 1.3) | [0, 0.15) |
| Satisfactory | [1.3, 1.8) | — |
| Bad | [1.8, ∞) | [0.15, ∞) |

---

## Package Structure

```
pyfresco/
├── __init__.py
├── __version__.py
├── obcd/                      # Optimization-based Controller Design
│   ├── __init__.py
│   ├── props.py               # UiParams and FgcProperties classes
│   ├── build_model.py         # Plant model construction
│   ├── solve.py               # Optimization solver entry point
│   ├── OptAlgoIB.py           # RST/ILC optimizer for current/field loops
│   ├── OptAlgoV.py            # Optimizer for voltage loop
│   ├── opt_select.py          # Algorithm selection logic
│   ├── common_funcs.py        # Shared utility functions
│   ├── constants.py           # Physical and algorithmic constants
│   └── exceptions.py          # Custom exceptions and input validation
└── frm/                       # Frequency Response Measurement
    ├── __init__.py
    ├── props.py               # UiParams for FRM
    ├── meas.py                # PRBS and sine measurement orchestration
    ├── meas_avg.py            # Averaging and signal processing
    ├── sine_conversion.py     # Sine-fit algorithm
    ├── constants.py           # FRM constants
    └── exceptions.py          # FRM-specific exceptions
```

---

## Notes

- A **stabilizing RST controller must be loaded** into the FGC before running any FRM measurement (PRBS or sine-fit), as the measurement is initialized in closed-loop mode.
- For data-driven ObCD, it is recommended to measure the open-loop FRF with the FRM tool first and pass the result to the optimizer.
- PyFresco uses the **ECOS** and **CVXOPT** solvers (via CVXPY) for semi-definite programming (SDP) problems.
- The ObCD algorithm automatically increases RST polynomial order if a feasible solution cannot be found at the initially specified order.

---

## Version

Current version: `0.1.4dev`
