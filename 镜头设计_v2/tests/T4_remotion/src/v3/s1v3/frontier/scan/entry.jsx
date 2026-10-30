// SCAN (S1 v3 frontier test) entry. Bundle:
//   npx remotion bundle src/v3/s1v3/frontier/scan/entry.jsx --out-dir=<scratch>/scan_bundle
import React from "react";
import {registerRoot, Composition} from "remotion";
import {ScanTest, DUR} from "./ScanTest";
import {ScanExtra} from "./ScanExtra";
const Root = () => <>
  <Composition id="ScanTest" component={ScanTest} durationInFrames={DUR} fps={30} width={1920} height={1080}/>
  <Composition id="ScanExtra" component={ScanExtra} durationInFrames={1} fps={30} width={1920} height={1080}/>
</>;
registerRoot(Root);
