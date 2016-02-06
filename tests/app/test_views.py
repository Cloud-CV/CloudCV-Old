from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class DecafServerTest(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse('decaf-server')

    def test_decaf_server(self):
        fp = open('/home/pydev/Desktop/deshraj.jpg')
        response = self.client.post(self.url, {'file': fp})
        print response
