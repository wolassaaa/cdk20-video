"""HKBU SCIE1007 coursework video: step 4 画面 of the phone-footage pipeline. Not built yet.

Input:  whole videos, 1_ident/cuts.json is NOT applied here
Output: 4_video/<name>.mp4 (Rec.709, constant 60 fps, upright, matted onto the backdrop, same length) plus the matte
Interface when built (same as steps 0 and 1): inputs(ctx) -> files read, params(ctx) -> settings,
run(ctx, out_dir) -> files written. run.py prints "还没做" while run() is missing.
"""
