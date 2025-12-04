const puppeteer = require("puppeteer-core");
const fs = require('fs');
// const chromium = require("@sparticuz/chromium");

// exports.handler = async (event) => {
//   const proxyServer = 'http://176.65.132.67:3128';
//   // const proxyServer = 'http://139.99.237.62:80';

//   const launchArgs = [
//     // ...chromium.args,
//     ...(proxyServer ? [`--proxy-server=${proxyServer}`] : []),
//     ...[],

//   ];
//   const browser = await puppeteer.launch({
//     // args: puppeteer.defaultArgs({ args: launchArgs, headless: "shell" }),
//     args: [
//       `--proxy-server=${proxyServer}`,
//       '--no-sandbox',
//     ],
//     // executablePath: await chromium.executablePath(),
//     executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
//     headless: "shell",
//   });

//   const page = await browser.newPage();
//   await page.goto('https://httpbin.org/ip');
//   await page.screenshot({ path: 'apify.jpeg', fullPage: true });


//   // const page = await browser.newPage();
//   // await page.goto("https://www.douglaschen.ca/", { waitUntil: "networkidle0" });
//   // console.log("page loaded");

//   // const content = await page.content();
//   // const has = content.toLowerCase().includes("douglas");
//   // await browser.close();

//   // console.log(has);

//   // return { has };
// };



exports.handler = async (event) => {
  const proxyServer = 'http://gw.dataimpulse.com:823';
  // const proxyUsername = 'cd1e807802fd87b394b0'
  const proxyUsername = 'cd1e807802fd87b394b0__cr.us'
  const proxyPassword = '6bf0a37885540690'
  const browser = await puppeteer.launch({
    args: [
      // `--proxy-server=${proxyServer}`,
      // `--proxy-auth=${proxyUsername}:${proxyPassword}`,
      // '--no-sandbox',
      // '--headless=shell'
    ],
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    // ignoreHTTPSErrors: true
  });
  const page = await browser.newPage();

  const responses = []
  let totalBytes = 0;
  
  page.on('response', async (response) => {
    try {
      const buffer = await response.buffer();
      totalBytes += buffer.length;

      responses.push({
        url: response.url(),
        size: buffer.length,
      })

    } catch (e) {}
  });

  const reqUrlsUsed = [];
  await page.setRequestInterception(true);
  page.on('request', (req) => {
    if (
      req.resourceType() === 'image' ||
      req.resourceType() === 'media' ||
      req.resourceType() === 'font' ||
      req.resourceType() === 'stylesheet' ||
      [
        'scontent-sea1-1.cdninstagram.com/v/t51.2885-15',
        'rsrc.php/v4i8QP4/yM/',
        'png',
        'ico',
        'json',
        'jpg',
        'jpeg',
        'gif',
        'svg',
        'webp',
        'ico',
        'bmp',
        'tiff',
        'ajax'
      ].map((url) => req.url().includes(url)).some(Boolean)
    ) {
      req.abort();
    } else {
      req.continue();
      reqUrlsUsed.push(req.url());
    }
  });
  
  await page.authenticate({
    username: proxyUsername,
    password: proxyPassword
  });

  const urls = [
    "https://www.instagram.com/theubcssa/?hl=en",
    // "https://www.instagram.com/laufey/",
  ];

  let has = false;
  for (const url of urls) {
    await page.goto(url, { waitUntil: "networkidle0", timeout: 120_000 });
    const content = await page.content();
    has = content.includes("DROEe_UCeSu");
  }

  await page.close();
  await browser.close();

  if (!has) {
    // Red text in console (ANSI escape code for red)
    console.log("\x1b[31mID not loaded.\x1b[0m");
  } else {
    // Green text in console (ANSI escape code for green)
    console.log("\x1b[32mID loaded successfully!\x1b[0m");
  }

  console.log(`${(totalBytes / 1_000_000).toFixed(2)} MB`);
  // fs.writeFileSync('reqUrlsUsed.json', JSON.stringify(reqUrlsUsed, null, 2));
  const sortedResponses = responses.sort((a, b) => b.size - a.size);
  fs.writeFileSync('sortedResponses.json', JSON.stringify(sortedResponses, null, 2));


  return {};
};

exports.handler({});