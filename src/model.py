'''
Contains the physics and mathematical modeling of the greenhouse.
'''

import numpy as np

class GreenhouseSystem:
    def __init__(self):
        # --- PHYSICAL CONSTANTS ---
        self.Z = 0.5           # Root zone depth (m)
        self.rho_a = 1.2       # Air density (kg/m^3)
        self.Cp = 1005.0       # Specific heat of air (J/kg·K)
        self.V = 200.0         # Volume of air (m^3)
        self.lam = 2.45e6      # Latent heat of vaporization (J/kg)
        self.h_c = 15.0        # Convective heat transfer coefficient (W/K)
        self.k_drain = 0.0001  # Soil drainage rate (1/s)
        self.alpha = 0.005     # Coupling Coefficient
        
        # Ambient Conditions
        self.T_amb = 25.0      
        self.C_amb = 0.010     

    def get_saturation_concentration(self, T_air):
        """Calculates Saturation Vapor Concentration based on Temperature."""
        es = 0.6108 * np.exp((17.27 * T_air) / (T_air + 237.3))
        es_pa = es * 1000 
        T_kelvin = T_air + 273.15
        C_sat = es_pa / (461.5 * T_kelvin)
        return C_sat

    def get_inputs(self, t, u1_override=None):
        """Determine system inputs (Irrigation, Solar, Vent) at time t."""
        # u1: Irrigation
        u1_irrigation = u1_override if u1_override is not None else 0.0
            
        # u2: Solar Radiation
        hour = t / 3600.0
        if 0 <= hour <= 12:
            u2_solar = 5000 * np.sin((np.pi * hour) / 12)
        else:
            u2_solar = 0.0

        # u3: Ventilation
        u3_vent = 0.5 

        return [u1_irrigation, u2_solar, u3_vent]

    def compute_derivatives(self, t, x, u_override=None):
        """
        Calculates the rates of change (dx/dt).
        x[0]: Soil Moisture, x[1]: Temp, x[2]: Humidity
        """
        theta = x[0]
        T_air = x[1]
        C_vap = x[2]

        # Get inputs
        u = self.get_inputs(t, u1_override=u_override)
        u1, u2, u3 = u[0], u[1], u[2]

        # Physics Calculations
        C_sat = self.get_saturation_concentration(T_air)
        vpd = max(0, C_sat - C_vap) 
        E = self.alpha * theta * vpd

        # 1. Soil Moisture Dynamics
        d_theta = (u1 - E - self.k_drain * theta) / self.Z

        # 2. Air Temperature Dynamics
        thermal_mass = self.rho_a * self.Cp * self.V
        convection = self.h_c * (self.T_amb - T_air)
        d_T_air = (u2 + convection - self.lam * E * self.V) / thermal_mass

        # 3. Humidity Dynamics
        Area = 50.0
        rho_w = 1000.0
        mass_evap_rate = E * rho_w * Area 
        d_C_vap = (mass_evap_rate - u3 * (C_vap - self.C_amb)) / self.V

        return np.array([d_theta, d_T_air, d_C_vap])