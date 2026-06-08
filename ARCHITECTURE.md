# System Architecture & Physics Modeling

## Table of Contents
1. [System Overview](#system-overview)
2. [State-Space Equations](#state-space-equations)
3. [Physical Constants](#physical-constants)
4. [Coupling Mechanisms](#coupling-mechanisms)
5. [Module Design](#module-design)
6. [Numerical Integration](#numerical-integration)
7. [Control Architecture](#control-architecture)

---

## System Overview

The Greenhouse Control System is a **coupled nonlinear dynamical system** consisting of three interdependent state variables:

```
State Vector: x(t) = [θ(t), T(t), C_vap(t)]ᵀ

Where:
- θ(t)      = Soil moisture (volumetric fraction) [0, 1]
- T(t)      = Air temperature [°C]
- C_vap(t)  = Absolute humidity [kg/m³]
```

The system is driven by three inputs:

```
Input Vector: u(t) = [u₁(t), u₂(t), u₃(t)]ᵀ

Where:
- u₁(t) = Irrigation rate [m/s] ← CONTROLLED by PID
- u₂(t) = Solar radiation [W] ← DISTURBANCE (time-varying)
- u₃(t) = Ventilation rate [m³/s] ← CONSTANT
```

The system dynamics follow:

$$\dot{\mathbf{x}} = \mathbf{f}(\mathbf{x}, \mathbf{u}, t)$$

where **f** is the physics model implemented in `src/model.py`.

---

## State-Space Equations

### Equation 1: Soil Moisture Dynamics

$$\frac{d\theta}{dt} = \frac{u_1 - E - k_{drain} \cdot \theta}{Z}$$

**Physical Interpretation:**
- **u₁**: Irrigation input increases moisture
- **E**: Evapotranspiration (coupling to temperature and humidity)
- **k_drain · θ**: Gravitational drainage (proportional to current moisture)
- **Z**: Normalization by root zone depth (m)

**Parameters:**
| Parameter | Value | Unit | Meaning |
|-----------|-------|------|---------|
| Z | 0.5 | m | Root zone depth |
| k_drain | 0.0001 | s⁻¹ | Drainage coefficient |
| α | 0.005 | dimensionless | Coupling factor |

**Valid Range:** 0 ≤ θ ≤ 1 (enforced implicitly in simulation)

---

### Equation 2: Air Temperature Dynamics

$$\frac{dT}{dt} = \frac{u_2 + h_c(T_{amb} - T) - \lambda \cdot E \cdot V}{M_{thermal}}$$

Where:
$$M_{thermal} = \rho_a \cdot C_p \cdot V$$

**Physical Interpretation:**
- **u₂**: Solar radiation heats the air (positive contribution)
- **h_c(T_amb - T)**: Convective heat exchange with outside (negative if T > T_amb)
- **λ·E·V**: Latent heat removed by evaporation (cooling effect)
- **M_thermal**: Thermal mass (resistance to temperature change)

**Parameters:**
| Parameter | Value | Unit | Meaning |
|-----------|-------|------|---------|
| ρ_a | 1.2 | kg/m³ | Air density |
| C_p | 1005 | J/(kg·K) | Specific heat of air |
| V | 200 | m³ | Greenhouse air volume |
| λ | 2.45×10⁶ | J/kg | Latent heat of vaporization |
| h_c | 15 | W/K | Convective heat coefficient |
| T_amb | 25 | °C | Ambient temperature |

**Interpretation:** Larger V → slower temperature changes (more stable)

---

### Equation 3: Humidity Dynamics

$$\frac{dC_{vap}}{dt} = \frac{m_{evap} - u_3(C_{vap} - C_{amb})}{V}$$

Where:
$$m_{evap} = E \cdot \rho_w \cdot A_{area}$$

**Physical Interpretation:**
- **m_evap**: Mass flux of water from evapotranspiration (adds humidity)
- **u₃(C_vap - C_amb)**: Ventilation removes excess humidity (negative if C_vap > C_amb)
- **V**: Normalization by air volume

**Parameters:**
| Parameter | Value | Unit | Meaning |
|-----------|-------|------|---------|
| A_area | 50 | m² | Soil surface area |
| ρ_w | 1000 | kg/m³ | Water density |
| C_amb | 0.010 | kg/m³ | Ambient humidity |
| u₃ | 0.5 | m³/s | Constant ventilation rate |

---

## Coupling Mechanism: Evapotranspiration (E)

The **evapotranspiration** variable E couples all three state equations. It represents the physical process of water leaving the soil (via plants and soil surface) to enter the air.

### Magnus Formula for Saturation Vapor Pressure

The saturation vapor pressure (kPa) is calculated using the Magnus approximation:

$$P_{sat}(T) = 0.6108 \cdot \exp\left(\frac{17.27 \cdot T}{T + 237.3}\right)$$

**Where:** T is in °C

This is then converted to concentration using the ideal gas law:

$$C_{sat}(T) = \frac{P_{sat} \cdot 1000}{R_{specific} \cdot T_{Kelvin}}$$

**Where:**
- R_specific = 461.5 J/(kg·K) (specific gas constant for water vapor)
- T_Kelvin = T + 273.15

### Vapor Pressure Deficit (VPD)

The driving force for evaporation is the **Vapor Pressure Deficit**:

$$\text{VPD} = \max(0, C_{sat}(T) - C_{vap})$$

**Physical Meaning:**
- VPD = 0: Air is saturated, no evaporation
- VPD > 0: Air can absorb moisture, evaporation occurs
- Higher VPD → stronger driving force for evaporation

### Evapotranspiration Rate

The actual evapotranspiration is modeled as:

$$E = \alpha \cdot \theta \cdot \text{VPD}$$

**Key Properties:**
- E ∝ θ: Wetter soil → more available water to evaporate
- E ∝ VPD: Drier air → stronger evaporative demand
- E ∝ α: Coupling coefficient (empirical fit)

---

## Physical Constants

### Thermodynamic Properties

| Constant | Value | Unit | Source |
|----------|-------|------|--------|
| λ (Latent heat) | 2.45×10⁶ | J/kg | Water property at ~20°C |
| C_p (Air heat capacity) | 1005 | J/(kg·K) | Dry air at sea level |
| ρ_a (Air density) | 1.2 | kg/m³ | Sea level, dry |
| ρ_w (Water density) | 1000 | kg/m³ | Pure water at 4°C |
| R_specific (Water vapor) | 461.5 | J/(kg·K) | Gas constant |

### Greenhouse Parameters

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| V (Air volume) | 200 | m³ | Typical small greenhouse |
| Z (Root zone depth) | 0.5 | m | Shallow potted plants |
| A_area (Soil surface) | 50 | m² | Growing bed area |
| h_c (Conv. coefficient) | 15 | W/K | Typical for natural venting |

### Control Parameters

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| Kp (Proportional) | 0.005 | s⁻¹ | Tuned for stability |
| Ki (Integral) | 0.00005 | s⁻² | Small to avoid overshoot |
| Kd (Derivative) | 0.2 | 1 | Damping term |
| u₁_max (Max irrigation) | 0.01 | m/s | Pump saturation limit |
| u₁_min (Min irrigation) | 0.0 | m/s | Cannot have negative flow |

---

## Module Design

### `src/model.py` - Physics Engine

**Class:** `GreenhouseSystem`

**Key Methods:**

```python
class GreenhouseSystem:
    def __init__(self):
        """Initialize physical constants"""
        
    def get_saturation_concentration(self, T_air: float) -> float:
        """
        Calculate C_sat using Magnus formula
        Input:  T_air (°C)
        Output: C_sat (kg/m³)
        """
        
    def get_inputs(self, t: float, u1_override: float = None) -> list:
        """
        Determine external inputs at time t
        Returns: [u1_irrigation, u2_solar, u3_vent]
        """
        
    def compute_derivatives(self, t: float, x: ndarray, u_override: float = None) -> ndarray:
        """
        Calculate dx/dt = f(x, u, t)
        Input:  x = [θ, T, C_vap]
        Output: [dθ/dt, dT/dt, dC_vap/dt]
        """
```

**Design Decisions:**
- **Decoupling**: Input generation (`get_inputs`) is separate from dynamics (`compute_derivatives`)
- **Flexibility**: `u_override` allows external control injection (PID control)
- **Extensibility**: Can add sensor noise, model uncertainty, or additional disturbances

---

### `src/controller.py` - PID Controller

**Class:** `PIDController`

**Implementation:**

```python
class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(None, None)):
        """
        Initialize PID gains and setpoint
        """
        
    def compute(self, measurement: float, dt: float) -> float:
        """
        Calculate control output u1
        
        Returns: u1_cmd (clamped to output_limits)
        
        Implements:
        u = Kp*e + Ki*∫e dt + Kd*de/dt
        where e = setpoint - measurement
        """
```

**State Variables:**
- `_integral`: Accumulator for integral term
- `_prev_error`: Previous error for derivative calculation

**Clamping (Anti-Windup):**
```python
u = clamp(u, min_out, max_out)
```
Prevents integral windup when actuator saturates.

---

### `main.py` - Integration & Simulation

**Main Loop Structure:**

```python
for i in range(steps):
    # 1. MEASURE: Read current state
    measured_moisture = current_x[0]
    
    # 2. COMPUTE: Calculate PID output
    u1_cmd = pid.compute(measured_moisture, dt)
    
    # 3. INTEGRATE: Apply physics update
    dx = sys.compute_derivatives(t, current_x, u_override=u1_cmd)
    current_x = current_x + dx * dt
    
    # 4. STORE: Log data
    x_log[i] = current_x
    u_log[i] = u1_cmd
```

**Integration Method:** Forward Euler
- Simple but sufficient for this nonlinear system
- **Advantage**: Matches real microcontroller behavior (fixed time step)
- **Disadvantage**: Less accurate than RK45 for stiff systems

---

## Numerical Integration

### Euler's Method (Forward Euler)

$$x(t + \Delta t) = x(t) + \dot{x}(t) \cdot \Delta t$$

**Used in main.py for realistic microcontroller simulation:**

```python
current_x = current_x + dx * dt
```

**Stability Condition:** Must satisfy CFL condition (Courant-Friedrichs-Lewy):

$$\Delta t < \frac{1}{\lambda_{max}}$$

Where λ_max is the largest eigenvalue of the system Jacobian.

**For this system:**
- Typical stable dt = 10 seconds (chosen empirically)
- Moisture dynamics are slow (hours) → can use large dt
- Temperature dynamics are faster (minutes) → must use moderate dt

### Alternative: RK45 (Runge-Kutta 4/5)

Used in the Jupyter notebook for higher accuracy:

```python
from scipy.integrate import solve_ivp
solution = solve_ivp(sys.dynamics, t_span, x0, method='RK45')
```

**Advantages:**
- Adaptive step size
- Higher accuracy (error ~ O(dt⁵))
- Better for stiff systems

**Disadvantages:**
- Doesn't match microcontroller timing
- Slower computation
- Cannot easily inject control delays

---

## Control Architecture

### Closed-Loop Block Diagram

```
Disturbances (u2, u3)
        ↓
    ┌───────────────────┐
    │  Greenhouse       │
    │  Physics          │ ← Current state x(t)
    │  (Model.py)       │
    └───────────────────┘
           ↓ x(t)
    ┌───────────────────┐
    │  Measurement      │ ← measured_moisture = x[0]
    └───────────────────┘
           ↓
    ┌───────────────────┐
    │  PID Controller   │ ← e = setpoint - measurement
    │  (Controller.py)  │    u1 = compute(e, dt)
    └───────────────────┘
           ↓ u1
    ┌───────────────────┐
    │  Pump/Actuator    │
    │  Saturation       │ ← clamp to [0, 0.01] m/s
    └───────────────────┘
           ↓ u1_saturated
    [Irrigation added to soil]
```

### Information Flow

1. **Sense:** Measure θ from state vector
2. **Think:** Compute error e = setpoint − θ
3. **Act:** Apply PID → u₁ = f(e, ∫e, de/dt)
4. **Update:** Integrate physics → x(t+dt) = x(t) + ẋ·dt
5. **Repeat:** Every Δt = 10 seconds

### Separation of Concerns

| Component | Responsibility | File |
|-----------|---|---|
| **GreenhouseSystem** | Model physics accurately | `src/model.py` |
| **PIDController** | Implement control algorithm | `src/controller.py` |
| **Main Loop** | Orchestrate simulation | `main.py` |

**Benefit:** Can test controller independently or swap in different controllers.

---

## Stability Analysis

### Linearization Around Equilibrium

At steady state (equilibrium):
- dθ/dt = 0 → u₁* = E* + k_drain·θ*
- dT/dt = 0 → u₂* = −h_c(T_amb − T*) + λ·E*·V
- dC_vap/dt = 0 → u₃*(C_vap* − C_amb) = m_evap*

### Eigenvalue Analysis

The Jacobian matrix at equilibrium determines stability:

$$J = \begin{bmatrix} \frac{\partial \dot{\theta}}{\partial \theta} & \frac{\partial \dot{\theta}}{\partial T} & \frac{\partial \dot{\theta}}{\partial C_{vap}} \\ \frac{\partial \dot{T}}{\partial \theta} & \frac{\partial \dot{T}}{\partial T} & \frac{\partial \dot{T}}{\partial C_{vap}} \\ \frac{\partial \dot{C}_{vap}}{\partial \theta} & \frac{\partial \dot{C}_{vap}}{\partial T} & \frac{\partial \dot{C}_{vap}}{\partial C_{vap}} \end{bmatrix}$$

**Stability Requirement:** All eigenvalues λᵢ must have Re(λᵢ) < 0

**In practice:** Validated empirically by observing convergence in simulations.

---

## System Dynamics Characteristics

### Time Scales

| Process | Time Scale | Reason |
|---------|-----------|--------|
| Soil Moisture | Hours | Large Z, slow drainage |
| Temperature | Minutes–Hours | Moderate thermal mass |
| Humidity | Minutes | Small V, ventilation effect |

### Observability

The system is **fully observable** from soil moisture alone:
- Can estimate T from moisture evolution (couples through E)
- Can estimate C_vap from humidity balance

**Implication:** Single-sensor (moisture) control is sufficient.

### Controllability

The system is **controllable** through irrigation (u₁):
- Moisture directly affects evaporation E
- E affects both T and C_vap
- Can move to any desired setpoint by modulating u₁

---

## Future Extensions

### Suggested Enhancements

1. **Improved Evapotranspiration Model**
   - Penman-Monteith equation (more accurate)
   - Crop-specific coefficients

2. **Nonlinear Control**
   - State feedback with gain scheduling
   - Model Predictive Control (MPC)

3. **Stochastic Modeling**
   - Sensor noise
   - Process disturbances
   - Weather uncertainty

4. **Multi-Zone Representation**
   - Different soil types
   - Spatial temperature gradients

5. **Hardware Integration**
   - Real sensor interfaces
   - Actuator control via GPIO
   - MQTT for remote monitoring

---

## References

### Equations
- Magnus formula: Alduchov & Eskridge (1996)
- Latent heat: NIST water properties
- Thermal mass: Heat transfer fundamentals

### Control Theory
- PID tuning: Ziegler-Nichols, Cohen-Coon methods
- Stability: Lyapunov theory, Routh-Hurwitz criterion

### Agricultural Science
- Penman-Monteith ET: Allen et al. (1998)
- Greenhouse climate: Bakker et al. (1995)
- Soil moisture: Van Genuchten (1980)

---

**Document Version:** 1.0  
**Last Updated:** June 2026  
**Maintainer:** AUREX-ML
