const { Builder, Browser } = require('selenium-webdriver');
const chromium = require('@sparticuz/chromium');


exports.handler = async (event) => {
  // const url = "https://www.instagram.com/theubcssa/";
  const url = "https://www.douglaschen.ca/";
  console.log(`CHROMIUM: ${await chromium.executablePath()}`);

  // const options = new chromium.Options();
  // options.addArguments(
  //   '--headless=new',
  //   '--disable-gpu'
  // );
  // options.setChromeBinaryPath('/opt/chrome/chrome');

  // // Mock proxy (replace with real if needed)
  // // const mockProxy = '103.174.102.95:80'; // example IP:port
  // // options.addArguments(`--proxy-server=http://${mockProxy}`);

  // const driver = new Builder()
  //   .forBrowser(Browser.CHROME)
  //   .setChromeOptions(options)
  //   .build();

  // try {
  //   await driver.get(url);
  //   await driver.sleep(5000);
  //   const html = await driver.getPageSource();
  //   return { html };
  // } finally {
  //   await driver.quit();
  // }
};