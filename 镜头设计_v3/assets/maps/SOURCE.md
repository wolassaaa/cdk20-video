# Hong Kong coastline

- File: `hk_coastline_osm.json`: OpenStreetMap ways tagged `natural=coastline`, bbox 22.13,113.80 to 22.58,114.48, fetched with the Overpass API (overpass.kumi.systems) on 2026-10-30. OSM data base date 2026-06-01.
- Licence: ODbL. On screen credit: "© OpenStreetMap contributors".
- Processed copy (closed land rings in local metres, simplified to 6 m, plus the Sha Tin to Pak Shek Kok arc): `styleframes/S1/v2/_code/s110/hk_land.json` (script `prep_map.py`).
- Place points are approximate, taken from public maps: Prince of Wales Hospital 22.3794N 114.2014E, CUHK 22.4196N 114.2068E, Hong Kong Science Park 22.4262N 114.2105E.

## Pearl River Delta and Hong Kong boundary (1-11 v2, 10-30)

- OSM `natural=coastline` for the Pearl River Delta, bbox 21.75,112.70 to 23.00,114.90, fetched as tiles through the Overpass API on 2026-10-30, plus the Hong Kong boundary relation 913110. Raw downloads stay local in `styleframes/S1/v2/_code/reel2/map111/dl/` (not in git).
- Processed copy used by the reel: `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/reel2/map111/prd.json` (script `_code/reel2/map111/prep111.py`).
- Licence: ODbL, credit "© OpenStreetMap contributors".
