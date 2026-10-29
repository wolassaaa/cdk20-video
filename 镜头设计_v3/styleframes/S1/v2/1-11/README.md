# 1-11 · 01:52–02:03 · C · VO: "part of it starts right here, in Hong Kong"

The coastline is real: OpenStreetMap `natural=coastline`, credited "© OpenStreetMap contributors". One red line runs from Sha Tin (Prince of Wales Hospital / CUHK) to Pak Shek Kok (Hong Kong Science Park). It is drawn as one clean arc, not a road route. There are no hospital or university logos; the names are text only.

Source script: `script_v3.3.md` 1-11 (Visual: Hong Kong coastline, a vermilion vessel line from Sha Tin to Pak Shek Kok, then W1). R23 affiliations; F11.

| Option | Idea, and why it fits the line | Tool | Draws on |
|---|---|---|---|
| `opt1_klein-relief.png` | All of Hong Kong cast in one ultramarine pigment, with the land raised as relief under low sun. A single glossy red cord lies on top from Sha Tin to Pak Shek Kok, with big "Hong Kong" type and the coordinates. | Blender Cycles (extruded OSM rings, velvet pigment) + Remotion | Yves Klein, *Relief planétaire* (RP 17 maps the Nice coastline in IKB) |
| `opt2_red-thread.png` | The coast laid as fine bone-white wire on black felt. One red thread is pinned at both places and arcs above the map, caught in a single spotlight. The human, hand-made link between hospital and lab. | Blender Cycles + Remotion | Chiharu Shiota's red-thread installations |
| `opt3_blue-sea_a/b.png` | The asked-for "blue sea, red route". Top-down: pure ultramarine water, matte black land, one red vessel line. Frame a shows the whole territory with "HONG KONG"; frame b is the close-up push with "≈ 5 KM". Clearest read of the set. | Blender Cycles (self-lit sea, slight gloss) + Remotion | Swiss transit-map clarity; colour-field painting |
| `opt4_coordinates.png` | The most minimal: a hairline coast and one red line, with the place written as numbers (FROM 22.38°N 114.20°E / TO 22.43°N 114.21°E). A contemporary-art map in which the text is the work. | Remotion only (SVG from OSM data). Flat on purpose: here the type is the idea. | On Kawara's date and place works; Richard Long's text and line walks |

Code: `_code/s110/prep_map.py` (stitches the OSM ways into land rings → `hk_land.json`), `bl_map.py` (writes the screen positions of the labels to JSON), `render_all.sh`. Remotion: `src/v3/s1v2/s110/F111.jsx`. Data note: `assets/maps/SOURCE.md`.

Fix pass: on every map, land north of the HK boundary (Shenzhen, plus the Dapeng peninsula) is dimmed with a soft black veil of about 60%. The boundary line is approximate and is not drawn. In opt2 the coast wire uses a simplified coast: narrow inlets and river channels (the Shing Mun River, which read as rails) are cut out by `prep_map.py` → `rings_simple`, and the exposure is lifted.

Caveat: the place points and the boundary are approximate (from public maps).
