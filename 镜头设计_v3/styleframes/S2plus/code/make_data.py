# Builds s2plus/data/plddt.json and sequence.json from the AlphaFold DB files for AF-Q8IZL9 (CDK20),
# then checks them against the numbers quoted in research/marathon_refs_20261031.md section 2.2.
# The JSON always holds what the files say. A disagreement prints FAIL and exits 1; nothing is adjusted to fit.
# No FASTA is on disk, so the sequence comes from the model: PDB SEQRES, cross-checked with the CIF and the CA atoms.
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
V3 = Path(__file__).resolve().parents[3]
AF = V3 / "assets" / "alphafold"
OUT = V3.parent / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data"
ONE = dict(ALA="A", ARG="R", ASN="N", ASP="D", CYS="C", GLN="Q", GLU="E", GLY="G", HIS="H", ILE="I",
           LEU="L", LYS="K", MET="M", PHE="F", PRO="P", SER="S", THR="T", TRP="W", TYR="Y", VAL="V")
WANT = dict(n=346, bins=dict(H=223, M=72, L=22, D=29), mean_1_302=91.5, mean_303_346=47.2)

conf = json.loads((AF / "AF-Q8IZL9-F1-confidence_v6.json").read_text(encoding="utf8"))
res, score, cat = conf["residueNumber"], conf["confidenceScore"], conf["confidenceCategory"]
pdb = (AF / "AF-Q8IZL9-F1-model_v6.pdb").read_text(encoding="utf8").splitlines()
cif = (AF / "AF-Q8IZL9-F1-model_v6.cif").read_text(encoding="utf8")

# three readings of the same sequence
seqres = "".join(ONE[t] for l in pdb if l.startswith("SEQRES") for t in l[19:].split())
ca = [l for l in pdb if l.startswith("ATOM") and l[12:16].strip() == "CA"]
atoms = "".join(ONE[l[17:20]] for l in ca)
cif_seq = re.search(r"_entity_poly\.pdbx_seq_one_letter_code\s+;(.+?)\n;", cif, re.S).group(1).replace("\n", "")
cif_mean = float(re.search(r"_ma_qa_metric_global\.metric_value\s+([\d.]+)", cif).group(1))

mean = lambda a, b: sum(score[a - 1:b]) / (b - a + 1)
bin_of = lambda s: "H" if s >= 90 else "M" if s >= 70 else "L" if s >= 50 else "D"
bins = {k: cat.count(k) for k in "HMLD"}
got_mean = dict(mean_1_302=round(mean(1, 302), 1), mean_303_346=round(mean(303, 346), 1))
bfac = [float(l[60:66]) for l in ca]

checks = [
    ("346 values", len(score), WANT["n"]),
    ("residues run 1..346 with no gaps", res, list(range(1, WANT["n"] + 1))),
    ("bins from the file's categories H/M/L/D", bins, WANT["bins"]),
    ("categories match the 90/70/50 thresholds", [bin_of(s) for s in score], cat),
    ("residues 1-302 mean", got_mean["mean_1_302"], WANT["mean_1_302"]),
    ("residues 303-346 mean", got_mean["mean_303_346"], WANT["mean_303_346"]),
    ("all-residue mean vs CIF global pLDDT", round(mean(1, 346), 2), cif_mean),
    ("PDB B-factors equal the JSON scores", bfac, score),
    ("sequence length", len(seqres), WANT["n"]),
    ("SEQRES equals CIF one-letter code", seqres, cif_seq),
    ("SEQRES equals the CA atom records", seqres, atoms),
]

OUT.mkdir(parents=True, exist_ok=True)
dump = lambda name, obj: (OUT / name).write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf8")
dump("plddt.json", dict(source="AlphaFold DB AF-Q8IZL9-F1 confidence v6, CC BY 4.0", score=score, cat="".join(cat), bins=bins, **got_mean))
dump("sequence.json", dict(source="AlphaFold DB AF-Q8IZL9-F1 model v6 (UniProt Q8IZL9), CC BY 4.0", seq=seqres))

fails = 0
for name, got, want in checks:
    ok = got == want
    fails += not ok
    show = got if not isinstance(got, (list, str)) else f"{len(got)} items"
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {show}" + ("" if ok else f" (expected {want if not isinstance(want, (list, str)) else str(len(want)) + ' items'})"))
print(f"unrounded means: 1-302 = {mean(1, 302):.3f}, 303-346 = {mean(303, 346):.3f}; score range {min(score)}-{max(score)}")
print(f"below 70: {bins['L'] + bins['D']} bars; below 70 inside 1-302: {sum(s < 70 for s in score[:302])}, inside 303-346: {sum(s < 70 for s in score[302:])}")
print("wrote plddt.json, sequence.json" + (f"; {fails} check(s) FAILED" if fails else "; all checks passed"))
sys.exit(1 if fails else 0)
