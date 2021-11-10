import logging
from unifi_switch_client import UnifiSwitchClient


def configure():
    """ This example configures a Unifi Switch

    Target firmware should be already downloaded at /tmp/ESWH.v1.9.2.5322630.stk
    """
    firmware_path = '/tmp/ESWH.v1.9.2.5322630.stk'
    with UnifiSwitchClient(
        host='https://localhost:8885',
        username='ubnt',
        password='ubnt') as client:
        ret, err = client.change_password(old_password='ubnt', new_password='changemetosomething')
        if ret:
            logging.info('Password successfully changed')
        else:
            logging.error(f'Could not set password: {err}')

        ret, err = client.upgrade_firmware(firmware_path)
        if ret:
            logging.info('Firmware upgraded successfully')
        else:
            logging.error(f'Could not upgrade firmware: {err}')
        ret, err = client.reboot_system()
        if ret:
            logging.info('The switch is rebooted.')
        else:
            logging.error(f'Could not reboot the switch: {err}')

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    configure()
