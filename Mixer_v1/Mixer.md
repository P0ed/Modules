# MIX4 mixer

`Mixer.pcb` is a 101.6 × 152.4 mm board for `../5Y-Mission/Panels/MIX4.panel`. Coordinates below are millimetres, viewed from the rear/component side, with the origin at the board's upper-left corner. The panel is mirrored horizontally relative to this view. The board sits 3.175 mm inside either panel side and 12.7 mm below the panel top.

The six copper layers are SIG / GND / VCC / VEE / GND / SIG. Signal ICs and LED drivers are AD823A in SOIC-8. All fixed resistors and capacitors are 1206. Panel controls, LEDs, and connectors use their specified through-hole footprints. Imported Base modules remain dependencies; keep the `Base` directory with this design.

## Connections

All MTA-156-3 footprints are rotated 90°. Viewed from this PCB side, pin 1 is the rightmost pad, pin 2 is the centre pad, and pin 3 is the leftmost pad.

| Connector | PCB centre X, Y | Pin 1 | Pin 2 | Pin 3 |
| --- | --- | --- | --- | --- |
| J_PWR | 76.2, 25.4 | −12 V / VEE | GND | +12 V / VCC |
| J_RETURN | 25.4, 25.4 | GND/shield | RETURN + | RETURN − |
| J_OUT | 25.4, 50.8 | GND/shield | MAIN + | MAIN − |
| J_SEND | 76.2, 50.8 | GND/shield | SEND + | SEND − |

Wire these headers to the corresponding panel-mounted LEMO sockets. Their four PCB clearance holes are Ø12.5 mm at Y = 12.7 and X = 12.7, 38.1, 63.5, 88.9. Rear-view hole order from left to right is RETURN, OUT, SEND, POWER.

| Panel row, front view | Left to right |
| --- | --- |
| Upper bananas | AUX SEND, SEND out, MAIN out, AUX MAIN |
| Lower bananas | Channel 1, Channel 2, Channel 3, Channel 4 |
| Upper controls | AUX SEND phase, SEND activity LED, MAIN activity LED, AUX MAIN phase |
| Lower switches | Channel 1, Channel 2, Channel 3, Channel 4 routing |
| Pots | Channel 1, Channel 2, Channel 3, Channel 4 levels |

Each 100 kΩ linear pot has pin 1 grounded, pin 2 as the buffered wiper, and pin 3 connected to its input. Each channel switch uses common pin 2 for the buffered level, throw pin 1 for MAIN, and throw pin 3 for SEND. Channels feed exactly one bus at a time. SW5 controls AUX SEND phase; SW6 controls AUX MAIN phase. Their throw 1 selects inversion and throw 3 selects normal polarity. Auxiliary inputs have unity gain and fixed bus assignments.

## Signal levels

The banana buses are DC coupled. Their nominal full-scale signal is 10 Vpp (±5 V). The MAIN sum comprises the channels routed to MAIN, phase-selected AUX MAIN, and the independent balanced RETURN. The SEND sum comprises channels routed to SEND and phase-selected AUX SEND. RETURN never feeds SEND internally.

SEND and MAIN LEMO outputs have differential gain 0.33 relative to their banana buses: a nominal 10 Vpp banana signal produces 3.3 Vpp between pins 2 and 3, with each leg carrying 1.65 Vpp around ground. RETURN has differential gain 100/33, restoring 3.3 Vpp differential to nominal 10 Vpp internally. These are gain calibrations, not amplitude limiters; summing multiple full-scale signals can clip.

Use 0.1% resistors for R_BAL_*, R_RET_*, and the feedback resistors R1/R2 inside M_BAL_SEND and M_BAL_OUT. Use 1206 resistors rated at least 0.5 W for the 470 Ω output-series resistors R3/R4 inside M_BUS, M_BAL_SEND, and M_BAL_OUT. Other resistor values shown in the design are nominal. Supply bypass capacitors are 1206 2.2 µF, rated 50 V; use X7R. Signal feedback capacitors are 47 pF C0G/NP0. Envelope/reference capacitors are 1206 1 µF, rated 50 V.

## Activity indication

Each bus has a separate monitor buffer, a ground-clamped half-wave AD823A stage, and a weighted summing stage that reconstructs signal magnitude. A buffered 49.6 mV reference subtracts approximately 99 mV to keep the LEDs dark at zero input. The 33 kΩ / 1 µF filter averages activity over approximately 33 ms. AD823A current-feedback drivers use 3.3 kΩ sense resistors; no additional rectifier diodes or transistors are fitted. The two 5 mm LED footprints align with the panel's amber CLB-300 lenses.

## Verification

Native Xcopper validation passed after saving and reopening the document: zero DRC violations, zero unrouted connections, zero schematic diagnostics, and zero module errors. The resolved assembly contains 130 parts: 12 AD823A packages, 59 fixed resistors, 35 capacitors, and 24 panel controls/LEDs/connectors. All 94 fixed passives are 1206.

Linear DC nodal analysis of the resolved schematic nets passed all 16 channel-routing combinations, all four auxiliary-phase combinations, and zero/full/mixed pot settings (192 cases). Separate checks passed for both balanced output gains, independent RETURN gain, and RETURN common-mode rejection. This analysis uses idealized op-amps with finite gain and excludes the nonlinear LED stages; it does not substitute for hardware audio, stability, noise, or LED brightness measurements.
