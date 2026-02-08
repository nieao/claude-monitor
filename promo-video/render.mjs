/**
 * Programmatic render script for Remotion v4.
 * Usage: node render.mjs
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CHROME_HS = path.resolve(__dirname, "chrome-headless-shell", "chrome-headless-shell-win64", "chrome-headless-shell.exe");

async function main() {
  const entryPoint = path.resolve(__dirname, "src/Root.tsx");
  const outputPath = path.resolve(__dirname, "promo.mp4");

  console.log("Using Chrome Headless Shell:", CHROME_HS);
  console.log("Bundling...");
  const bundled = await bundle({ entryPoint });

  console.log("Selecting composition...");
  const comp = await selectComposition({
    serveUrl: bundled,
    id: "PromoVideo",
    browserExecutable: CHROME_HS,
    chromeMode: "headless-shell",
  });

  console.log(`Rendering ${comp.durationInFrames} frames at ${comp.fps}fps (${comp.width}x${comp.height})...`);
  await renderMedia({
    composition: comp,
    serveUrl: bundled,
    codec: "h264",
    outputLocation: outputPath,
    browserExecutable: CHROME_HS,
    chromeMode: "headless-shell",
  });

  console.log(`Done! Output: ${outputPath}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
