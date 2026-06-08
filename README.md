# Greenhouse Control System 🌱

A Python-based simulation environment for testing automated control strategies in precision agriculture. This project models the dynamic thermodynamics of a greenhouse—tracking soil moisture, air temperature, and absolute humidity—and implements a PID controller to automate irrigation.

## Overview

This simulation provides a **digital twin** of a greenhouse environment, enabling engineers and agricultural technologists to design, test, and optimize automated irrigation control systems. The system uses real-world physics (coupled differential equations) to model:

- **Soil Moisture Dynamics**: Irrigation input, evapotranspiration, and drainage
- **Air Temperature Dynamics**: Solar radiation, convective heat transfer, and evaporative cooling
- **Humidity Dynamics**: Plant transpiration and ventilation airflow

The simulation demonstrates both **open-loop** (time-based) and **closed-loop** (feedback-based PID) control strategies for maintaining optimal growing conditions.

## Features

✅ **Coupled Physics Simulation** - Models realistic interactions between soil, air, and plant conditions
✅ **PID Controller** - Industry-standard control algorithm for precision irrigation
✅ **Real-World Parameters** - Uses physical constants (latent heat, thermal mass, drainage rates)
✅ **Visualization** - Matplotlib plots showing system dynamics over time
✅ **Modular Architecture** - Separates physics engine from control logic for easy extension

## Project Structure

```
Greenhouse-Control-System-/
├── README.md                 # This file
├── ARCHITECTURE.md           # System design and equations
├── PID_TUNING_GUIDE.md      # How to tune the PID controller
├── main.py                   # Entry point: runs PID control simulation
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py
│   ├── model.py             # GreenhouseSystem physics engine
│   ├── controller.py        # PIDController implementation
│   └── (future modules)
└── notebook.ipynb           # Interactive Jupyter notebook with theory & examples
```

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AUREX-ML/Greenhouse-Control-System-.git
   cd Greenhouse-Control-System-
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Run the simulation

```bash
python main.py
```

This will:
1. Initialize a greenhouse model
2. Create a PID controller tuned for 50% soil moisture
3. Run a 12-hour simulation with 10-second time steps
4. Generate plots showing soil moisture, temperature, and humidity

### Expected Output

The simulation produces three plots:

1. **Soil Moisture vs. Time** (with PID control signal overlay)
   - Shows moisture tracking to the 50% target
   - PID output increases during peak solar hours to compensate for higher evaporation

2. **Air Temperature vs. Time**
   - Follows a sinusoidal pattern mimicking solar radiation
   - Peak temperature around hour 6 (simulated noon)

3. **Absolute Humidity vs. Time**
   - Rises as transpiration increases with temperature
   - Partially removed by ventilation

## How It Works

### The Three State Variables

| Variable | Symbol | Unit | Range | Physical Meaning |
|----------|--------|------|-------|-------------------|
| Soil Moisture | θ | m³/m³ | 0–1 | Volumetric water content of soil |
| Air Temperature | T | °C | Ambient ± 10°C | Greenhouse air temperature |
| Humidity | C_vap | kg/m³ | 0–0.02 | Absolute water vapor content |

### The Three Inputs (u)

| Input | Symbol | Controlled By | Purpose |
|-------|--------|---|---------|
| Irrigation | u₁ | **PID Controller** | Adds water to soil |
| Solar Radiation | u₂ | Physics (sine wave) | Heat disturbance |
| Ventilation | u₃ | Constant | Humidity removal |

### The Coupling Mechanism: Evapotranspiration (E)

The key coupling variable is **Evapotranspiration (E)**:

$$E = \alpha \cdot \theta \cdot \text{VPD}$$

Where:
- **α** = coupling coefficient (0.005)
- **θ** = soil moisture (wetter soil → more evaporation)
- **VPD** = Vapor Pressure Deficit = C_sat(T) - C_vap (drier air → more evaporation)

E affects all three state variables:
- Decreases soil moisture (water leaves the soil)
- Decreases temperature (evaporative cooling)
- Increases humidity (water enters the air)

### The PID Controller

The controller maintains soil moisture at a setpoint (default: 0.50 or 50%) by adjusting irrigation:

$$u_1 = K_p \cdot e(t) + K_i \int e(t)dt + K_d \frac{de(t)}{dt}$$

Where:
- **e(t)** = setpoint − measurement (error)
- **K_p** = 0.005 (Proportional gain)
- **K_i** = 0.00005 (Integral gain)
- **K_d** = 0.2 (Derivative gain)

See [PID_TUNING_GUIDE.md](PID_TUNING_GUIDE.md) for tuning instructions.

## Configuration

### Key Parameters in `src/model.py`

```python
# Greenhouse dimensions and properties
Z = 0.5              # Root zone depth (m)
V = 200.0            # Air volume (m³)
rho_a = 1.2          # Air density (kg/m³)
Cp = 1005.0          # Specific heat of air (J/kg·K)

# Physical processes
lam = 2.45e6         # Latent heat of vaporization (J/kg)
h_c = 15.0           # Convective heat transfer coefficient (W/K)
k_drain = 0.0001     # Soil drainage rate (1/s)
alpha = 0.005        # Coupling coefficient (evapotranspiration)

# Boundary conditions
T_amb = 25.0         # Ambient temperature (°C)
C_amb = 0.010        # Ambient humidity (kg/m³)
```

