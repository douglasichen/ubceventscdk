const { Builder, Browser } = require('selenium-webdriver');
const chromium = require('@sparticuz/chromium');
const chrome = require('selenium-webdriver/chrome');

exports.handler = async (event) => {
  // const url = "https://www.instagram.com/theubcssa/";
  // const url = "https://www.douglaschen.ca/";

  // const options = new chrome.Options();
  // options.addArguments(
  //   '--headless=new',
  //   '--no-sandbox',
  //   '--disable-dev-shm-usage',
  //   '--disable-gpu',
  //   '--single-process'
  // );
  // options.setChromeBinaryPath(await chromium.executablePath());

  // // Mock proxy (replace with real if needed)
  // // const mockProxy = '195.123.209.48:3128'; // example IP:port
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