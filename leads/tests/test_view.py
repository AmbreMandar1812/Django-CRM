from django.test import TestCase ,Client
from django.urls import reverse

# Create your tests here.
class test_landing_page(TestCase):
    def setUp(self):
           self.client = Client()
    
    def test_index_page(self):
           url = reverse('landing')
           response = self.client.get(url)
           self.assertEqual(response.status_code, 200)
           self.assertTemplateUsed(response, 'landing.html')

