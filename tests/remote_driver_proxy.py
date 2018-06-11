import unittest
import time

from selenium import webdriver
from selenium.webdriver.common import proxy
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestSite(unittest.TestCase):

    def setUp(self):
        proxy_protocol = 'http'
        proxy_host = '212.237.53.59'
        proxy_port = '3128'
        proxy_url = '{protocol}://{host}:{port}'.format(protocol=proxy_protocol, host=proxy_host, port=proxy_port)

        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--proxy-server={url}'.format(url=proxy_url))
        self.selenium_grid_url = 'http://188.246.227.206:4444/wd/hub'


    def test_site(self):
        driver = None
        try:
            driver = webdriver.Remote(command_executor=self.selenium_grid_url, desired_capabilities=self.options.to_capabilities())
            page_url = 'http://188.254.71.82/rds_ts_pub/?show=view&id_object=556AE866F9B347A497651EBAD80B3EEE'
            driver.get(page_url)
            driver.get_screenshot_as_file('./proxy.png')
            time.sleep(10)
            driver.get_screenshot_as_file('./proxy2.png')
            # wait = WebDriverWait(driver, 0.5*60)
            # ip_address = wait.until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, '#Text14 > p > span > a > b'))
            # )
            # print(ip_address.text if ip_address else 'None')
        except (KeyboardInterrupt, Exception) as e:
            print('---> ', str(e))
            if driver:
                driver.quit()
        finally:
            print('quit')
            if driver:
                driver.quit()

if __name__ == '__main__':
    unittest.main()
