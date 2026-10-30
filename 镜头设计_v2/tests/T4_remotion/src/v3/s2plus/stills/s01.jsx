// Still 01 · 2-02. Klein half, A half, the research question in the largest Voice, nothing else. Method 13 only.
// The cut sits on x = 960, so 4K footage crops to 1920x2160 without scaling.
import React from "react";
import {Stage, Voice, PersonPlaceholder, K, M, colW} from "../kit";

const QUESTION = ["How can", "computer-aided", "methods help", "scientists find", "and assess", "potential cancer", "drug candidates?"];  // verbatim once joined with spaces

export default () => <Stage bg={K.klein}>
  {/* y 78 sets the first cap top on the 96 margin; the last descender ends near 975 */}
  {/* 6 columns, not 5: at 120 px the longest line sets 675 px, so colW(5) = 634 would wrap it and break the seven-line setting */}
  <Voice x={M} y={78} w={colW(6)} size={120} on={K.klein}>{QUESTION.map(l => <div key={l}>{l}</div>)}</Voice>
  <PersonPlaceholder who="A" side="right" lean={-120} eye/>
</Stage>;
