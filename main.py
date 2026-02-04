'''
Configuration, Integration Loop, and Plotting.
'''

import numpy as np
import matplotlib.pyplot as plt
from src.model import GreenhouseSystem
from src.controller import PIDController

def run_simulation():
    # --- 1. SETUP ---
    sys = GreenhouseSystem()
    
    # PID Config: Target Moisture 50%
    pid = PIDController(
        Kp=0.005, 
        Ki=0.00005, 
        Kd=0.2, 
        setpoint=0.50, 
        output_limits=(0, 0.01)
    )

    # Time Settings
    total_time = 12 * 3600
    dt = 10.0
    steps = int(total_time / dt)

    # Data Logging
    t_log = np.linspace(0, total_time, steps)
    x_log = np.zeros((steps, 3))
    u_log = np.zeros(steps)

    # Initial State [Moisture, Temp, Humidity]
    current_x = np.array([0.4, 20.0, 0.012]) 

    # --- 2. SIMULATION LOOP ---
    print("Starting simulation...")
    for i in range(steps):
        t = t_log[i]
        
        # A. Measure
        measured_moisture = current_x[0]
        
        # B. Control (PID)
        u1_cmd = pid.compute(measurement=measured_moisture, dt=dt)
        
        # C. Physics Update (Euler Integration)
        # We ask the model for derivatives based on current state and PID input
        dx = sys.compute_derivatives(t, current_x, u_override=u1_cmd)
        
        # Apply derivatives
        current_x = current_x + dx * dt
        
        # D. Log
        x_log[i] = current_x
        u_log[i] = u1_cmd

    print("Simulation complete. Generating plots...")
    plot_results(t_log, x_log, u_log)

def plot_results(t_log, x_log, u_log):
    time_hours = t_log / 3600
    x1, x2, x3 = x_log[:, 0], x_log[:, 1], x_log[:, 2]

    fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # Plot 1: Moisture & PID
    axs[0].plot(time_hours, x1, 'g-', linewidth=2, label='Soil Moisture')
    axs[0].axhline(y=0.5, color='r', linestyle='--', label='Target (0.5)')
    axs[0].set_ylabel('Soil Moisture (%)', fontsize=12)
    axs[0].set_title('Modular PID Control Simulation', fontsize=14)
    axs[0].grid(True)
    
    ax2 = axs[0].twinx()
    ax2.plot(time_hours, u_log, 'k--', alpha=0.5, label='Irrigation Input')
    ax2.set_ylabel('Irrigation Rate', color='k')
    lines, labels = axs[0].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axs[0].legend(lines + lines2, labels + labels2, loc='center right')

    # Plot 2: Temperature
    axs[1].plot(time_hours, x2, 'r-', linewidth=2)
    axs[1].set_ylabel('Temperature (°C)', fontsize=12)
    axs[1].grid(True)

    # Plot 3: Humidity
    axs[2].plot(time_hours, x3 * 1000, 'b-', linewidth=2)
    axs[2].set_ylabel('Humidity (g/m³)', fontsize=12)
    axs[2].set_xlabel('Time (Hours)', fontsize=12)
    axs[2].grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()