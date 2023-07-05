import sys
import time
import datetime
import logging

import urllib3
import urllib.parse
import requests
from requests.auth import HTTPDigestAuth
from bs4 import BeautifulSoup

# pylint: disable=R0904
# pylint: disable=R0914

# Disable the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logger
_log = logging.getLogger(__name__)

class Camera:
    def __init__(self, ip, user, password):
        self.__cam_ip = ip
        self.__cam_user = user
        self.__cam_password = password
        self.cam_url = 'http://' + self.__cam_ip

    def get_info(self):
        text = 'Camera Info:\n'
        text += f'  Camera Model: {self.get_parameters("Brand.ProdFullName", only_value=True)}'
        text += f'  Serial: {self.get_parameters("Properties.System.SerialNumber", only_value=True)}'
        text += f'  Firmware: {self.get_parameters("Properties.Firmware.Version", only_value=True)}'

        text += 'Network Info:\n'
        text += f'  IP: {self.get_parameters("Network.eth0.IPAddress", only_value=True)}'
        text += f'  MAC: {self.get_parameters("Network.eth0.MACAddress", only_value=True)}'

        text += 'Video Info:\n'
        text += f'  Resolutions: {self.get_parameters("Image.I0.Appearance.Resolution", only_value=True)}'
        text += f'  Compression Level: {self.get_parameters("Image.I0.Appearance.Compression", only_value=True)}'
        text += f'  FPS: {self.get_parameters("Image.I0.Stream.FPS", only_value=True)}'

        text += 'Camera Status:\n'
        status = cam.get_status()
        for key in status.keys():
            text += f'  {key[0].upper() + key[1:]}: {status[key]}\n'

        return text

    @staticmethod
    def __merge_dicts(*dict_args) -> dict:
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts

        Args:
            *dict_args: argument dictionary

        Returns:
            Return a merged dictionary
        """
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    def _command(self, url: str, payload: dict = None):
        """
        Function used to send commands to the camera
        Args:
            url: url for the camera
            payload: arguments dictionary

        Returns:
            Returns the response from the device to the command sent

        """
        resp = requests.get(url, auth=HTTPDigestAuth(self.__cam_user, self.__cam_password),
                            params=payload, verify=False)

        if (resp.status_code != 200) and (resp.status_code != 204):
            soup = BeautifulSoup(resp.text, features="lxml")
            logging.error('%s', soup.get_text())
            if resp.status_code == 401:
                sys.exit(1)

        return resp

    def get_parameters(self, group=None, only_value=False):
        """
        Get parameters from camera

        Args:
            group (str): group of parameters
            only_value (bool): return only value

        Returns:
            dict: parameters

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi?action=list'
        if group is not None:
            url += '&group=' + group

        resp = self._command(url)

        if resp.status_code == 200:
            if only_value:
                try:
                    return resp.text.split('=')[1].replace('\r', '')
                except IndexError:
                    return resp.text
            else:
                return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_camera_info(self):
        """
        Request type camera.

        Returns:
            return type camera, Network camera or ptz camera

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi?action=list&group=Brand.ProdType'
        resp = self._command(url)

        if resp.status_code == 200:
            vector = resp.text.split('=')
            return vector[1].replace('\r', '')
        else:
            return str(resp) + str(resp.text)

    def factory_reset_default(self):  # 5.1.3
        """
        Reload factory default. All parameters except Network.BootProto, Network.IPAddress,
        Network. SubnetMask, Network.Broadcast and Network.DefaultRouter are set to their factory
        default values.

        Returns:
            Success (OK) or Failure (Settings or syntax are probably incorrect).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/factorydefault.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def hard_factory_reset_default(self):  # 5.1.4
        """
        Reload factory default. All parameters are set to their factory default value.

        Returns:
            Success (OK) or Failure (error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/hardfactorydefault.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def restart_server(self):  # 5.1.6
        """
        Restart server.

        Returns:
            Success (OK) or Failure (error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/restart.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_server_report(self):  # 5.1.7
        """
        This CGI request generates and returns a server report. This report is useful as an
        input when requesting support. The report includes product information, parameter
        settings and system logs.

        Returns:
            Success (OK and server report content text) or Failure (error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/serverreport.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_system_log(self):  # 5.1.8.1
        """
        Retrieve system log information. The level of information included in the log is set
        in the Log. System parameter group.

        Returns:
            Success (OK and system log content text) or Failure (error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/systemlog.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_system_access_log(self):  # 5.1.8.2
        """
        Retrieve client access log information. The level of information included in the log
        is set in the Log.Access parameter group.

        Returns:
            Success (OK and access log content text) or Failure (error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/accesslog.cgi'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_date_and_time(self):  # 5.1.9.1
        """
        Get the system date and time.

        Returns:
            Success (OK and time and date content text) or Failure (error and description).
                example: <month> <day>, <year> <hour>:<minute>:<second>
                Error example: Request failed: <error message>

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/date.cgi?action=get'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_date(self, year_date: int = None, month_date: int = None,
                 day_date: int = None):  # 5.1.9.2
        """
        Change the system date.

        Args:
            year_date: current year.
            month_date: current month.
            day_date: current day.

        Returns:
            Success (OK) or Failure (Request failed: <error message>).

        """
        payload = {
            'action': 'set',
            'year': year_date,
            'month': month_date,
            'day': day_date
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/date.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_time(self, hour: int = None, minute: int = None, second: int = None,
                 timezone: str = None):  # 5.1.9.2
        """
        Change the system time.

        Args:
            hour: current hour.
            minute: current minute.
            second: current second.
            timezone: specifies the time zone that the new date and/or time is given in. The camera
            translates the time into local time using whichever time zone has been specified through
            the web configuration.

        Returns:
            Success (OK) or Failure (Request failed: <error message>).

        """
        payload = {
            'action': 'set',
            'hour': hour,
            'minute': minute,
            'second': second,
            'timezone': timezone
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/date.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_image_size(self):  # 5.2.1
        """
        Retrieve the actual image size with default image settings or with given parameters.

        Returns:
            Success (OK and image size content text) or Failure (Error and description).
                example:
                    image width = <value>
                    image height = <value>
        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/imagesize.cgi?camera=1'
        resp = self._command(url)

        if resp.status_code == 200:
            # vector = resp.text.split()
            # print(vector[3], 'x', vector[7])
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_video_status(self, camera_status: int = None):  # 5.2.2
        """
        Video encoders only. Check the status of one or more video sources.

        Args:
            camera_status: video source

        Returns:
            Success (OK and video status content text) or Failure (Error and description).
            example:
                Video 1 = <information>
        """
        payload = {
            'status': camera_status
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/videostatus.cgi?'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def get_bitmap_request(self, resolution: str = None, camera: str = None,
                           square_pixel: int = None):  # 5.2.3.1
        """
        Request a bitmap image.

        Args:
            resolution: resolution of the returned image. Check the product’s Release notes for
            supported resolutions.
            camera: select a video source or the quad stream.
            square_pixel: enable/disable square pixel correction. Applies only to video encoders.

        Returns:
            Success ('image save' and save the image in the file folder) or Failure (Error and
            description).

        """
        payload = {
            'resolution': resolution,
            'camera': camera,
            'square_pixel': square_pixel
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/bitmap/image.bmp'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            now = datetime.datetime.now()
            with open(str(now.strftime("%d-%m-%Y_%Hh%Mm%Ss")) + ".bmp", 'wb') as var:
                var.write(resp.content)
            return str('Image saved')
        else:
            return str(resp) + str(resp.text)

    def get_jpeg_request(self, resolution: str = None, camera: str = None,
                         square_pixel: int = None, compression: int = None,
                         clock: int = None, date: int = None, text: int = None,
                         text_string: str = None, text_color: str = None,
                         text_background_color: str = None, rotation: int = None,
                         text_position: str = None, overlay_image: int = None,
                         overlay_position: str = None):  # 5.2.4.1
        """
        The requests specified in the JPEG/MJPG section are supported by those video products
        that use JPEG and MJPG encoding.

        Args:
            resolution: Resolution of the returned image. Check the product’s Release notes.
            camera: Selects the source camera or the quad stream.
            square_pixel: Enable/disable square pixel correction. Applies only to video encoders.
            compression: Adjusts the compression level of the image.
            clock: Shows/hides the time stamp. (0 = hide, 1 = show)
            date: Shows/hides the date. (0 = hide, 1 = show)
            text: Shows/hides the text. (0 = hide, 1 = show)
            text_string: The text shown in the image, the string must be URL encoded.
            text_color: The color of the text shown in the image. (black, white)
            text_background_color: The color of the text background shown in the image.
            (black, white, transparent, semitransparent)
            rotation: Rotate the image clockwise.
            text_position: The position of the string shown in the image. (top, bottom)
            overlay_image: Enable/disable overlay image.(0 = disable, 1 = enable)
            overlay_position:The x and y coordinates defining the position of the overlay image.
            (<int>x<int>)

        Returns:
            Success ('image save' and save the image in the file folder) or Failure (Error and
            description).

        """
        payload = {
            'resolution': resolution,
            'camera': camera,
            'square_pixel': square_pixel,
            'compression': compression,
            'clock': clock,
            'date': date,
            'text': text,
            'text_string': text_string,
            'text_color': text_color,
            'text_background_color': text_background_color,
            'rotation': rotation,
            'text_position': text_position,
            'overlay_image': overlay_image,
            'overlay_position': overlay_position
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/jpg/image.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            now = datetime.datetime.now()
            with open(str(now.strftime("%d-%m-%Y_%Hh%Mm%Ss")) + ".jpg", 'wb') as var:
                var.write(resp.content)
            return str('Image saved')
        else:
            return str(resp) + str(resp.text)

    def get_dynamic_text_overlay(self):  # 5.2.5.1
        """
        Get dynamic text overlay in the image.

        Returns:
            Success (dynamic text overlay) or Failure (Error and description).

        """
        url = 'http://' + self.__cam_ip + '/axis-cgi/dynamicoverlay.cgi?action=gettext'
        resp = self._command(url)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_dynamic_text_overlay(self, text: str = None, camera: str = None):  # 5.2.5.1
        """
        Set dynamic text overlay in the image.

        Args:
            text: text to set overlay
            camera: select video source or the quad stream. ( default: default camera)

        Returns:
            OK if the camera set text overlay or error and description

        """
        payload = {
            'action': 'settext',
            'text': text,
            'camera': camera
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/dynamicoverlay.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def check_profile(self, name: str = None):  # 0
        """
        Check if the profile exists

        Args:
            name: profile name

        Returns:
            Return 1 or 0

        """
        payload = {
            'action': 'list',
            'group': 'root.StreamProfile'
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        text2 = resp.text.split('\n')
        if resp.status_code == 200:
            for i, _ in enumerate(text2):
                text3 = text2[i].split('Name=')
                if len(text3) > 1 and text3[1] == name:
                    return 1
            return 0
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def create_profile(self, name: str, *, resolution: str = None, video_codec: str = None,
                       fps: int = None, compression: int = None, h264_profile: str = None,
                       gop: int = None, bitrate: int = None, bitrate_priority: str = None):
        """
        Create stream profile.

        Args:
            name: profile name (str)
            resolution: resolution. (str : "1920x1080")
            video_codec: video codec. (str : "h264")
            fps: frame rate.
            compression: axis compression.
            h264_profile: profile h264. (str: "high")
            gop: Group of pictures.
            bitrate: video bitrate.
            bitrate_priority: video bitrate priority.

        Returns:
            Profile code and OK if the profile create or error and description.

        """
        if self.check_profile(name):
            return name + ' already exists. Remove the previous profile or change the name of ' \
                          'the profile to be created.'

        params = {
            'resolution': resolution,
            'videocodec': video_codec,
            'fps': fps,
            'compression': compression,
            'h264profile': h264_profile,
            'videokeyframeinterval': gop,
            'videobitrate': bitrate,
            'videobitratepriority': bitrate_priority
        }

        params_filtred = {key: value for (key, value) in params.items() if value is not None}
        text_params = urllib.parse.urlencode(params_filtred)
        payload = {
            'action': 'add',
            'template': 'streamprofile',
            'group': 'StreamProfile',
            'StreamProfile.S.Name': name,
            'StreamProfile.S.Parameters': text_params
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        soup = BeautifulSoup(resp.text, features="lxml")
        if resp.status_code == 200:
            return soup.body.get_text()
        else:
            return str(resp) + str(soup.get_text())

    def create_user(self, user: str, password: str, sgroup: str, *, group: str = 'users', comment: str = None):
        # 5.1.2
        """
        Create user.

        Args:
            user: user name
            password: password
            group: An existing primary group name of the account.
            sgroup: security group (admin, operator, viewer)
            comment: user description

        Returns:
            Success (Created account <account name>) or Failure (Error and description).

        """
        if self.check_user(user):
            return user + ' already exists.'

        if sgroup == 'admin':
            sgroup = 'admin:operator:viewer:ptz'
        elif sgroup == 'operator':
            sgroup = 'operator:viewer:ptz'
        elif sgroup == 'ptz':
            sgroup = 'viewer:ptz'

        payload = {
            'action': 'add',
            'user': user,
            'pwd': password,
            'grp': group,
            'sgrp': sgroup,
            'comment': comment
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/pwdgrp.cgi'
        resp = self._command(url, payload)

        soup = BeautifulSoup(resp.text, features="lxml")
        if resp.status_code == 200:
            return soup.body.get_text()
        else:
            return str(resp) + str(soup.get_text())

    def update_user(self, user: str, *, password: str = None, group: str = 'users',
                    sgroup: str = None, comment: str = None):  # 5.1.2
        """
        Update user params.

        Args:
            user: user name
            password: new password or current password to change others params.
            group: An existing primary group name of the account.
            sgroup: security group. (admin, operator, viewer)
            comment: user description.

        Returns:
            Success (OK) or Failure (Error and description).

        """
        if not self.check_user(user):
            return user + ' does not exists.'

        if sgroup == 'admin':
            sgroup = 'admin:operator:viewer:ptz'
        elif sgroup == 'operator':
            sgroup = 'operator:viewer:ptz'
        elif sgroup == 'ptz':
            sgroup = 'viewer:ptz'

        payload = {
            'action': 'update',
            'user': user,
            'pwd': password,
            'grp': group,
            'sgrp': sgroup,
            'comment': comment
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/pwdgrp.cgi'
        resp = self._command(url, payload)

        soup = BeautifulSoup(resp.text, features="lxml")
        if resp.status_code == 200:
            return soup.body.get_text()
        else:
            return str(resp) + str(soup.get_text())

    def remove_user(self, user: str):  # 5.1.2
        """
        Remove user.
        Args:
            user:  user name

        Returns:
            Success (OK) or Failure (Error and description).
        """
        if not self.check_user(user):
            return user + 'does not exists.'

        payload = {
            'action': 'remove',
            'user': user
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/pwdgrp.cgi'
        resp = self._command(url, payload)

        soup = BeautifulSoup(resp.text, features="lxml")
        if resp.status_code == 200:
            return soup.body.get_text()
        else:
            return str(resp) + str(soup.get_text())

    def check_user(self, name: str):  # 0
        """
        Check if user exists
        Args:
            name: user name

        Returns:
            Success (0 = doesn't exist, 1 exist) or Failure (Error and description).
        """
        payload = {
            'action': 'get'
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/pwdgrp.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            text2 = resp.text.split('\n')
            for i, _ in enumerate(text2):  # for i in range(len(text2)):
                text3 = text2[i].split('users=')
                if len(text3) > 1:
                    text4 = text3[1].replace('"', '').replace('\r', '').split(',')
                    for j, _ in enumerate(text4):
                        if text4[j] == name:
                            return 1
            return 0
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_hostname(self, hostname: str = None, *, set_dhcp: str = None):  # 0
        """
        Configure how the device selects a hostname, with the possibility to set a static hostname and/or enable
        auto-configuration by DHCP.

        Args:
            hostname: hostname
            set_dhcp: auto-configuration by DHCP. (yes, no)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'Network.HostName': hostname,
            'Network.VolatileHostName.ObtainFromDHCP': set_dhcp
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_stabilizer(self, stabilizer: str = None, *, stabilizer_margin: int = None):  # 0
        """
        Set electronic image stabilization (EIS).

        Args:
            stabilizer: stabilizer value ("on" or "off")
            stabilizer_margin: stabilization margin (0 to 200)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.Stabilizer': stabilizer,
            'ImageSource.I0.Sensor.StabilizerMargin': stabilizer_margin  # 0 a 200
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_capture_mode(self, capture_mode: str = None):
        """
        Set capture mode.

        Args:
            capture_mode: capture mode. (1 = 1080, 2 = 720 - camera Full HD)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor': capture_mode
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_wdr(self, wdr: str = None, *, contrast: int = None):
        """
        WDR - Forensic Capture - Wide Dynamic Range can improve the exposure when there is a
        considerable contrast between light and dark areas in an image.
        Args:
            wdr: WDR value (on, off)
            contrast: contrast level.

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.WDR': wdr,
            'ImageSource.I0.Sensor.LocalContrast': contrast
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_appearance(self, *, brightness: int = None, contrast: int = None,
                       saturation: int = None, sharpness: int = None):
        """
        Image Appearance Setting.

        Args:
            brightness: adjusts the image brightness.
            contrast: adjusts the image's contrast.
            saturation: adjusts color saturation. (Color level)
            sharpness: controls the amount of sharpening applied to the image.

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.Brightness': brightness,
            'ImageSource.I0.Sensor.ColorLevel': saturation,
            'ImageSource.I0.Sensor.Sharpness': sharpness,
            'ImageSource.I0.Sensor.Contrast': contrast
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            soup = BeautifulSoup(resp.text, features="lxml")
            return str(resp) + str(soup.get_text())

    def set_ir_cut_filter(self, ir_cut: str = None, *, shift_level: int = None):
        """
        IR cut filter settings.

        Args:
            ir_cut: IR value. (Off to allow the camera to 'see' infrared light, set to On during
            daylight or bright light conditions to cut out infrared light, Automatic the camera will
            automatically switch between On and Off, according to the current lighting conditions)
            shift_level: This setting can be used to change when the camera shifts into night mode.

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.DayNight.IrCutFilter': ir_cut,
            'ImageSource.I0.DayNight.ShiftLevel': shift_level
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = requests.get(url, auth=HTTPDigestAuth(self.__cam_user, self.__cam_password), params=payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    # "flickerfree60" "flickerfree50" "flickerreduced60" "flickerreduced50" "auto" "hold"
    # "auto" "center" "spot"(pontual) "upper" "lower" "left" "right" "custom"
    def set_exposure(self, *, exposure: str = None, exposure_window: str = None,
                     max_exposure_time: int = None,
                     max_gain: int = None, exposure_priority_normal: int = None,
                     lock_aperture: str = None, exposure_value: int = None):
        """
        Exposure Settings.

        Args:
            exposure: exposure  mode. (flickerfree60, flickerfree50, flickerreduced60,
            flickerreduced50, auto, hold)
            exposure_window: This setting determines which part of the image will be used to
            calculate the exposure. (auto, center, spot, upper, lower, left, right, custom)
            max_exposure_time: maximum shutter time (MS)
            max_gain: maximum gain
            exposure_priority_normal: commitment blur / noise
            lock_aperture: lock the shutter aperture
            exposure_value: exposure level

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.Exposure': exposure,  # modo de exposição (exposure)
            'ImageSource.I0.Sensor.ExposureWindow': exposure_window,  # zona de exposição
            'ImageSource.I0.Sensor.MaxExposureTime': max_exposure_time,  # Obturador maximo em MS
            'ImageSource.I0.Sensor.MaxGain': max_gain,  # ganho maximo
            'ImageSource.I0.Sensor.ExposurePriorityNormal': exposure_priority_normal,
            # compromisso desfoque/ruido
            'ImageSource.I0.DCIris.Enable': lock_aperture,  # travar abertura - yes or no
            'ImageSource.I0.Sensor.ExposureValue': exposure_value  # nivel de exposição
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_custom_exposure_window(self, top: int = None, bottom: int = None, left: int = None,
                                   right: int = None):
        """
        Set custom exposition zone.

        Args:
            top: upper limit
            bottom: lower limit
            left: left limit
            right: right limit

        Returns:
            Success (OK) or Failure (Error and description).

        """
        # pass as pixel update to values 0 to 9999
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.CustomExposureWindow.C0.Top': top,
            'ImageSource.I0.Sensor.CustomExposureWindow.C0.Bottom': bottom,
            'ImageSource.I0.Sensor.CustomExposureWindow.C0.Left': left,
            'ImageSource.I0.Sensor.CustomExposureWindow.C0.Right': right
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_backlight(self, backlight: str = None):
        """
        Backlight compensation makes the subject appear clearer when the image background is too
        bright, or the subject is too dark.

        Args:
            backlight: backlight value. (true, false)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'PTZ.Various.V1.BackLight': backlight,

        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_highlight(self, highlight: int = None):
        """
        The Axis product will detect a bright light from a source such as a torch or car headlights
        and mask that image area. This setting is useful when the camera operates in a very dark
        area where a bright light may overexpose part of the image and prevent the operator from
        seeing other parts of the scene.

        Args:
            highlight: highlight value. (0, 1)

        Returns:
            Success (OK) or Failure (Error and description).
        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.HLCSensitivity': highlight,

        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_image_setings(self, *, defog: str = None, noise_reduction: str = None,
                          noise_reduction_tuning: int = None, image_freeze_ptz: str = None):
        """
        Image Settings.

        Args:
            defog: detect the fog effect and automatically remove it to get a clear image. (on, off)
            noise_reduction: noise reduction function (on, off)
            noise_reduction_tuning: Noise Reduction Adjustment level (0 to 100)
            image_freeze_ptz: freeze the image while the camera is moving during a pan, tilt or zoom
            operation. (on, off)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'ImageSource.I0.Sensor.Defog': defog,
            'ImageSource.I0.Sensor.NoiseReduction': noise_reduction,
            'ImageSource.I0.Sensor.NoiseReductionTuning': noise_reduction_tuning,
            'PTZ.UserAdv.U1.ImageFreeze': image_freeze_ptz
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_ntp_server(self, ntp_server: str = None):
        """
            Configure NTP server.
        Args:
            ntp_server: link or IP server

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'Time.NTP.Server': ntp_server,
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def set_pan_tilt_zoom_enable(self, *, pan_enable: str = None, tilt_enable: str = None,
                                 zoom_enable: str = None):
        """
            Turns PTZ control on and off.

        Args:
            pan_enable: pan enabled value (true, false)
            tilt_enable: tilt enabled value (true, false)
            zoom_enable: zoom enabled value (true, false)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'action': 'update',
            'PTZ.Various.V1.PanEnabled': pan_enable,
            'PTZ.Various.V1.TiltEnabled': tilt_enable,
            'PTZ.Various.V1.ZoomEnabled': zoom_enable
        }
        url = 'http://' + self.__cam_ip + '/axis-cgi/param.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def auto_focus(self, focus: str = None):  # on or off
        """
        Enable or disable automatic focus

        Args:
            focus: focus value (on, off)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'autofocus': focus
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/com/ptz.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    def auto_iris(self, iris: str = None):
        """
        Enable or disable automatic iris control

        Args:
            iris: iris value (on, off)

        Returns:
            Success (OK) or Failure (Error and description).

        """
        payload = {
            'autoiris': iris
        }

        url = 'http://' + self.__cam_ip + '/axis-cgi/com/ptz.cgi'
        resp = self._command(url, payload)

        if resp.status_code == 200:
            return resp.text
        else:
            return str(resp) + str(resp.text)

    # CAMERA CONTROL #
    def _ptz_command(self, payload: dict):
        """
        Function used to send ptz commands to the camera
        Args:
            payload: argument dictionary for camera control

        Returns:
            Returns the response from the device to the command sent

        """
        logging.info('camera_command(%s)', payload)

        base_q_args = {
            'camera': 1,
            'html': 'no',
            'timestamp': int(time.time())
        }

        merged_args = self.__merge_dicts(payload, base_q_args)
        url = 'http://' + self.__cam_ip + '/axis-cgi/com/ptz.cgi'

        return self._command(url, merged_args)

    def absolute_move(self, pan: float = None, tilt: float = None, zoom: int = None,
                      speed: int = None):
        """
        Operation to move pan, tilt or zoom to a absolute destination.

        Args:
            pan: pans the device relative to the (0,0) position.
            tilt: tilts the device relative to the (0,0) position.
            zoom: zooms the device n steps.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent.

        """
        return self._ptz_command({'pan': pan, 'tilt': tilt, 'zoom': zoom, 'speed': speed})

    def continuous_move(self, pan: int = None, tilt: int = None, zoom: int = None):
        """
        Operation for continuous Pan/Tilt and Zoom movements.

        Args:
            pan: speed of movement of Pan.
            tilt: speed of movement of Tilt.
            zoom: speed of movement of Zoom.

        Returns:
            Returns the response from the device to the command sent.

        """
        pan_tilt = str(pan) + "," + str(tilt)
        return self._ptz_command({'continuouspantiltmove': pan_tilt, 'continuouszoommove': zoom})

    def relative_move(self, pan: float = None, tilt: float = None, zoom: int = None,
                      speed: int = None):
        """
        Operation for Relative Pan/Tilt and Zoom Move.

        Args:
            pan: pans the device n degrees relative to the current position.
            tilt: tilts the device n degrees relative to the current position.
            zoom: zooms the device n steps relative to the current position.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent.

        """
        return self._ptz_command({'rpan': pan, 'rtilt': tilt, 'rzoom': zoom, 'speed': speed})

    def stop_move(self):
        """
        Operation to stop ongoing pan, tilt and zoom movements of absolute relative and
        continuous type

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'continuouspantiltmove': '0,0', 'continuouszoommove': 0})

    def center_move(self, pos_x: int = None, pos_y: int = None, speed: int = None):
        """
        Used to send the coordinates for the point in the image where the user clicked. This
        information is then used by the server to calculate the pan/tilt move required to
        (approximately) center the clicked point.

        Args:
            pos_x: value of the X coordinate.
            pos_y: value of the Y coordinate.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        pan_tilt = str(pos_x) + "," + str(pos_y)
        return self._ptz_command({'center': pan_tilt, 'speed': speed})

    def area_zoom(self, pos_x: int = None, pos_y: int = None, zoom: int = None,
                  speed: int = None):
        """
        Centers on positions x,y (like the center command) and zooms by a factor of z/100.

        Args:
            pos_x: value of the X coordinate.
            pos_y: value of the Y coordinate.
            zoom: zooms by a factor.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        xyzoom = str(pos_x) + "," + str(pos_y) + "," + str(zoom)
        return self._ptz_command({'areazoom': xyzoom, 'speed': speed})

    def move(self, position: str = None, speed: float = None):
        """
        Moves the device 5 degrees in the specified direction.

        Args:
            position: position to move. (home, up, down, left, right, upleft, upright, downleft...)
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'move': str(position), 'speed': speed})

    def go_home_position(self, speed: int = None):
        """
        Operation to move the PTZ device to it's "home" position.

        Args:
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'move': 'home', 'speed': speed})

    def get_status(self):
        """
        Operation to request camera status.

        Returns:
            Returns a tuple with the current camera values (pan, tilt, zoom, iris, focus, brightness, ...),
            whatever is available.

        """
        resp = self._ptz_command({'query': 'position'})
        if resp.status_code == 200:
            # create a dictionary with the camera values
            cam_values = {}
            for line in resp.text.split('\r\n'):
                if '=' in line:
                    key = line.split('=')[0]
                    value = line.split('=')[1]
                    cam_values[key] = value
        else:
            _log.error('Error getting camera status: %s', resp.status_code)
            cam_values = None

        return cam_values

    def get_ptz(self):
        """
        Operation to request PTZ status.

        Returns:
            Returns a tuple with the position of the camera (P, T, Z)

        """
        cam_values = self.get_status()
        if cam_values:
            # check if the camera values are available and return the ones that are
            pan = cam_values.get('pan', None)
            tilt = cam_values.get('tilt', None)
            zoom = cam_values.get('zoom', None)
            # TODO: check if the values are int or float
            return pan, tilt, zoom
        else:
            return None, None, None

    def get_zoom(self):
        """
        Operation to request zoom status.

        Returns:
            Returns the zoom value of the camera

        """
        cam_values = self.get_status()
        if cam_values:
            # check if the camera values are available and return the ones that are
            # TODO: check if the value is int or float
            return cam_values.get('zoom', None)
        else:
            return None

    def get_focus(self):
        """
        Operation to request focus status.

        Returns:
            Returns the focus value of the camera

        """
        cam_values = self.get_status()
        if cam_values:
            # check if the camera values are available and return the ones that are
            # TODO: check if the value is int or float
            return cam_values.get('focus', None)
        else:
            return None

    def go_to_server_preset_name(self, name: str = None, speed: int = None):
        """
        Move to the position associated with the preset on server.

        Args:
            name: name of preset position server.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'gotoserverpresetname': name, 'speed': speed})

    def go_to_server_preset_no(self, number: int = None, speed: int = None):
        """
        Move to the position associated with the specified preset position number.

        Args:
            number: number of preset position server.
            speed: speed move camera.

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'gotoserverpresetno': number, 'speed': speed})

    def go_to_device_preset(self, preset_pos: int = None, speed: int = None):
        """
        Bypasses the presetpos interface and tells the device to go directly to the preset
        position number stored in the device, where the is a device-specific preset position number.

        Args:
            preset_pos: number of preset position device
            speed: speed move camera

        Returns:
            Returns the response from the device to the command sent

        """
        return self._ptz_command({'gotodevicepreset': preset_pos, 'speed': speed})

    def list_preset_device(self):
        """
        List the presets positions stored in the device.

        Returns:
            Returns the list of presets positions stored on the device.

        """
        return self._ptz_command({'query': 'presetposcam'})

    def list_all_preset(self):
        """
        List all available presets position.

        Returns:
            Returns the list of all presets positions.

        """
        resp = self._ptz_command({'query': 'presetposall'})
        soup = BeautifulSoup(resp.text, features="lxml")
        resp_presets = soup.text.split('\n')
        presets = []

        for i in range(1, len(resp_presets) - 1):
            preset = resp_presets[i].split("=")
            presets.append((int(preset[0].split('presetposno')[1]), preset[1].rstrip('\r')))

        return presets

    def set_speed(self, speed: int = None):
        """
        Sets the head speed of the device that is connected to the specified camera.
        Args:
            speed: speed value.

        Returns:
            Returns the response from the device to the command sent.

        """
        return self._ptz_command({'speed': speed})

    def get_speed(self):
        """
        Requests the camera's speed of movement.

        Returns:
            Returns the camera's move value.

        """
        resp = self._ptz_command({'query': 'speed'})
        # check if the response is OK and does not contain an Error
        if resp.status_code == 200 and 'Error' not in resp.text:
            # return the speed value
            return int(resp.text.split()[0].split('=')[1])
        else:
            _log.error('Error getting camera speed: Status Code: %s, Response: %s', resp.status_code, resp.text)
            return None

    def info_ptz_comands(self):
        """
        Returns a description of available PTZ commands. No PTZ control is performed.

        Returns:
            Success (OK and system log content text) or Failure (error and description).

        """
        resp = self._ptz_command({'info': '1'})
        return resp.text


if __name__ == '__main__':
    ip = '10.0.220.152'
    usr = 'root'
    pwd = 'fruitsalad5671'

    # create camera object
    cam = Camera(ip, usr, pwd)

    # get camera info
    print(cam.get_info())

    # get camera available camera commands
    print(cam.info_ptz_comands())

    while True:
        print(f'Pan: {cam.get_ptz()[0]}, Tilt: {cam.get_ptz()[1]}, Zoom: {cam.get_ptz()[2]}, Focus: {cam.get_focus()}')
        time.sleep(.1)

    # cam.continuous_move(zoom=100)
