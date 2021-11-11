import logging
from unifi_switch_client import UnifiSwitchClient


def backup():
    """ This example downloads the current configuration from a Unifi Switch
    """
    backup_dir = f'/tmp/'
    with UnifiSwitchClient(
        host='https://localhost:8885',
        username='ubnt',
        password='changemetosomething') as client:
        ret, err = client.backup(backup_dir)
        if ret:
            logging.info('System configuration successfully backed up')
        else:
            logging.error(f'Could not download system configuration: {err}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    backup()
