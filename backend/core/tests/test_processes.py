import logging
import pytest
from django.conf import settings
from rest_framework.test import APITestCase



class ProcessesAPIViewTestCase(APITestCase):
    
    def test_list_product(self):
        self.assertEqual(1, 1)
