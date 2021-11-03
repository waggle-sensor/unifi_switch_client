#!/usr/bin/env python3

import os
import logging
import json
import time

import requests

class UnifySwitchClient(object):
    """ A SUNAPI interface for Hanwha camera

    Keyword Arguments:
    ----------
    `host` -- HTTP endpoint for Hanwha camera device (e.g., http://10.0.0.3)

    `username` -- username used for opening a session

    `password` -- password used for opening a session

    Using Context Manager:
    ---------
    This can be used with Python context manager
    ```python
    with UnifySwitchClient(
            host='http://10.0.0.3',
            username='user',
            password='password') as client:
        print(client.get_mac_table())
        ...
    ```

    Using Class Instance:
    ---------
    ```python
    client = UnifySwitchClient(
        host='http://10.0.0.3',
        username='user',
        password='password')
    client.open()
    print(client.get_mac_table())
    client.close()
    ```
    """
    def __init__(self, host='https://10.31.81.2', username='ubnt', password='password'):
        self.host = host
        self.username = username
        self.password = password

        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
        }

    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def _get_response(self, url, data=None, additional_headers={}):
        headers = self.default_headers.copy()
        headers.update(additional_headers)
        self.session.headers = headers
        logging.debug(f'Requesting {url}')
        logging.debug(f'with headers: {self.session.headers}')
        if data == None:
            res = self.session.get(url)
        else:
            res = self.session.post(url, data=data)
        logging.debug(f'Received return code: {res.status_code}')
        if 'Content-type' in res.headers:
            content_type = res.headers['Content-type']
            logging.debug(f'Content-type {content_type} found')
            body = self._convert_body(content_type, res)
        else:
            body = res.text
        if res.status_code != 200:
            logging.error(f'{body}')
        return res.status_code, res.headers, body

    def _convert_body(self, content_type, response):
        if 'application/json' in content_type:
            return response.json()
        elif 'image/jpeg' in content_type:
            return response.content
        elif 'application/octet-stream' in content_type:
            return response.content
        else:
            response.text

    def get_token(self, username, password):
        """ Returns a token for authentication

        Keyword Arguments:
        --------
        `username` -- username used for authentication

        `password` -- password used for authentication

        Returns:
        --------
        `token` -- token used for querying APIs
        """
        url = os.path.join(self.host, 'api/v1.0/user/login')
        headers = {'Referer': self.host if self.host.endswith('/') else self.host + '/'}
        data = json.dumps({'username': username, 'password': password})
        r_code, r_header, r_body = self._get_response(url, data=data, additional_headers=headers)
        if r_code == 200:
            if r_body['error'] == 0:
                logging.debug(f'token received: {r_header["x-auth-token"]}')
                return True, r_header['x-auth-token']
            else:
                return False, r_body['message']
        else:
            return False, r_code

    def open(self):
        """ Opens a HTTPS session
        """
        self.session = requests.Session()
        # Disabling SSL verification
        self.session.verify = False
        ret, token = self.get_token(self.username, self.password)
        if ret:
            self.default_headers.update({'x-auth-token': token})
        else:
            return Exception(f'Failed to connect to {self.host}: {token}')
        logging.debug('Session open')

    def close(self):
        """ Closes the HTTPS session
        """
        url = os.path.join(self.host, 'api/v1.0/user/logout')
        headers = {'Referer': os.path.join(self.host, 'logout')}
        data=json.dumps({})
        return_code, r_headers, r_body = self._get_response(url, data=data, additional_headers=headers)
        if return_code == 200:
            logging.debug('Session closed')
            return True, r_body
        else:
            return False, r_body['message']

    def get_mac_table(self):
        """ Returns a MAC table

        Returns:
        --------
        `table` -- A JSON of MAC table
        """
        url = os.path.join(self.host, 'api/v1.0/tools/mac-table')
        headers = {'Referer': os.path.join(self.host, 'tools/mac-table')}
        return_code, r_headers, r_body = self._get_response(url, additional_headers=headers)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body['message']

    def ping(self, ip_address, trial=3):
        """ Pings to IP address

        Returns:
        --------
        `success` -- boolean indicating whethere the request succeeded

        `ping` -- result of the ping request; if `success` is False, corresponding error message is contained
        """
        try:
            logging.debug(f'Start pinging to {ip_address}')
            url = os.path.join(self.host, 'api/v1.0/tools/ping/start')
            headers = {'Referer': os.path.join(self.host, 'tools/ping')}
            data = json.dumps({
                "count": trial,
                "interval": 1,
                "packetSize": 56,
                "destination": ip_address
            })
            return_code, r_headers, r_body = self._get_response(url, data=data, additional_headers=headers)
            if return_code == 200:
                time.sleep(trial)
            else:
                raise Exception(f'Could not start ping: {return_code} - {r_body}')
        except Exception as ex:
            logging.debug(f'Failed to ping: {str(ex)}')
            return False, str(ex)
        finally:
            url = os.path.join(self.host, 'api/v1.0/tools/ping/stop')
            headers = {'Referer': os.path.join(self.host, 'tools/ping')}
            data = json.dumps({})
            return_code, r_headers, r_body = self._get_response(url, data=data, additional_headers=headers)
            if return_code == 200:
                url = os.path.join(self.host, 'api/v1.0/tools/ping')
                headers = {'Referer': os.path.join(self.host, 'tools/ping')}
                return_code, r_headers, r_body = self._get_response(url, additional_headers=headers)
                if return_code == 200:
                    return True, r_body
                else:
                    logging.debug(f'Failed to retreive ping result: {return_code} - {r_body}')
                    return False, r_body
            else:
                logging.debug(f'Failed to stop pinging: {return_code} - {r_body}')
                return False, r_body
