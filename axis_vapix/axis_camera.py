import logging

import urllib3
from axis_vapix import vapix_control
from axis_vapix import vapix_config


# Disable the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(filename='vapix.log', filemode='w', level=logging.DEBUG)
logging.info('Started')


class Camera:
    def __init__(self, ip, user, password):
        self.__cam_ip = ip
        self.__cam_user = user
        self.__cam_password = password
        self.cam_url = 'http://' + self.__cam_ip

        self.control = vapix_control.CameraControl(ip, user, password)
        self.config = vapix_config.CameraConfiguration(ip, user, password)

    def get_info(self):
        ip_address = self.config.get_parameters('Network.eth0.IPAddress')
        brand = self.config.get_parameters('Brand')
        fw_version = self.config.get_parameters('Properties.Firmware.Version')

        # format the information
        info = {'ip_address': ip_address.split('=')[1],
                'brand': brand.split('=')[1],
                'fw_version': fw_version.split('=')[1]}
        return info


if __name__ == '__main__':
    ip = '10.0.220.152'
    usr = 'root'
    pwd = 'fruitsalad5671'

    cam = Camera(ip, usr, pwd)
    print(cam.get_info())

    cam.control.continuous_move(zoom=-100)