### PID Tuning in `main.py`

```python
pid = PIDController(
    Kp=0.005,                    # Proportional gain
    Ki=0.00005,                  # Integral gain
    Kd=0.2,                      # Derivative gain
    setpoint=0.50,               # Target soil moisture
    output_limits=(0, 0.01)      # Min/max irrigation rate
)
```

## Advanced Usage

### Example 1: Change the Target Moisture

```python
pid = PIDController(
    Kp=0.005, Ki=0.00005, Kd=0.2,
    setpoint=0.60,  # Higher moisture for sensitive crops
    output_limits=(0, 0.01)
)
```

### Example 2: Adjust the Simulation Duration

```python
total_time = 24 * 3600  # 24-hour simulation instead of 12
dt = 10.0
steps = int(total_time / dt)
```

### Example 3: Test Different Solar Profiles

Edit the `get_inputs()` method in `src/model.py`:

```python
# Cloudy day (reduced peak solar)
u2_solar = 3000 * np.sin((np.pi * hour) / 12)  # Lower amplitude
```

## Interpreting the Results

### Good Control Performance
- ✅ Moisture stays near setpoint (minimal oscillation)
- ✅ Low overshoot (doesn't spike above target)
- ✅ Smooth PID output (no chattering)

### Signs of Tuning Issues
- ⚠️ **Oscillation**: Moisture overshoots setpoint → Reduce Kp, increase Kd
- ⚠️ **Sluggish Response**: Takes too long to reach setpoint → Increase Kp
- ⚠️ **Steady-State Error**: Moisture won't reach setpoint → Increase Ki
- ⚠️ **Noisy Output**: Control signal jiggles → Reduce Kd

See [PID_TUNING_GUIDE.md](PID_TUNING_GUIDE.md) for detailed troubleshooting.

## Architecture

For a detailed explanation of the system architecture, state-space equations, and physics modeling, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | 2.0.2 | Numerical arrays and math |
| matplotlib | 3.9.4 | Visualization and plotting |

All dependencies are listed in `requirements.txt`.

## Example Scenarios

### Scenario 1: Hot, Dry Day
The PID controller automatically increases irrigation during peak sun hours to compensate for higher evaporation. Watch the black dashed line (PID output) increase around hours 4–8.

### Scenario 2: Cool, Cloudy Day
Modify `get_inputs()` to reduce `u2_solar`. The PID needs less irrigation, so water consumption drops.

### Scenario 3: System With Sensor Delay
Add a delay to the measurement:
```python
measured_moisture = x_log[max(0, i-delay_steps), 0]
```
Observe how delays destabilize the system and tuning becomes critical.

## Future Enhancements

- [ ] **Dynamic Setpoint Control**: Day/night cycle for reduced water usage
- [ ] **Deadband Implementation**: Prevent pump chattering
- [ ] **Feed-Forward Control**: Predictive irrigation based on solar forecast
- [ ] **Sensor Noise Simulation**: Realistic noisy measurements
- [ ] **Adaptive PID Tuning**: Auto-tune gains based on disturbances
- [ ] **Multi-Zone Greenhouse**: Model different growth zones independently
- [ ] **Crop-Specific Profiles**: Configurable water needs by plant type

See the Jupyter notebook for more advanced control strategies.

## Contributing

Contributions are welcome! Areas for improvement:

1. **Model Refinements**: Better evapotranspiration equations, soil hydrology
2. **Control Algorithms**: Implement MPC, adaptive control, or machine learning
3. **Hardware Integration**: Connect to real sensor data and actuators
4. **Documentation**: Add more examples and use cases
5. **Testing**: Unit tests and integration tests

## References

### Scientific Papers & Resources
- Magnus Formula for saturation vapor pressure
- Penman–Monteith Evapotranspiration Model
- PID Control Theory (Ogata, Nise)
- Greenhouse Climate Control (Bakker et al., 1995)

### Related Tools
- [Greenhouse Simulation Software (IGPrec)](https://www.wageningen-plant-sciences.com/)
- [Python Control Systems Library](https://python-control.readthedocs.io/)

## License

[Specify your license here, e.g., MIT, Apache 2.0]

## Contact & Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Contact the AUREX-ML team

---

## Quick Troubleshooting

**Q: The simulation doesn't produce any plots**
A: Make sure matplotlib is installed: `pip install matplotlib`

**Q: The moisture overshoots the target**
A: The PID gains need tuning. See [PID_TUNING_GUIDE.md](PID_TUNING_GUIDE.md)

**Q: I want to modify the control strategy**
A: See [ARCHITECTURE.md](ARCHITECTURE.md) for details on how to extend the controller.

**Q: The simulation runs but produces unrealistic results**
A: Check that the initial conditions and physical parameters are realistic for your greenhouse.

---

**Last Updated**: June 2026 | **Version**: 1.0
