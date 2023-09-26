#!/usr/bin/env python3

import json
import logging
import os
import time

import requests

class UnifiOpenException(Exception):
    """Custom exception accepting a dictionary with the connection failure details.

    Attributes:
        reason -- dictionary with the connection failure details
        message -- explanation of the error
    """

    def __init__(self, message, reason=None):
        self.reason = reason
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} [reason: {self.reason}]"


class UnifiSwitchClient(object):
    """Unifi switch client

    Keyword Arguments:
    ----------
    `host` -- HTTPS endpoint for Unifi switch device (e.g., https://10.0.0.3)

    `username` -- username used for opening a session

    `password` -- password used for opening a session

    Using Context Manager:
    ---------
    This can be used with Python context manager
    ```python
    with UnifiSwitchClient(
            host='http://10.0.0.3',
            username='user',
            password='password') as client:
        print(client.get_mac_table())
        ...
    ```

    Using Class Instance:
    ---------
    ```python
    client = UnifiSwitchClient(
        host='http://10.0.0.3',
        username='user',
        password='password')
    client.open()
    print(client.get_mac_table())
    client.close()
    ```
    """

    def __init__(self, host="https://10.31.81.2", username="ubnt", password="password"):
        self.host = host
        self.username = username
        self.password = password

        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def _prep_headers(self, payload={}, additional_headers={}):
        headers = self.default_headers.copy()
        headers.update(additional_headers)
        content_type = payload.get("content_type", "")
        if content_type == "file":
            # When sending files, do not specify Content-Type as it is filled by requests
            headers.pop("Content-Type")
        self.session.headers = headers
        logging.debug(f"with headers: {self.session.headers}")

    def _get_response(self, method_func, url, payload, additional_headers={}):
        self._prep_headers(payload, additional_headers)
        content_type = payload.get("content_type", "")
        _payload = payload.get("payload", "")
        if content_type == "":
            resp = method_func(url)
        elif content_type == "data":
            resp = method_func(url, data=_payload)
        elif content_type == "file":
            resp = method_func(url, files=_payload)
        return resp

    def _parse_response(self, res):
        
        logging.debug(f"Received return code: {res.status_code}")
        logging.debug(f"Received headers: {res.headers}")
        if "Content-type" in res.headers:
            content_type = res.headers["Content-type"]
            logging.debug(f"Content-type {content_type} found")
            body = self._convert_body(content_type, res)
        else:
            body = res.text
        if res.status_code != 200:
            logging.error(f"{body}")
        return res.status_code, res.headers, body

    def _convert_body(self, content_type, response):
        if "application/json" in content_type:
            return response.json()
        elif "image/jpeg" in content_type:
            return response.content
        elif "application/octet-stream" in content_type:
            return response.content
        elif "application/gzip" in content_type:
            return response.content
        else:
            response.text

    def _generate_payload(self, content_type, payload=None):
        return {
            "content_type": content_type,
            "payload": payload,
        }

    def _get(self, url, payload={}, additional_headers={}):
        logging.debug(f"[GET] {url}")
        resp = self._get_response(self.session.get, url, payload, additional_headers)
        return self._parse_response(resp)
    
    def _post(self, url, payload={}, additional_headers={}):
        logging.debug(f"[POST] {url}")
        resp = self._get_response(self.session.post, url, payload, additional_headers)
        return self._parse_response(resp)
    
    def _put(self, url, payload={}, additional_headers={}):
        logging.debug(f"[PUT] {url}")
        resp = self._get_response(self.session.put, url, payload, additional_headers)
        return self._parse_response(resp)

    def get_token(self, username, password):
        """Returns a token for authentication

        Keyword Arguments:
        --------
        `username` -- username used for authentication

        `password` -- password used for authentication

        Returns:
        --------
        `token` -- token used for querying APIs
        """
        url = os.path.join(self.host, "api/v1.0/user/login")
        headers = {"Referer": self.host if self.host.endswith("/") else self.host + "/"}
        payload = self._generate_payload("data", json.dumps({"username": username, "password": password}))
        r_code, r_header, r_body = self._post(url, payload=payload, additional_headers=headers)
        if r_code == 200:
            if r_body["error"] == 0:
                logging.debug(f'token received: {r_header["x-auth-token"]}')
                return True, r_header["x-auth-token"]
            else:
                return False, r_body["message"]
        else:
            return False, r_body

    def open(self):
        """Opens a HTTPS session"""
        self.session = requests.Session()
        # Disabling SSL verification
        self.session.verify = False
        ret, token = self.get_token(self.username, self.password)
        if ret:
            self.default_headers.update({"x-auth-token": token})
        else:
            raise UnifiOpenException(f"Failed to connect to {self.host}", reason=token)
        logging.debug("Session open")

    def close(self):
        """Closes the HTTPS session"""
        url = os.path.join(self.host, "api/v1.0/user/logout")
        headers = {"Referer": os.path.join(self.host, "logout")}
        payload = self._generate_payload("data", json.dumps({}))
        return_code, r_headers, r_body = self._post(
            url, payload=payload, additional_headers=headers
        )
        if return_code == 200:
            logging.debug("Session closed")
            return True, r_body
        else:
            return False, r_body

    def get_device_info(self):
        """Returns device information from Unifi switch

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeeded

        `device_info` -- response of the request
        """
        logging.debug("Getting device information...")
        url = os.path.join(self.host, "api/v1.0/device")
        headers = {"Referer": self.host if self.host.endswith("/") else self.host + "/"}
        return_code, r_headers, r_body = self._get(url, additional_headers=headers)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body

    def change_password(self, old_password, new_password, user="ubnt"):
        """Changes password of ubnt account

        Keyword Arguments:
        --------
        `old_password` -- the old password

        `new_password` -- new password; should be longer than 8 characters

        `user` -- user account; default to ubnt

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeeded

        `message` -- response of the request
        """
        payload = self._generate_payload("data", json.dumps(
            {"username": user, "oldPassword": old_password, "newPassword": new_password}
        ))
        url = os.path.join(self.host, "api/v1.0/user/change-password")
        headers = {"Referer": self.host if self.host.endswith("/") else self.host + "/"}
        return_code, r_headers, r_body = self._post(
            url, payload=payload, additional_headers=headers
        )
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body

    def get_mac_table(self):
        """Returns a MAC table

        Returns:
        --------
        `table` -- A JSON of MAC table
        """
        url = os.path.join(self.host, "api/v1.0/tools/mac-table")
        headers = {"Referer": os.path.join(self.host, "tools/mac-table")}
        return_code, r_headers, r_body = self._get(url, additional_headers=headers)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body["message"]

    def ping(self, ip_address, trial=3):
        """Pings to IP address

        Returns:
        --------
        `success` -- boolean indicating whethere the request succeeded

        `ping` -- result of the ping request; if `success` is False, corresponding error message is contained
        """
        try:
            logging.debug(f"Start pinging to {ip_address}")
            url = os.path.join(self.host, "api/v1.0/tools/ping/start")
            headers = {"Referer": os.path.join(self.host, "tools/ping")}
            payload = self._generate_payload("data", json.dumps(
                {"count": trial, "interval": 1, "packetSize": 56, "destination": ip_address}
            ))
            return_code, r_headers, r_body = self._post(
                url, payload=payload, additional_headers=headers
            )
            if return_code == 200:
                time.sleep(trial)
            else:
                raise Exception(f"Could not start ping: {return_code} - {r_body}")
        except Exception as ex:
            logging.debug(f"Failed to ping: {str(ex)}")
            return False, str(ex)
        finally:
            url = os.path.join(self.host, "api/v1.0/tools/ping/stop")
            headers = {"Referer": os.path.join(self.host, "tools/ping")}
            payload = self._generate_payload("data", json.dumps({}))
            return_code, r_headers, r_body = self._post(
                url, payload=payload, additional_headers=headers
            )
            if return_code == 200:
                url = os.path.join(self.host, "api/v1.0/tools/ping")
                headers = {"Referer": os.path.join(self.host, "tools/ping")}
                return_code, r_headers, r_body = self._get(url, additional_headers=headers)
                if return_code == 200:
                    return True, r_body
                else:
                    logging.debug(f"Failed to retreive ping result: {return_code} - {r_body}")
                    return False, r_body
            else:
                logging.debug(f"Failed to stop pinging: {return_code} - {r_body}")
                return False, r_body

    def reboot_system(self):
        """Reboots the switch

        Returns:
        --------
        `success` -- boolean indicating whethere the request succeeded

        `message` -- detailed message about the request
        """
        logging.debug("Rebooting the switch...")
        url = os.path.join(self.host, "api/v1.0/system/reboot")
        headers = {"Referer": os.path.join(self.host, "settings")}
        payload = self._generate_payload("data", json.dumps({}))
        return_code, r_headers, r_body = self._get(
            url, payload=payload, additional_headers=headers
        )
        if return_code == 200:
            if r_body["statusCode"] == 200:
                return True, r_body
            else:
                return False, r_body["detail"]
        else:
            return False, r_body["message"]

    def upgrade_firmware(self, firmware_path):
        """Upgrades the switch with given firmware

        Keyword Arguments:
        --------
        `firmware_path` -- a path to the firmware file

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `message` -- detailed message about the request
        """
        logging.debug("Upgrading firmware...")
        url = os.path.join(self.host, "api/v1.0/system/upgrade/direct")
        headers = {"Referer": os.path.join(self.host, "settings")}
        filename = os.path.basename(firmware_path)
        payload = self._generate_payload("file", {"file": (filename, open(firmware_path, "rb"), "application/octet-stream")})
        return_code, r_headers, r_body = self._post(
            url, payload=payload, additional_headers=headers
        )
        if return_code != 200:
            return False, r_body
        if r_body["statusCode"] != 200:
            return False, r_body["detail"]
        else:
            logging.debug("Firmware transfer succeded")

        logging.debug("Waiting for the upgrade to be done...")
        url = os.path.join(self.host, "api/v1.0/system/upgrade")
        headers = {"Referer": os.path.join(self.host, "settings")}
        retry = 0
        while retry < 5:
            return_code, r_headers, r_body = self._get(url, additional_headers=headers)
            if return_code == 200:
                if "in_progress" in r_body["status"]:
                    logging.debug(
                        f'Upgrading in progress. Progress percentage: {r_body["progressPercent"]}'
                    )
                if "finished" in r_body["status"]:
                    logging.debug(
                        f"Firmware upgrade successfully finished. You may reboot the switch."
                    )
                    return True, r_body
            else:
                logging.debug(
                    f"Failed to retreive status of the firmware upgrade. Retry count: {retry}"
                )
                retry += 1
            time.sleep(2)
        logging.error(f"Failed to upgrade firmware: Reached retry {retry} times.")
        return False, None

    def backup(self, backup_dir):
        """Backs up the system using given backup path

        Keyword Arguments:
        --------
        `backup_dir` -- a directory where system backup file will be stored

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `message` -- detailed message about the request
        """
        logging.debug("Backing up the switch...")
        url = os.path.join(self.host, "api/v1.0/system/backup")
        headers = {"Referer": os.path.join(self.host, "settings")}
        return_code, r_headers, r_body = self._get(url, additional_headers=headers)
        if return_code == 200:
            if "Content-type" in r_headers and "application/gzip" in r_headers["Content-type"]:
                filename = f"ubnt_edgeswitch_{int(time.time())}.tar.gz"
            else:
                filename = f"ubnt_edgeswitch_{int(time.time())}"
            with open(os.path.join(backup_dir, filename), "wb") as file:
                file.write(r_body)
            return True, None
        else:
            return False, r_body

    def restore(self, backup_file):
        """Restores the system with given backup file

        Keyword Arguments:
        --------
        `backup_file` -- a gz file of system configuration

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `message` -- detailed message about the request
        """
        logging.debug(f"Restoring the switch using {backup_file}...")
        url = os.path.join(self.host, "api/v1.0/system/backup/restore/direct")
        headers = {"Referer": os.path.join(self.host, "settings")}
        filename = os.path.basename(backup_file)
        payload = self._generate_payload("file", {"file": (filename, open(backup_file, "rb"), "application/x-gzip")})
        return_code, r_headers, r_body = self._post(
            url, payload=payload, additional_headers=headers
        )
        if return_code != 200:
            return False, r_body
        if r_body["statusCode"] != 200:
            return False, r_body["detail"]
        else:
            logging.debug(f"{backup_file} transfer succeded")
        logging.debug("Waiting for the restore to be done...")
        url = os.path.join(self.host, "api/v1.0/system/backup/restore")
        headers = {"Referer": os.path.join(self.host, "settings")}
        retry = 0
        while retry < 5:
            return_code, r_headers, r_body = self._get(url, additional_headers=headers)
            if return_code == 200:
                if "in_progress" in r_body["status"]:
                    logging.debug("Restoring in progress...")
                if "finished" in r_body["status"]:
                    logging.debug(f"Restore is complete")
                    return True, r_body
            else:
                logging.debug(f"Failed to retreive status of the restore. Retry count: {retry}")
                retry += 1
            time.sleep(2)
        logging.error(f"Failed to restore configuration: Reached retry {retry} times.")

    def get_ports_profile(self):
        """Returns port configuration

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `list` -- list of dicts representing each port
        """
        logging.debug(f"Querying port information...")
        url = os.path.join(self.host, "api/v1.0/interfaces")
        return_code, r_headers, r_body = self._get(url)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body["message"]
        
    def set_ports_profile(self, profiles):
        """Puts port configuration in Switch

        Keyword Arguments:
        --------
        `profiles` -- a list of dict for each port configuration to set

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `message` -- detailed message about the request
        """
        logging.debug(f"Pushing port configuration to switch...")
        url = os.path.join(self.host, "api/v1.0/interfaces")
        payload = self._generate_payload("data", json.dumps(profiles))
        return_code, r_headers, r_body = self._put(url, payload=payload)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body["message"]
    
    def get_stat(self):
        """Returns statistics for system and ports

        Returns:
        --------
        `success` -- a boolean indicating whether the request succeded

        `dict` -- dict representing statistics on the system and each port
        """
        logging.debug(f"Querying statistics information...")
        url = os.path.join(self.host, "api/v1.0/statistics")
        return_code, r_headers, r_body = self._get(url)
        if return_code == 200:
            return True, r_body
        else:
            return False, r_body["message"]