# -*- coding: utf-8 -*-

import gevent.monkey
gevent.monkey.patch_all()
import gevent
from gevent.queue import Queue, Empty
from gevent.lock import BoundedSemaphore

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
from selenium.common.exceptions import WebDriverException

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

        self.selenium_grid_url = 'http://188.246.227.206:4444/wd/hub'

        self.capabilities = {
          'browserName': 'chrome',
          'chromeOptions':  {
            'useAutomationExtension': False,
            'forceDevToolsScreenshot': True,
            'directConnect': True,
            'args': [
                # '--start-maximized',
                '--disable-infobars',
                '--disable-extensions',
                # '--disable-gpu',
                # '--disable-dev-shm-usage',
                '--no-sandbox',
                '--headless',
                '--window-size=600,480',
                # '--remote-debugging-port=9222',
                # '--crash-dumps-dir=/tmp',
                '--silent',
                '--ignore-certificate-errors',
                '--disable-popup-blocking',
                '--incognito',
            ]
          }
        }

        # drivers
        self.drivers = []

        # gevent queue
        nodes = os.getenv('NODES', 3)
        instances = os.getenv('INSTANCES', 1)
        self.maxsize = int(nodes) * int(instances)

        self.tasks = Queue(maxsize=self.maxsize)
        self.semaphore = BoundedSemaphore(1)

        # page config
        self.page_object_count = 100

    def get_last_page(self):
        driver = None
        last_page = 0
        try:
            # self.options.add_argument('--proxy-server={url}'.format(url=proxy_url))
            self.semaphore.acquire()
            driver = webdriver.Remote(command_executor=self.selenium_grid_url, desired_capabilities=self.capabilities)
            driver.set_page_load_timeout(10*60)
            self.drivers.append(driver)
            self.semaphore.release()

            page_url = 'http://public.fsa.gov.ru/table_rds_pub_ts/'
            driver.get(page_url)
            wait = WebDriverWait(driver, 30*60)
            btn_find = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#btn_find'))
            )
            btn_find.click()

            container_grid = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#ContainerGrid'))
            )

            driver.execute_script('window.tableManager.changePerPage({count})'.format(count=self.page_object_count))

            long_wait = WebDriverWait(driver, 30*60)
            cl_last = long_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.cl_last'))
            )

            onclick = cl_last.get_attribute('onclick')

            regexp = r'page_noid_=(?P<last_page>\d+)'
            result = re.search(regexp, onclick, re.I | re.U)
            last_page = result.group('last_page')

        except (KeyboardInterrupt, Exception) as e:
            print('---> ', str(e))
            if driver:
                driver.quit()
        finally:
            if driver:
                driver.quit()
            if driver in self.drivers:
                self.drivers.remove(driver)

        return int(last_page)

    def save_links(self, worker):
        print('Start worker: {worker}'.format(worker=worker))
        PS_DB_NAME = os.getenv('PS_DB_NAME', '')
        PS_USER = os.getenv('PS_USER', '')
        PS_PASSWORD = os.getenv('PS_PASSWORD', '')
        PS_HOST = os.getenv('PS_HOST', 'localhost')
        PS_PORT = os.getenv('PS_PORT', 5432)

        driver = None
        try:
            # self.options.add_argument('--proxy-server={url}'.format(url=proxy_url))
            self.semaphore.acquire()
            driver = webdriver.Remote(command_executor=self.selenium_grid_url, desired_capabilities=self.capabilities)
            driver.set_page_load_timeout(10*60)
            self.drivers.append(driver)
            self.semaphore.release()

            page_url = 'http://public.fsa.gov.ru/table_rds_pub_ts/'
            driver.get(page_url)
            wait = WebDriverWait(driver, 30*60)
            btn_find = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#btn_find'))
            )
            btn_find.click()

            container_grid = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#ContainerGrid'))
            )

            driver.execute_script('window.tableManager.changePerPage({count})'.format(count=self.page_object_count))

            container_grid = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#ContainerGrid'))
            )

            last_page = self.last_page

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

                    print('worker: {worker}, ready {ready} of {all}'.format(
                        worker=worker, ready=len(pages), all=last_page
                    ))

                    script = """downloadPage('index.php',
                        'ajax=main&' + tableManager.getControlsData() + '&idid_=content-table'+getDivContent('tableContent-content-table')+
                        '&page_byid_={count}&page_noid_={page_id}',
                        'tableContent-content-table');
                    """

                    long_wait = WebDriverWait(driver, 30*60)

                    page_per_worker = int(self.last_page / self.maxsize)
                    range_start = page_per_worker * worker
                    range_end = page_per_worker * worker + page_per_worker

                    if worker + 1 == self.maxsize:
                        range_end += self.last_page % self.maxsize + 1

                    for page_id in range(int(last_page)):
                        if page_id not in pages and range_start <= page_id < range_end:
                            driver.execute_script(script.format(count=self.page_object_count, page_id=page_id))
                            container_grid = long_wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.cl_navigPage'))
                            )
                            links = driver.find_elements_by_css_selector('.dl_cert_num.object.link')
                            links = [link.get_attribute('href') for link in links]
                            print(page_id, ' => ', len(links))

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
                        elif not range_start <= page_id < range_end:
                            pass
                        else:
                            print('worker: {worker}, page: {page_id} already done!'.format(worker=worker, page_id=page_id))

            print('Done worker: {worker}'.format(worker=worker))
        except WebDriverException as e:
            print('Error worker: {worker}, error: {error}'.format(worker=worker, error=str(e)))
            if driver:
                driver.quit()
            self.save_links(worker)
            print('save_links')
        finally:
            if driver:
                driver.quit()
            if driver in self.drivers:
                self.drivers.remove(driver)

    def worker(self, n):
        try:
            while True:
                task = self.tasks.get(timeout=60*60*24)
                self.save_links(task)
        except Empty:
            print('Quitting time!')

    def main(self):
        for i in range(self.maxsize):
            self.tasks.put(i)

    def test_site(self):
        self.last_page = self.get_last_page()
        print('Last page: {last_page}'.format(last_page=self.last_page))
        time.sleep(3)

        while(True):
            gevent.joinall([
                gevent.spawn(self.main),
                *[gevent.spawn(self.worker, n) for n in range(self.maxsize)],
            ])

if __name__ == '__main__':
    unittest.main()
