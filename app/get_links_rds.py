# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DOTENV_PATH = os.path.join(BASE_PATH, '.env')
load_dotenv(DOTENV_PATH)

import unittest
import re
import time
import psycopg2
import logging

from selenium import webdriver
from selenium.webdriver.common import proxy
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestSite(unittest.TestCase):

    def setUp(self):
        # logger
        self.logger = logging.getLogger(__name__)
        logger_handler = logging.FileHandler(os.path.join(BASE_PATH, '{}.log'.format(__file__)))
        logger_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        logger_handler.setFormatter(logger_formatter)
        self.logger.addHandler(logger_handler)
        self.logger.setLevel(logging.WARNING)
        self.logger.propagate = False

        # options
        proxy_protocol = 'http'
        proxy_host = '212.237.53.59'
        proxy_port = '3128'
        proxy_url = '{protocol}://{host}:{port}'.format(protocol=proxy_protocol, host=proxy_host, port=proxy_port)

        self.options = webdriver.ChromeOptions()
        self.selenium_grid_url = 'http://188.246.227.206:4444/wd/hub'

    def save_links(self):
        PS_DB_NAME = os.getenv('PS_DB_NAME', '')
        PS_USER = os.getenv('PS_USER', '')
        PS_PASSWORD = os.getenv('PS_PASSWORD', '')
        PS_HOST = os.getenv('PS_HOST', 'localhost')
        PS_PORT = os.getenv('PS_PORT', 5432)

        driver = None
        try:
            # self.options.add_argument('--proxy-server={url}'.format(url=proxy_url))
            driver = webdriver.Remote(command_executor=self.selenium_grid_url, desired_capabilities=self.options.to_capabilities())

            page_url = 'http://public.fsa.gov.ru/table_rds_pub_ts/'
            driver.get(page_url)
            wait = WebDriverWait(driver, 30*60)
            btn_find = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#btn_find'))
            )
            btn_find.click()
            driver.get_screenshot_as_file('./btn_find.png')

            container_grid = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#ContainerGrid'))
            )

            page_object_count = 100

            driver.execute_script('window.tableManager.changePerPage({count})'.format(count=page_object_count))

            long_wait = WebDriverWait(driver, 30*60)
            cl_last = long_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.cl_last'))
            )

            onclick = cl_last.get_attribute('onclick')

            regexp = r'page_noid_=(?P<last_page>\d+)'
            result = re.search(regexp, onclick, re.I | re.U)
            last_page = result.group('last_page')

            with psycopg2.connect(dbname=PS_DB_NAME, user=PS_USER, password=PS_PASSWORD, host=PS_HOST, port=PS_PORT) as connection:
                with connection.cursor() as cursor:
                    sql_string = """
                        SELECT "page"
                        FROM "declaration"
                        GROUP BY "page"
                        ORDER BY "page";
                    """
                    cursor.execute(sql_string)

                    pages = [row[0] for row in cursor.fetchall()]

                    print('Ready {ready} of {all}'.format(ready=len(pages), all=last_page))

                    script = """downloadPage('index.php',
                        'ajax=main&' + tableManager.getControlsData() + '&idid_=content-table'+getDivContent('tableContent-content-table')+
                        '&page_byid_={count}&page_noid_={page_id}',
                        'tableContent-content-table');
                    """

                    for page_id in range(0, int(last_page)):
                        if page_id not in pages:
                            driver.execute_script(script.format(page_id=page_id, count=page_object_count))
                            container_grid = long_wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.cl_navigPage'))
                            )
                            driver.get_screenshot_as_file('./checkpoint.png')
                            links = driver.find_elements_by_css_selector('.dl_cert_num.object.link')
                            links = [link.get_attribute('href') for link in links]
                            print(page_id, ' => ', len(links))
                            # driver.get_screenshot_as_file('./container_grid_page_{}.png'.format(page_id))

                            values = []
                            for link in links:
                                values.append("('{link}', {page_id})".format(link=link, page_id=page_id))
                            values = ", ".join(values)

                            sql_string = """
                                INSERT INTO "declaration" ("url", "page")
                                VALUES {values};
                            """.format(values=values)
                            cursor.execute(sql_string)
                            connection.commit()
                        else:
                            print('Page {page_id} already done!'.format(page_id=page_id))

            print('Done!')
        except (KeyboardInterrupt, Exception) as e:
            print('---> ', str(e))
            if driver:
                driver.quit()
        finally:
            print('quit')
            if driver:
                driver.quit()

    def test_site(self):
        self.save_links()

if __name__ == '__main__':
    unittest.main()
