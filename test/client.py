import mock
import requests
import unittest

from pwinty import Pwinty, PwintyError

TEST_MERCHANT_ID = '123456'
TEST_API_KEY = '7890123'


class FakeApiResponse(object):
    def __init__(self, status, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.status_code = status

    def json(self):
        return {
            'args': self.args,
            'kwargs': self.kwargs,
        }


def get_fake_response(*args, **kwargs):
    return FakeApiResponse(200, *args, **kwargs)


def get_fake_error(*args, **kwargs):
    return FakeApiResponse(404, Message='That did not work')


class PwintyClientTest(unittest.TestCase):
    def setUp(self):
        self.client = Pwinty(TEST_MERCHANT_ID, TEST_API_KEY)

    def tearDown(self):
        self.client = None

    def test_init(self):
        with self.assertRaises(Exception):
            client = Pwinty()

        self.assertEqual(self.client.api, 'https://sandbox.pwinty.com/v2')
        self.assertEqual(
            self.client.headers['X-Pwinty-REST-API-Key'], TEST_API_KEY)
        self.assertEqual(
            self.client.headers['X-Pwinty-MerchantId'], TEST_MERCHANT_ID)

        client = Pwinty(
            TEST_MERCHANT_ID, TEST_API_KEY, sandbox=False, version='v3')
        self.assertEqual(client.api, 'https://api.pwinty.com/v3')

    def test_http_mapping(self):
        self.assertEqual(
            self.client._get_http_method('POST'), requests.post)
        self.assertEqual(
            self.client._get_http_method('DELETE'), requests.delete)
        self.assertEqual(
            self.client._get_http_method('PUT'), requests.put)
        self.assertEqual(
            self.client._get_http_method('GET'), requests.get)

    @mock.patch('pwinty.requests')
    def test_call_api(self, requests_mock):
        requests_mock.get = get_fake_response
        requests_mock.delete = get_fake_response
        requests_mock.post = get_fake_response
        requests_mock.put = get_fake_response

        request = self.client._call_api('GET', '')
        self.assertEqual(
            request.args[0], 'https://sandbox.pwinty.com/v2')
        self.assertEqual(
            request.kwargs['headers'], self.client.headers)
        self.assertEqual(
            request.kwargs['data'], {})

        request = self.client._call_api(
            'POST', '',
            order_id=23,
            address='123 Fake St',
        )

        self.assertEqual(request.kwargs['data']['order_id'], 23)
        self.assertEqual(
            request.kwargs['data']['address'], '123 Fake St')

        # Test error handling
        requests_mock.get = get_fake_error
        with self.assertRaises(PwintyError):
            self.client._call_api('GET', '')


if __name__ == '__main__':
    unittest.main()
