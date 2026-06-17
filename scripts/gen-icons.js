#!/usr/bin/env node
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const svgPath = path.resolve(__dirname, '../frontend/public/favicon.svg');
const outDir = path.resolve(__dirname, '../frontend/public/icons');

fs.mkdirSync(outDir, { recursive: true });

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];

async function generate() {
  const svg = fs.readFileSync(svgPath);

  for (const size of sizes) {
    await sharp(svg)
      .resize(size, size)
      .png()
      .toFile(path.join(outDir, `icon-${size}x${size}.png`));
    console.log(`Generated ${size}x${size}`);
  }

  // Maskable icon: add 20% padding so the logo sits inside the safe zone
  const maskableSize = 512;
  const logoSize = Math.round(maskableSize * 0.8);
  const offset = Math.round((maskableSize - logoSize) / 2);

  const resized = await sharp(svg).resize(logoSize, logoSize).png().toBuffer();
  await sharp({
    create: {
      width: maskableSize,
      height: maskableSize,
      channels: 4,
      background: { r: 79, g: 70, b: 229, alpha: 1 }, // indigo-600
    },
  })
    .composite([{ input: resized, top: offset, left: offset }])
    .png()
    .toFile(path.join(outDir, 'maskable-512x512.png'));
  console.log('Generated maskable 512x512');

  console.log('All icons generated.');
}

generate().catch((e) => { console.error(e); process.exit(1); });
