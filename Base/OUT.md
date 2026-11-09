`OUT.pcb` contains two inverting output stages. Use `JACK_OUT1` and `JACK_OUT2` for external connectors; these nodes are after the 470 Ω series resistors. `AMP_OUT1` and `AMP_OUT2` expose the op-amp outputs before those resistors for internal connections that need the amplifier node.

| Pin | Name | Connection |
| --- | --- | --- |
| 1 | `JACK_OUT1` | Channel 1 connector output, after R3 |
| 2 | `IN1` | Channel 1 inverting summing node |
| 3 | `AMP_OUT1` | Channel 1 op-amp output, before R3 |
| 4 | `AMP_OUT2` | Channel 2 op-amp output, before R4 |
| 5 | `IN2` | Channel 2 inverting summing node |
| 6 | `JACK_OUT2` | Channel 2 connector output, after R4 |

R1 and R2 set the feedback resistance for channels 1 and 2, respectively; both default to 100 kΩ. Their feedback is taken from `JACK_OUT1/2`, while the 47 pF feedback capacitors connect to `AMP_OUT1/2`.
