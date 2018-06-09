"""
<body>
    <form method="post" action="reg.php">
        <div style="margin-top: 10%">
        <center>
              <img src="captcha.php?sid=87159" width="120" height="20" alt="">
                <br>
                <br>
              <input type="text" name="captcha">
                <br>
                <br>
              <input type="submit" value="Проверить">
        </center>
        </div>
    </form>

<div></div></body>
"""

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract
import cv2
import unittest
import time
import requests

from selenium import webdriver
from selenium.webdriver.common import proxy
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

class TestRosAccreditationSite(unittest.TestCase):

    def setUp(self):
        proxy_protocol = 'http'
        proxy_host = '212.237.53.59'
        proxy_port = '3128'
        proxy_url = '{protocol}://{host}:{port}'.format(protocol=proxy_protocol, host=proxy_host, port=proxy_port)

        self.options = webdriver.ChromeOptions()
        # self.options.add_argument('--proxy-server={url}'.format(url=proxy_url))
        self.selenium_grid_url = 'http://188.246.227.206:4444/wd/hub'


    def test_proxy(self):
        captcha_img = 'captcha.png'
        src_img = 'src.png'
        scale_img = 'scale.png'
        white_img = 'white.png'
        gray_img = 'gray.png'

        driver = None
        try:
            driver = webdriver.Remote(command_executor=self.selenium_grid_url, desired_capabilities=self.options.to_capabilities())
            ready = True
            summary = 0
            while(ready):
              page_url = 'http://188.254.71.82/rds_ts_pub/?show=view&id_object=556AE866F9B347A497651EBAD80B3EEE'
              driver.get(page_url)
              wait = WebDriverWait(driver, 3*60)
              image = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body > form center > img'))
              )

              location = image.location
              size = image.size

              driver.get_screenshot_as_file(captcha_img)

              image = Image.open(captcha_img)
              left = location['x']
              top = location['y']
              right = location['x'] + size['width']
              bottom = location['y'] + size['height']
              image = image.crop((left, top, right, bottom))
              image.save(src_img)

              result = input('Введите капчу: ').encode('utf8').decode('utf8')

              input_text = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="captcha"]'))
              )
              script = """document.querySelector('input[name="captcha"]').setAttribute('value', '{value}')""".format(value=result)

              driver.execute_script(script);

              driver.get_screenshot_as_file('./captcha_set_value.png')
              submit = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="submit"]'))
              )
              submit.click();
              time.sleep(5)
              driver.get_screenshot_as_file('./captcha_result.png')
              summary+=1
              try:
                wait = WebDriverWait(driver, 10)
                container_grid = wait.until(
                  EC.presence_of_element_located((By.CSS_SELECTOR, '#ContainerGrid'))
                )
                ready = False
                print('Done')
              except (NoSuchElementException, TimeoutException):
                ready = True
                print('Retry')
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
