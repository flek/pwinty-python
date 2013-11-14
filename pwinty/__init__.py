import requests


class PwintyError(Exception):
    """
    Generic error class for failed Pwinty requests
    """
    pass


class Pwinty(object):
    def __init__(self, merchant_id, apikey, version=None, sandbox=True):
        """
        The core client class for interacting with the Pwinty API.
        @param merchant_id: str, Your Pwinty merchant ID
        @param apikey: str, Your Pwinty API key
        @param version: str, API version to use. Default: v2
        @param sandbox: bool, Whether to use the sandbox.
        """
        if version is None:
            version = 'v2'

        self.api = 'https://{0}.pwinty.com/{1}'.format(
            'sandbox' if sandbox else 'api',
            version,
        )

        self.headers = {
            'X-Pwinty-REST-API-Key': apikey,
            'X-Pwinty-MerchantId': merchant_id,
        }

    def _get_http_method(self, verb):
        """
        Takes an input of "GET", for example, and returns the corresponding
        function from the HTTP library being used.
        @param verb: str, HTTP method to use
        """
        return getattr(requests, verb.lower())

    def _get_error_message(self, response):
        """
        Parse standard error message format for when Pwinty returns errors.
        @param response: requests.Response, The API response
        """
        error = response.json().get('Error')
        if error and 'Message' in error:
            return error.get('Message')
        return 'An unknown error occurred'

    def _call_api(self, method, api, files=None, **kwargs):
        """
        Make a request with the specified method to the specified API endpoint.
        Handles passing authentication and catching generic errors. kwargs are
        passed as parameters with the request.
        @param method: str, The HTTP method to request with
        @param api: str, The path of the API endpoint to request
        @param files: dict, Files to send as multipart/form-data
        """
        action = self._get_http_method(method)
        response = action(
            self.api + api,
            data=kwargs,
            files=files,
            headers=self.headers
        )

        if response.status_code == 401:
            raise PwintyError('Authentication Failed')
        elif response.status_code == 404:
            raise PwintyError('The specified resource could not be found')
        elif response.status_code == 400 or response.status_code >= 500:
            raise PwintyError(self._get_error_message(response))

        return response

    def get_orders(self):
        """
        See: http://pwinty.com/api#OrdersGet
        """
        return self._call_api('GET', '/Orders').json()

    def get_order(self, order_id):
        """
        See: http://pwinty.com/api#OrdersGet
        @param order_id: int|str, The ID of the order to fetch
        """
        return self._call_api('GET', '/Orders/{0}'.format(order_id)).json()

    def create_order(self, **kwargs):
        """
        See: http://pwinty.com/api#OrdersPost
        """
        return self._call_api('POST', '/Orders', **kwargs).json()

    def update_order(self, order_id, **kwargs):
        """
        See: http://pwinty.com/api#OrdersPut
        @param order_id: int|str, The ID of the order to update
        """
        response = self._call_api(
            'PUT', '/Orders/{0}'.format(order_id), **kwargs)

        if response.status_code == 403:
            raise PwintyError('Order submitted and can not be updated')

        return response.json()

    def update_order_status(self, order_id, status):
        """
        See: http://pwinty.com/api#OrdersStatusPost
        @param order_id: int|str, The ID of the order to update
        @param status: str, The status to set (http://pwinty.com/Statuses)
        """
        response = self._call_api(
            'POST', '/Orders/{0}/Status'.format(order_id), status=status)

        if response.status_code == 403:
            raise PwintyError('Can not move to specified status from current')

        return response.json()

    def get_submission_status(self, order_id):
        """
        See: http://pwinty.com/api#OrdersSubmissionStatusGet
        @param order_id: int|str, The ID of the order to update
        """
        return self._call_api(
            'GET', '/Orders/{0}/SubmissionStatus'.format(order_id)).json()

    def get_countries(self):
        """
        See: http://pwinty.com/api#CountriesGet
        """
        return self._call_api('GET', '/Country').json()

    def get_photos(self, order_id):
        """
        See: http://pwinty.com/api#PhotosGet
        @param order_id: str|int, The ID of the order to get photos for
        """
        return self._call_api(
            'GET', '/Orders/{0}/Photos'.format(order_id)).json()

    def get_photo(self, order_id, photo_id):
        """
        See: http://pwinty.com/api#PhotosGetById
        @param order_id: str|int, The ID of the order containing the photo
        @param photo_id: str|int, The ID of the photo to get
        """
        return self._call_api(
            'GET', '/Orders/{0}/Photos/{1}'.format(order_id, photo_id)).json()

    def add_photo(self, order_id, ptype, url=None, copies=None, sizing=None,
                  price_to_user=None, md5hash=None, imgfile=None):
        """
        See: http://pwinty.com/api#PhotosPost
        @param order_id: str|int, The ID of the order to add to
        @param ptype: str, The type to add (http://pwinty.com/PhotoTypes)
        @param url: str, The URL of the image file to add
        @param copies: int, The number of copies to order. Default: 1
        @param sizing: str, See http://pwinty.com/Resizing
        @param price_to_user: int, How much to invoice for
        @param md5hash: str, Hash of the file to check before processing
        @param imgfile: str, The file to upload for the order
        """
        if url is None and imgfile is None:
            raise PwintyError('File or URL for the image is required')
        elif url is not None and imgfile is not None:
            raise PwintyError('Cannot use both a URL and a file')

        files = None
        data = {
            'type': ptype,
            'url': url,
            'copies': copies or 1,
            'sizing': sizing or 'Crop',
            'priceToUser': price_to_user,
            'md5Hash': md5hash,
        }

        if imgfile:
            files = {
                'file': open(imgfile, 'r'),
            }

        response = self._call_api(
            'POST', '/Orders/{0}/Photos'.format(order_id), files=files, **data)

        if response.status_code == 403:
            raise PwintyError('Cannot add photos to this order')

        return response.json()

    def delete_photo(self, order_id, photo_id):
        """
        See: http://pwinty.com/api#PhotosDelete
        @param order_id: str|int, The ID of the order containing the photo
        @param photo_id: str|int, The ID of the photo to delete
        """
        response = self._call_api(
            'DELETE', '/Orders/{0}/Photos/{1}'.format(order_id, photo_id))

        if response.status_code == 403:
            raise PwintyError('Cannot remove photos from this order')

        return response.json()

    def get_catalogue(self, country_code, quality_level):
        """
        See: http://pwinty.com/api#CatalogueGet
        @param country_code: str, The country to get the catalogue for
        @param quality_level: str, The desired quality level
        """
        response = self._call_api(
            'GET', '/Catalogue/{0}/{1}'.format(country_code, quality_level))
        return response.json()
