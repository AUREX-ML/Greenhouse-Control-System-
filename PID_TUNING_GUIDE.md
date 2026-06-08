# PID Controller Tuning Guide

## Table of Contents
1. [PID Fundamentals](#pid-fundamentals)
2. [Current Tuning](#current-tuning)
3. [Tuning Methods](#tuning-methods)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Strategies](#advanced-strategies)

---

## PID Fundamentals

### The Three Terms

A PID controller calculates the control output as:

$$u(t) = K_p \cdot e(t) + K_i \int_0^t e(\tau) d\tau + K_d \frac{de(t)}{dt}$$

Where:
- **e(t)** = setpoint − measurement (error)
- **Kp** = Proportional gain
- **Ki** = Integral gain  
- **Kd** = Derivative gain

### Understanding Each Term

#### Proportional Term: Kp · e(t)

**What it does:** Reacts to current error

**Analogy:** "The soil is dry NOW → turn on the pump harder"

**Mathematical form:**
```
P = Kp * error
```

**Effect on system:**
| If Kp is... | System becomes... | Effect |
|---|---|---|
| **Too small** | Sluggish, slow to respond | Takes forever to reach setpoint |
| **Too large** | Oscillatory, overshoots | Moisture bounces around setpoint |
| **Just right** | Fast but stable | Quick convergence |

**Range:** 0.001 to 0.1 (problem-dependent)

---

#### Integral Term: Ki · ∫ e dt

**What it does:** Accumulates past errors to eliminate steady-state error

**Analogy:** "The soil has been slightly dry for 10 minutes → slowly ramp up the water"

**Mathematical form:**
```python
integral += error * dt  # Accumulate error over time
I = Ki * integral
```

**Effect on system:**
| If Ki is... | System becomes... | Effect |
|---|---|---|
| **Zero** | Constant offset | Moisture won't reach setpoint exactly |
| **Too large** | Slow to respond, windup | Takes long time to settle |
| **Too small** | Integrator works slowly | Good steady-state, but sluggish |
| **Just right** | Perfect steady-state | Moisture stays at setpoint |

**Range:** 0.00001 to 0.001 (usually 10-100× smaller than Kp)

---

#### Derivative Term: Kd · de/dt

**What it does:** Predicts future error based on rate of change

**Analogy:** "The moisture is rising fast → ease off the water before we overshoot"

**Mathematical form:**
```python
D = Kd * ((error - prev_error) / dt)
```

**Effect on system:**
| If Kd is... | System becomes... | Effect |
|---|---|---|
| **Zero** | Oscillatory, overshoots | No damping on rise |
| **Too large** | Sluggish, dampens too much | Response becomes jerky |
| **Too small** | Slight overshoot | Acceptable behavior |
| **Just right** | Smooth rise to setpoint | Critical damping |

**Range:** 0.01 to 1.0 (problem-dependent, often largest term)

---

## Current Tuning

### Default Parameters in `main.py`

```python
pid = PIDController(
    Kp=0.005,          # Proportional gain
    Ki=0.00005,         # Integral gain (100x smaller than Kp)
    Kd=0.2,             # Derivative gain (40x larger than Kp)
    setpoint=0.50,      # Target soil moisture (50%)
    output_limits=(0, 0.01)  # Min and max irrigation rate
)
```

### Performance Characteristics

**Expected behavior with default tuning:**

1. **First 1 hour:** Moisture rises from 0.4 to 0.5 (setpoint)
2. **Hours 1–12:** Moisture holds steady near 0.5
3. **Irrigation output:** 
   - Low at night (< 0.002 m/s)
   - Peaks at noon (≈ 0.005 m/s)
   - Returns to baseline in evening

**Why these values were chosen:**
- **Kp = 0.005**: Small because small errors cause large moisture changes
- **Ki = 0.00005**: Tiny to avoid integral windup (preventing oscillation)
- **Kd = 0.2**: Large to provide good damping and smooth response

---

## Tuning Methods

### Method 1: Ziegler-Nichols (ZN)

The classic method for industrial tuning.

#### Step 1: Find Critical Gain (K_u)

1. Set Ki = 0 and Kd = 0 (proportional only)
2. Gradually **increase Kp** until the system oscillates continuously
3. Record the value when oscillation just begins → **K_u**
4. Record the oscillation period → **P_u** (in seconds)

#### Step 2: Calculate Tuning Parameters

```python
# For PID controller
Kp = 0.6 * K_u
Ki = 1.2 * K_u / P_u
Kd = 3.0 * K_u * P_u / 40

# For PI controller (Kd = 0)
Kp = 0.45 * K_u
Ki = 0.54 * K_u / P_u
```

#### Step 3: Fine-tune

If response is too aggressive, multiply all gains by 0.8. If too sluggish, multiply by 1.2.

#### Example Application

```python
# Suppose you find:
K_u = 0.02    # Critical gain
P_u = 300     # Period = 5 minutes = 300 seconds

# Ziegler-Nichols PID tuning:
Kp = 0.6 * 0.02 = 0.012
Ki = 1.2 * 0.02 / 300 = 0.00008
Kd = 3.0 * 0.02 * 300 / 40 = 0.45

# Update your controller:
pid = PIDController(Kp=0.012, Ki=0.00008, Kd=0.45, 
                     setpoint=0.50, output_limits=(0, 0.01))
```

---

### Method 2: Trial and Tune (Empirical)

Quickest method for practitioners.

#### Procedure

1. **Start conservative:** Begin with Kp = 0.001, Ki = Ki_min, Kd = 0
2. **Increase Kp** until response is fast enough but not oscillating
3. **Increase Kd** to reduce overshoot
4. **Increase Ki** only if steady-state error persists

#### Quick Reference

| Problem | Symptom | Solution |
|---------|---------|----------|
| **Slow response** | Takes > 1 hour to reach setpoint | ↑ Kp by 50% |
| **Oscillation** | Moisture bounces ± 0.05 around target | ↓ Kp by 30%, ↑ Kd by 50% |
| **Overshoot** | Peaks at 0.55 before settling to 0.50 | ↑ Kd by 50% |
| **Steady-state error** | Moisture plateaus at 0.48 (misses 0.50) | ↑ Ki by 100% |
| **Noisy output** | Pump turns on/off rapidly (chattering) | ↓ Kd by 50%, add deadband |

---

### Method 3: Using the Jupyter Notebook

The interactive notebook allows you to:

1. Run simulation with current gains
2. Observe output plots
3. Adjust gains in the cell
4. Re-run immediately
5. Compare results side-by-side

**This is the **recommended method** for learning!**

---

## Troubleshooting

### Problem 1: System Oscillates (Bounces Around Setpoint)

**Symptoms:**
- Moisture overshoots to 0.55, drops to 0.45, repeats
- Control output jitters
- Never settles smoothly

**Diagnosis:** Kp is too large (system is over-responsive)

**Solution:**
```python
# Before
pid = PIDController(Kp=0.02, Ki=0.0001, Kd=0.2, ...)

# After: Reduce Kp, increase Kd (more damping)
pid = PIDController(Kp=0.01, Ki=0.0001, Kd=0.3, ...)
```

**Advanced:** Check if derivative term is helping. Try:
- Increase Kd to add smoothing
- Add derivative filter to reduce noise

---

### Problem 2: Slow/Sluggish Response

**Symptoms:**
- Starts at 0.4, takes 3+ hours to reach 0.5
- System doesn't respond to disturbances quickly
- Plant stress due to slow corrections

**Diagnosis:** Kp is too small

**Solution:**
```python
# Before
pid = PIDController(Kp=0.001, Ki=0.00001, Kd=0.1, ...)

# After: Increase Kp
pid = PIDController(Kp=0.005, Ki=0.00005, Kd=0.2, ...)
```

**Caution:** Don't increase Kp too fast → can cause oscillation

---

### Problem 3: Steady-State Error (Doesn't Reach Setpoint)

**Symptoms:**
- Moisture reaches 0.48 and stops (never reaches 0.50)
- System is stable but off-target
- Integral term not accumulating enough

**Diagnosis:** Ki is too small or system has a steady-state disturbance

**Solution:**
```python
# Before
pid = PIDController(Kp=0.005, Ki=0.00001, Kd=0.2, ...)

# After: Increase Ki
pid = PIDController(Kp=0.005, Ki=0.0001, Kd=0.2, ...)  # 10x larger
```

**Advanced:** Check for unmodeled disturbances:
- Is k_drain too high?
- Is solar radiation estimate wrong?
- Is there a sensor bias?

---

### Problem 4: Pump Chattering (Rapid On/Off)

**Symptoms:**
- Control output oscillates: [0, 0, 0, max, max, 0, 0, max, ...]
- Pump turns on/off every second
- Inefficient, damages pump

**Diagnosis:** Kd is too small or dt is too small

**Solutions:**

**Option A: Increase Kd (smooth the output)**
```python
pid = PIDController(Kp=0.005, Ki=0.00005, Kd=0.5, ...)  # Higher Kd
```

**Option B: Add a Deadband (ignore small errors)**
```python
error = setpoint - measured_moisture
if abs(error) < 0.01:  # 1% deadband
    u1_cmd = 0.0
else:
    u1_cmd = pid.compute(measured_moisture, dt)
```

**Option C: Increase time step (less frequent updates)**
```python
dt = 30.0  # Update every 30 seconds instead of 10
```

---

### Problem 5: Unrealistic Output (Exceeds Limits)

**Symptoms:**
- Control output goes negative (impossible!)
- Output exceeds physical pump capacity
- System becomes infeasible

**Diagnosis:** Output limits are set incorrectly or gains are too large

**Solution:** Check `output_limits`:
```python
# Before (incorrect)
pid = PIDController(Kp=0.05, Ki=0.001, Kd=0.5,
                     setpoint=0.50,
                     output_limits=(0, 0.02))  # Too high?

# After (physical limits)
pid = PIDController(Kp=0.005, Ki=0.00005, Kd=0.2,
                     setpoint=0.50,
                     output_limits=(0, 0.01))  # Realistic pump rate
```

**Verify:**
- Maximum irrigation rate should be ~ 0.005-0.01 m/s (5-10 mm/hour)
- Minimum should be 0.0 (pump can turn off)

---

## Advanced Strategies

### Strategy 1: Dynamic Setpoint (Day/Night Cycling)

Save water by lowering the target moisture at night when evaporation is low.

```python
# Inside the simulation loop
current_hour = (t / 3600.0) % 24

if 6 <= current_hour <= 18:  # Daytime
    pid.setpoint = 0.50  # High moisture (plants need it)
else:  # Nighttime
    pid.setpoint = 0.35  # Lower moisture (reduce drainage waste)

u1_cmd = pid.compute(measured_moisture, dt)
```

**Water savings:** 20-30%
**Crop safety:** Maintains health (roots don't dry out at 0.35)

---

### Strategy 2: Anti-Windup (Integral Clipping)

Prevent the integral term from growing unbounded when output is saturated.

```python
class PIDController:
    def compute(self, measurement, dt):
        error = self.setpoint - measurement
        
        P = self.Kp * error
        
        # Integral term
        self._integral += error * dt
        I = self.Ki * self._integral
        
        D = self.Kd * ((error - self._prev_error) / dt)
        
        output = P + I + D
        
        # Clamp output
        if self.min_out is not None:
            output = max(self.min_out, output)
        if self.max_out is not None:
            output = min(self.max_out, output)
        
        # Anti-windup: Back-calculate integral to prevent growth
        # when output is saturated
        if output != P + I + D:  # Output was clamped
            # Reset integral to prevent further growth
            if abs(error) < 0.05:  # Only when error is small
                self._integral *= 0.9  # Decay integral slowly
        
        self._prev_error = error
        return output
```

**Effect:** Prevents integral from growing while pump is at max/min

---

### Strategy 3: Feed-Forward Control

Use the solar radiation forecast to proactively increase irrigation during expected peak heat.

```python
# Inside the simulation loop
# Get current solar radiation
hour = (t / 3600.0) % 24
u2_solar = 5000 * np.sin((np.pi * hour) / 12) if 0 <= hour <= 12 else 0

# Calculate feed-forward term (proportional to solar)
# Higher solar → higher evaporation → more water needed
k_ff = 0.000001  # Tuned empirically
feed_forward = k_ff * u2_solar

# Calculate PID normally
pid_output = pid.compute(measured_moisture, dt)

# Combine: PID handles errors, feed-forward handles disturbance
u1_cmd = pid_output + feed_forward

# Clamp to physical limits
u1_cmd = max(0, min(0.01, u1_cmd))
```

**Benefit:** Anticipates evaporation → smoother control
**Trade-off:** Requires accurate solar model

---

### Strategy 4: Adaptive Tuning (Gain Scheduling)

Change PID gains based on operating conditions.

```python
def get_adaptive_gains(current_hour, current_temp):
    """
    Adjust PID gains based on environmental conditions
    """
    if 6 <= current_hour <= 18 and current_temp > 25:
        # Hot day: More responsive, more damping
        return {'Kp': 0.008, 'Ki': 0.00008, 'Kd': 0.3}
    elif current_hour < 6 or current_hour > 18:
        # Night: Less responsive (less disturbance)
        return {'Kp': 0.002, 'Ki': 0.00002, 'Kd': 0.1}
    else:
        # Default
        return {'Kp': 0.005, 'Ki': 0.00005, 'Kd': 0.2}

# In simulation loop
gains = get_adaptive_gains(current_hour, current_temp)
pid.Kp = gains['Kp']
pid.Ki = gains['Ki']
pid.Kd = gains['Kd']
```

**Benefit:** Optimized for each condition
**Complexity:** More parameters to tune

---

### Strategy 5: Sensor Filtering

Smooth noisy moisture measurements to prevent control jitter.

```python
class SimpleLowPassFilter:
    def __init__(self, alpha=0.1):
        """
        Simple exponential moving average
        alpha: smoothing factor (0 to 1)
            - Low alpha (0.05): Smooth but slow
            - High alpha (0.3): Responsive but noisy
        """
        self.alpha = alpha
        self.filtered = None
    
    def filter(self, raw_value):
        if self.filtered is None:
            self.filtered = raw_value
        else:
            self.filtered = self.alpha * raw_value + (1 - self.alpha) * self.filtered
        return self.filtered

# In simulation loop
filter = SimpleLowPassFilter(alpha=0.1)
measured_moisture = filter.filter(x_log[i, 0])  # Filter raw moisture
u1_cmd = pid.compute(measured_moisture, dt)
```

**Benefit:** Reduces control noise from sensor jitter
**Trade-off:** Adds phase lag (slight delay in response)

---

## Tuning Checklist

Use this checklist to systematically tune your system:

- [ ] **Understand the problem:**
  - [ ] Identify current performance issue (oscillation, slow, etc.)
  - [ ] Decide which KP/Ki/Kd to adjust

- [ ] **Make one change at a time:**
  - [ ] Change only ONE gain
  - [ ] Run simulation, observe plot
  - [ ] Record result (good/bad)
  - [ ] If good, keep change; if bad, revert

- [ ] **Document your tuning:**
  - [ ] Write down Kp, Ki, Kd values and date
  - [ ] Note conditions (temperature, setpoint, etc.)
  - [ ] Keep version history

- [ ] **Validate in new scenarios:**
  - [ ] Test with different setpoints
  - [ ] Test with different temperatures
  - [ ] Test with day/night cycle
  - [ ] Test with disturbances

- [ ] **Consider limitations:**
  - [ ] Physical pump limits
  - [ ] Sensor accuracy
  - [ ] Soil properties
  - [ ] Crop type

---

## Quick Reference: Gain Adjustment Table

```
                    Error is Large    Settling Oscillates  Settling Smooth
Response too slow   ↑ Kp + ↑ Ki       ↓ Kd                 OK
Response too fast   ↓ Kp              ↑ Kd                 ↓ Kp
Overshoot too much  ↓ Kp              ↑ Kd                 ↓ Ki
Reaches setpoint    ↑ Ki              ↑ Ki + ↑ Kd         OK
Doesn't reach       ↑ Ki + ↑ Kp       ↓ Kp + ↑ Ki         ↑ Ki
```

---

## Resources

### Further Reading
- [PID Without a PhD](http://www.embedded.com/design/prototyping-and-development/4211211)
- [Control Tutorials for MATLAB/Simulink](http://ctms.engin.umich.edu/ctms/index.php)
- [Greenhouse Climate Control (Bakker et al., 1995)](https://library.wur.nl/)

### Tools
- Python Control Library: `pip install control`
- Scipy: `solve_ivp()` for exact ODE solving
- Matplotlib: Visualization of results

### Communities
- [r/ControlTheory](https://www.reddit.com/r/ControlTheory/)
- [ControlTheory.org Forums](https://www.controltheory.org/)
- [IEEE Control Systems Society](https://css.ieee.org/)

---

**Document Version:** 1.0  
**Last Updated:** June 2026  
**Difficulty Level:** Beginner → Advanced
