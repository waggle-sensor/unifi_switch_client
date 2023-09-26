import os
import logging
import json
from unifi_switch_client import UnifiSwitchClient


def device_info():
    """ This example downloads the current configuration from a Unifi Switch
    """
    password = os.getenv("UNIFI_PASSWORD", "")
    with UnifiSwitchClient(
        host='https://localhost:8885',
        username='ubnt',
        password=password) as client:
        ret, info = client.get_device_info()
        if ret:
            logging.info(json.dumps(info, indent=4))
        else:
            logging.error(f'Could not get system information: {info}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    device_info()
