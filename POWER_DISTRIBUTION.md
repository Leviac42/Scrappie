# Power Distribution Plan - Distributed Setup

## Power Budget

### Battery Capacity
- **Type**: 24V 50Ah SLA (Sealed Lead Acid)
- **Energy**: 1200Wh (24V × 50Ah)
- **Usable**: ~960Wh (80% depth of discharge for longevity)

---

## Power Consumption

| Component | Idle | Average | Peak | Notes |
|-----------|------|---------|------|-------|
| **Jetson Orin Nano** | 4W | 12W | 15W | GPIO UART, 2x cameras |
| **AMD 6800u** | 8W | 20W | 28W | SLAM + Nav2 |
| **Surface Pro 9** | 5W | 12W | 15W | Visualization (optional) |
| **MDDS30 + Motors** | 2W | 25W | 100W | Variable with load |
| **RealSense x2** | 3W | 5W | 6W | @ 30 FPS |
| **Cooling Fans** | 2W | 2W | 2W | 2x 80mm fans |
| **Accessories** | 1W | 2W | 3W | WiFi, switches |
| **Total (no Surface)** | 20W | 66W | 156W | Robot-critical only |
| **Total (with Surface)** | 25W | 78W | 171W | Full system |

---

## Runtime Estimates

**Robot-Critical Only** (Jetson + AMD + Motors):
- **Idle**: 960Wh / 20W = **48 hours**
- **Average navigation**: 960Wh / 66W = **14.5 hours**
- **Peak (climbing/obstacles)**: 960Wh / 156W = **6.2 hours**

**Full System** (Including Surface):
- **Average use**: 960Wh / 78W = **12.3 hours**
- **Realistic mixed use**: **8-10 hours**

**Worst Case** (All peak):
- 960Wh / 171W = **5.6 hours**

---

## DC-DC Converter Requirements

### Converter Specifications

| Output | Current | Power | Input Range | Efficiency | Model Suggestion |
|--------|---------|-------|-------------|------------|------------------|
| **19V** | 3A | 57W | 18-36V | >90% | Traco TEN 30-2411 or similar |
| **15V** | 3A | 45W | 18-36V | >90% | Mean Well SD-50B-15 |
| **12V** | 2A | 24W | 18-36V | >90% | Generic buck converter |
| **5V** | 5A | 25W | 18-36V | >85% | Generic USB buck converter |

### Wiring Diagram

```
                    24V 50Ah Battery
                          │
              ┌───────────┴───────────┐
              │  Main Power Switch    │
              │  (50A Circuit Breaker) │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        │                 │                 │
   Direct 24V        DC-DC Array      Fuse Block
        │                 │                 │
        │                 │                 │
        ▼                 ▼                 ▼
    MDDS30          ┌─────────┐     Accessories
  Motor Driver      │         │
                    │ 19V 3A  ├──► AMD 6800u (GPD Win4)
                    │         │
                    ├─────────┤
                    │         │
                    │ 15V 3A  ├──► Jetson Orin Nano
                    │         │
                    ├─────────┤
                    │         │
                    │ 12V 2A  ├──► Surface Pro 9
                    │         │
                    ├─────────┤
                    │         │
                    │ 5V 5A   ├──┬─► RealSense Cameras
                    │         │  ├─► Cooling Fans
                    │ (USB)   │  └─► WiFi Router
                    └─────────┘
```

### Power Distribution Board Layout

```
Location: Center of robot chassis, near battery

[Battery +] ──┬── [50A Fuse] ── [Main Switch] ──┬── MDDS30 (Direct 24V)
              │                                  │
              │                                  ├── DC-DC 19V (AMD)
              │                                  │
              │                                  ├── DC-DC 15V (Jetson)
              │                                  │
              │                                  ├── DC-DC 12V (Surface)
              │                                  │
              │                                  └── DC-DC 5V (Accessories)
              │
[Battery -] ──┴────────── COMMON GROUND ─────────┘
```

---

## Physical Mounting

### DC-DC Converter Mounting
- **Location**: Underside of robot, near battery
- **Mounting**: DIN rail or aluminum plate
- **Spacing**: 1" between converters for airflow
- **Heatsinking**: Small heatsinks on hot converters

### Cable Specifications

| Connection | Wire Gauge | Length | Notes |
|------------|------------|--------|-------|
| Battery → Converters | 12 AWG | 12" | High current paths |
| 19V → AMD | 18 AWG | 24" | 3A max |
| 15V → Jetson | 18 AWG | 18" | 3A max |
| 12V → Surface | 20 AWG | 36" | 2A max |
| 5V → Accessories | 20 AWG | Various | 5A total |
| MDDS30 → Battery | 12 AWG | 12" | Motor current |

### Connectors

- **Battery**: Anderson Powerpole 45A
- **DC-DC Inputs**: Screw terminals
- **DC-DC Outputs**:
  - AMD: 5.5×2.5mm barrel jack
  - Jetson: USB-C PD or barrel jack
  - Surface: Surface Connect or USB-C PD
  - 5V: USB Type-A (multiple)

