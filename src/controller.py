'''
Handles the logic for the control algorithm independently of the system it controls.
'''

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(None, None)):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.min_out, self.max_out = output_limits
        
        self._integral = 0
        self._prev_error = 0
    
    def compute(self, measurement, dt):
        """
        Calculates the control output based on measurement and time step.
        """
        # 1. Calculate Error
        error = self.setpoint - measurement
        
        # 2. Proportional Term
        P = self.Kp * error
        
        # 3. Integral Term (Accumulate error over time)
        self._integral += error * dt
        I = self.Ki * self._integral
        
        # 4. Derivative Term (Rate of change of error)
        D = self.Kd * ((error - self._prev_error) / dt)
        
        # 5. Calculate Output
        output = P + I + D
        
        # 6. Save error for next step
        self._prev_error = error
        
        # 7. Clamp output
        if self.min_out is not None: output = max(self.min_out, output)
        if self.max_out is not None: output = min(self.max_out, output)
        
        return output