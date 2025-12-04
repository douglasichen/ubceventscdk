import boto3
import botocore
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
import time
from swiftshadow import QuickProxy


def handler(event, context):
   print(f'boto3 version: {boto3.__version__}')
   print(f'botocore version: {botocore.__version__}')
   
   url = "https://www.instagram.com/theubcssa/"  # Replace with your URL
   # url = "https://douglaschen.ca"
   options = Options()
   options.add_argument("--disable-gpu")
   # driver = webdriver.Chrome(options=options)

   # driver.get(url)
   # time.sleep(5)  # Wait 30 seconds

   # html = driver.page_source
   # with open("without-proxy.html", "w", encoding="utf-8") as f:
   #     f.write(html)

   # driver.quit()

   [proxy, protocol] = QuickProxy()
   options.proxy = Proxy({
   'proxyType': ProxyType.MANUAL, f'{protocol}' : f'{protocol}://{proxy}'
   })
   driver = webdriver.Chrome(options=options)
   driver.get(url)
   time.sleep(5)  # Wait 30 seconds
   html = driver.page_source
   return {"html": html}