---

## Safety Features

### Overcurrent Protection

1. **Main Battery**: 50A circuit breaker
2. **Per Converter**: Built-in current limiting
3. **Motors**: MDDS30 has built-in protection
4. **Emergency Stop**: Physical E-stop cuts all power

### Voltage Monitoring

```bash
# Monitor battery voltage via multimeter or dedicated monitor
# Critical levels:
# - Full: 27.6V (float charge)
# - Nominal: 24V
# - Warning: 23V (50% capacity)
# - Critical: 21V (20% capacity, stop operation)
# - Cutoff: 20V (prevent damage)
```

### Low Voltage Shutdown

Implement in software:
```python
# In base_controller.py or separate node
def check_battery_voltage():
    voltage = read_battery_voltage()  # Via ADC or voltage monitor
    if voltage < 21.0:
        rospy.logwarn("CRITICAL: Battery voltage low! Stopping robot.")
        publish_stop_command()
        # Trigger graceful shutdown
```

---

## Thermal Management

### Cooling Strategy

**Passive:**
- Heatsinks on DC-DC converters
- Thermal pads on compute platforms
- Open chassis design for airflow

**Active:**
- 2× 80mm fans (5V, 1W each)
- Intake: Bottom front
- Exhaust: Top rear
- Controlled by temperature sensors

### Fan Control (Optional)

```python
# PWM control based on temperature
if max_temp > 70:
    fan_speed = 100%
elif max_temp > 60:
    fan_speed = 75%
elif max_temp > 50:
    fan_speed = 50%
else:
    fan_speed = 25%  # Always some airflow
```

---

## Testing Procedure

### 1. Bench Test (No Load)

```bash
# With multimeter, verify voltages:
1. Battery voltage: ~24-27V
2. 19V rail: 19.0V ± 0.5V
3. 15V rail: 15.0V ± 0.3V
4. 12V rail: 12.0V ± 0.3V
5. 5V rail: 5.0V ± 0.2V

# Check current draw (idle):
- Should be <5W total with nothing connected
```

### 2. Load Test (Individual Components)

```bash
# Connect one component at a time, measure:
1. AMD 6800u: 8-10W idle, 20-28W load
2. Jetson: 4-6W idle, 12-15W load
3. Surface: 5-8W idle, 12-15W load
4. Cameras: 3W idle, 5-6W active
```

### 3. Full System Test

```bash
# Run full robot stack, monitor:
- Total power draw: Should be <80W average
- Voltage drops: <0.5V under full load
- Thermal: All components <80°C
- Runtime: >6 hours at average use
```

### 4. Peak Load Test

```bash
# Climb ramp or obstacle while running full stack:
- Peak draw: May reach 150-170W momentarily
- Verify no brownouts/reboots
- Thermal: Check for hot spots
```

---

## Power Optimization Tips

1. **Surface Pro Sleep** when not visualizing: Saves 12W
2. **Reduce camera FPS** to 15 when navigation only: Saves 2W
3. **Conservative CPU governor** on AMD when idle: Saves 5-10W
4. **Disable unused services** on all platforms
5. **Use Ethernet** instead of WiFi where possible: Saves 1-2W

---

## Maintenance

### Weekly
- Check all power connections tight
- Clean dust from converters/heatsinks
- Verify battery voltage under load

### Monthly
- Test battery capacity (full discharge cycle)
- Inspect wires for damage
- Clean cooling fans

### Quarterly
- Replace fuses if blown
- Check converter efficiency
- Thermal paste replacement if needed

---

## Upgrade Paths

### If Battery Life Insufficient

1. **Parallel Battery Pack**
   - Add second 24V 50Ah battery
   - Double runtime to 12+ hours
   - ~25 lbs additional weight

2. **Higher Capacity**
   - Upgrade to 24V 75Ah (~1800Wh)
   - 50% more runtime
   - ~15 lbs additional weight

3. **Lithium Upgrade**
   - 24V 60Ah LiFePO4 (~1536Wh usable)
   - Lighter weight (40% less)
   - Higher cost, longer life
   - Built-in BMS

---

## Bill of Materials

| Item | Qty | Est. Cost | Notes |
|------|-----|-----------|-------|
| DC-DC 19V 3A | 1 | $30 | AMD power |
| DC-DC 15V 3A | 1 | $25 | Jetson power |
| DC-DC 12V 2A | 1 | $15 | Surface power |
| DC-DC 5V 5A USB | 1 | $12 | Accessories |
| 50A Circuit Breaker | 1 | $20 | Main protection |
| Anderson Powerpole Connectors | 4 | $15 | Battery/high current |
| Wire (assorted) | - | $25 | 12-20 AWG |
| Terminal blocks | 5 | $10 | Distribution |
| Heatsinks (small) | 4 | $8 | Thermal management |
| 80mm Fans | 2 | $15 | Cooling |
| DIN rail/mounting plate | 1 | $10 | Mounting |
| **Total** | - | **~$185** | Approximate |

---

**Power system designed for 8-10 hour runtime with full capability! ⚡**
