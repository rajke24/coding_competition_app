from django.test import LiveServerTestCase, TestCase
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


class RankingTest(TestCase):

    def test_case(self):
        selenium = webdriver.Chrome(ChromeDriverManager().install())
        selenium.get('http://127.0.0.1:8000/')
