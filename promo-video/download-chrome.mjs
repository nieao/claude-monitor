import https from "https";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const url = "https://registry.npmmirror.com/-/binary/chrome-for-testing/144.0.7559.20/win64/chrome-headless-shell-win64.zip";
const zipPath = path.join(__dirname, "chrome-hs.zip");
const extractDir = path.join(__dirname, "chrome-headless-shell");

function download(targetUrl) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(zipPath);
    https.get(targetUrl, { timeout: 300000 }, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        console.log("Redirected to:", response.headers.location);
        file.close();
        return download(response.headers.location).then(resolve).catch(reject);
      }
      const total = parseInt(response.headers["content-length"] || "0", 10);
      let downloaded = 0;
      response.on("data", (chunk) => {
        downloaded += chunk.length;
        if (total > 0) {
          const pct = ((downloaded / total) * 100).toFixed(1);
          process.stdout.write(`\r  ${pct}% (${(downloaded / 1e6).toFixed(1)}MB / ${(total / 1e6).toFixed(1)}MB)`);
        }
      });
      response.pipe(file);
      file.on("finish", () => {
        file.close();
        console.log("\nDownload complete!");
        resolve();
      });
    }).on("error", reject);
  });
}

async function extract() {
  console.log("Extracting...");
  const { default: extractZip } = await import("extract-zip");
  await extractZip(zipPath, { dir: extractDir });
  fs.unlinkSync(zipPath);
  console.log("Done! Chrome Headless Shell extracted to:", extractDir);
}

async function main() {
  console.log("Downloading Chrome Headless Shell from npmmirror...");
  // Clean up previous attempts
  if (fs.existsSync(extractDir)) fs.rmSync(extractDir, { recursive: true });
  if (fs.existsSync(zipPath)) fs.unlinkSync(zipPath);

  await download(url);
  await extract();

  // Verify
  const exe = path.join(extractDir, "chrome-headless-shell-win64", "chrome-headless-shell.exe");
  if (fs.existsSync(exe)) {
    console.log("Verified: chrome-headless-shell.exe exists at", exe);
  } else {
    console.log("Warning: exe not found at expected path. Contents:");
    console.log(fs.readdirSync(extractDir));
  }
}

main().catch(e => { console.error(e); process.exit(1); });
