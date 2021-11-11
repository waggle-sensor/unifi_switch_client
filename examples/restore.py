import logging
from unifi_switch_client import UnifiSwitchClient


def restore():
    """ This example restores configuration to target Unifi switch
    """
    backup_path = f'/tmp/ubnt_edgeswitch_1636649639.tar.gz'
    with UnifiSwitchClient(
        host='https://localhost:8885',
        username='ubnt',
        password='changemetosomething') as client:
        ret, err = client.restore(backup_path)
        if ret:
            logging.info('System configuration successfully restored')
        else:
            logging.error(f'Could not restore system configuration: {err}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    restore()
