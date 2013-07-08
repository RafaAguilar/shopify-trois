from ... import ShopifyTroisTestCase

import requests
import mock

from shopify_trois.exceptions import InvalidRequestException, ShopifyException
from shopify_trois import Credentials, Collection
from shopify_trois.engines.http import Json as Shopify
from shopify_trois.engines.http.request import Request
from shopify_trois.models.model import Model


class TestModel(Model):
    resource = "test_models"
    supported = ['update', 'view', 'create', 'index', 'delete']
    properties = ['id', 'name']


class JsonEngineTestCase(ShopifyTroisTestCase):

    def test_class(self):
        expected = "json"
        self.assertEqual(Shopify.extension, expected)

        expected = "application/json; charset=utf-8"
        self.assertEqual(Shopify.mime, expected)

    def test_headers(self):
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        expected = "application/json; charset=utf-8"
        self.assertEquals(shopify.session.headers['Content-Type'], expected)

        credentials = Credentials(oauth_access_token="test")
        shopify = Shopify(shop_name='test', credentials=credentials)
        expected = "test"
        self.assertEquals(
            shopify.session.headers["X-Shopify-Access-Token"],
            expected
        )

    def test_url_for_request(self):
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        request = Request()
        request.resource = "/test"
        url = shopify.url_for_request(request)
        # Note: the base request class does not have an extension.
        expected = "https://test.myshopify.com/admin/test.json"
        self.assertEquals(url, expected)

        request.resource = "/test/mmmm food"
        url = shopify.url_for_request(request)
        # Note: The url generated by url_for_request are not escaped. The
        # actual request.{method} will escape the url for us.
        expected = "https://test.myshopify.com/admin/test/mmmm food.json"
        self.assertEquals(url, expected)

    def test_can_request(self):
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        model = Model()
        try:
            shopify._can_request("create", model)
            self.fail()
        except InvalidRequestException:
            pass

        try:
            shopify._can_request("create", Model)
            self.fail()
        except InvalidRequestException:
            pass

        model.supported.append("create")
        shopify._can_request("create", model)

    def test_update(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        # A new entity should not be updateable without it's pk being set.
        try:
            instance = TestModel()
            shopify.update(instance)
            self.fail()
        except InvalidRequestException:
            pass

        data = '{"test_model": {"name": "test"}}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)

        response.status_code = 200

        shopify.session.put = mock.Mock(return_value=response)
        instance = TestModel(id=2)
        shopify.update(instance)
        self.assertEquals(instance.name, "test")

        #TODO Mock the OAuthEngine.put method to capture the extra prop

        shopify.ignore_model_properties = True
        instance = TestModel(id=1, extra_property="Hello")
        shopify.update(instance)
        self.assertEquals(instance.name, "test")
        self.assertEquals(instance.id, 1)

        shopify.ignore_model_properties = False
        instance = TestModel(id=1)
        result = shopify.update(instance, auto_update=False)
        self.assertIsInstance(result, dict)
        self.assertFalse(hasattr(instance, "name"))

        try:
            response = requests.Response()
            response.encoding = encoding
            response._content = data.encode(encoding)
            response.status_code = 404
            shopify.session.put = mock.Mock(return_value=response)
            result = shopify.update(instance)
            self.fail()
        except ShopifyException:
            pass

    def test_index(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        data = '{"test_models": [{"id": 1, "name": "test"}]}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)
        response.status_code = 200

        shopify.session.get = mock.Mock(return_value=response)

        result = shopify.index(TestModel)
        self.assertIsInstance(result, Collection)

        result = shopify.index(TestModel, auto_instance=False)
        self.assertIsInstance(result, dict)
        self.assertTrue("test_models" in result)

        try:
            response = requests.Response()
            response.encoding = encoding
            response._content = data.encode(encoding)
            response.status_code = 404
            shopify.session.get = mock.Mock(return_value=response)
            result = shopify.index(TestModel)
            self.fail()
        except ShopifyException:
            pass

    def test_fetch(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        data = '{"test_model": {"id": 1, "name": "test"}}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)
        response.status_code = 200

        shopify.session.get = mock.Mock(return_value=response)
        instance = shopify.fetch(TestModel, 2)
        self.assertIsInstance(instance, TestModel)
        self.assertEquals(instance.name, "test")
        self.assertEquals(instance.id, 1)

        result = shopify.fetch(TestModel, 2, auto_instance=False)
        self.assertIsInstance(result, dict)

        try:
            response = requests.Response()
            response.encoding = encoding
            response._content = data.encode(encoding)
            response.status_code = 404
            shopify.session.get = mock.Mock(return_value=response)
            result = shopify.fetch(TestModel, 2)
            self.fail()
        except ShopifyException:
            pass

    def test_add(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        data = '{"test_model": {"id": 1, "name": "test"}}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)
        response.status_code = 201

        shopify.session.post = mock.Mock(return_value=response)

        instance = TestModel(name="test")
        shopify.add(instance)
        self.assertEquals(instance.name, "test")
        self.assertEquals(instance.id, 1)

        #TODO Mock the OAuthEngine.post method to capture the extra prop

        shopify.ignore_model_properties = True
        instance = TestModel(name="test", extra_property="Hello")
        shopify.add(instance)
        self.assertEquals(instance.name, "test")
        self.assertEquals(instance.id, 1)

        shopify.ignore_model_properties = False
        instance = TestModel(name="test")
        result = shopify.add(instance, auto_update=False)
        self.assertEquals(instance.name, "test")
        self.assertFalse(hasattr(instance, "id"))
        self.assertIsInstance(result, dict)

        try:
            response = requests.Response()
            response.encoding = encoding
            response._content = data.encode(encoding)
            response.status_code = 404
            shopify.session.post = mock.Mock(return_value=response)
            result = shopify.add(instance)
            self.fail()
        except ShopifyException:
            pass

    def test_delete(self):
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        response = requests.Response()
        response.status_code = 200
        shopify.session.delete = mock.Mock(return_value=response)

        # A new entity should not be removable.
        try:
            instance = TestModel()
            shopify.delete(instance)
            self.fail()
        except InvalidRequestException:
            pass

        instance = TestModel(id=1)
        result = shopify.delete(instance)
        self.assertTrue(result)

        response = requests.Response()
        response.status_code = 404
        shopify.session.delete = mock.Mock(return_value=response)
        try:
            instance = TestModel(id=4)
            shopify.delete(instance)
            self.fail()
        except ShopifyException:
            pass

    def test_setup_access_token(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        data = '{"access_token": "test"}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)
        response.status_code = 200
        shopify.session.post = mock.Mock(return_value=response)

        shopify.setup_access_token()

        self.assertEquals(credentials.oauth_access_token, "test")
        self.assertTrue('X-Shopify-Access-Token' in shopify.session.headers)

    def test_authorize_app_url(self):
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        expected = "https://test.myshopify.com/admin/oauth/authorize" \
                   "?client_id=&scope="

        result = shopify.authorize_app_url()
        self.assertEquals(
            result,
            expected
        )

    def test_oauth_access_token(self):
        encoding = 'UTF-8'
        credentials = Credentials()
        shopify = Shopify(shop_name='test', credentials=credentials)

        data = '{"access_token": "test"}'
        response = requests.Response()
        response.encoding = encoding
        response._content = data.encode(encoding)
        response.status_code = 200
        shopify.session.post = mock.Mock(return_value=response)

        access_token = shopify.oauth_access_token()
        self.assertEquals(access_token, "test")

        response.status_code = 403
        shopify.session.post = mock.Mock(return_value=response)
        try:
            access_token = shopify.oauth_access_token()
            self.fail()
        except ShopifyException:
            pass
