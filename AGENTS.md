# Rules and physical constraints:

- Design using only 1206 passives and `Base` ICs
- Do not rotate ICs, passives and included modules
- Move components away from banana footprints, as I might bolt them with nuts and will need the space for a wrench
- Keep the summing nodes short, place the resistors near the Op-amp's `-` pin of `Base/MIX.xcb`
- If space allows, keep distance between traces even though DRC might allow it
- ~12mm to from the panel’s rear face to the PCB’s nearest surface to fit NKK switches (the tallest part) + 1.6mm PCB — the rest is used for components
- Modules with LEMO connectors are standalone units (26mm deep) encosed with a case produced by `../Mill` tool
- - LEMO.1B.303 connects to angled MTA156-3 (vertical won't fit inside the case)
- - The MTA footprint needs some space around to allow for plugging/unplugging
- `4x4` and `8x4` are made for 4U Random Source superslim boats (43mm deep)
- - `4x4` module has 4.25x7" panel and 4x6" PCBs
- - `8x4` module has 8.5x7" panel and 8x6" PCBs
- - Power is connected to vertical MTA156-4
- Panel layout is provided by `../Panels` tool as a `*.panel` file
- SMT compontnts are top layer parts and assembled by PCBA service
- THT components are assembled by hand with user facing controls located at the bottom layer while MTA connectors placed at the top
- The PCB therefore is flipped left to right relative to the Panel
- Try to make it looking good aestetically
