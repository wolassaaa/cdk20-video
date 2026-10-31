"""HKBU SCIE1007 coursework science video. Lantern T5 (W4): the last frame of the motion film, so the film stops exactly on this still. The measured number is a stencil cut through the wall with solid light behind it. The pocket is AI-predicted, so it stays in cold rays. 048 is our own re-docking, so it sits in punched-plate light. See film.py."""
from film import F_END, frame
from lk import save

save(frame(F_END - 1), "T5.png")
