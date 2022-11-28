import subprocess
import os
from os.path import isfile, join
import time
import threading
import shutil
import pandas as pd
import re
import configparser
import json
from optparse import OptionParser

import networkx
import androguard
import torch
import transformers


def get_package_names() -> dict:
    r"""
    Installes all APKs at given path and extracts its package-name
    :return: Dictionary with { APKname : package }
    """

    create_device('package_names')
    start_emulator()

    apk_packages = {}

    # get all apks from folder
    apk_file_names = [f for f in os.listdir(apk_path) if isfile(join(apk_path, f))]
    for apk in apk_file_names:
        if apk.__eq__('tests.yml'):
            continue

        apk_packages[apk] = 'Error'

        # get all currently installed packages
        installed_before = subprocess.check_output([adb_path, 'shell', 'pm', 'list', 'packages', '-f']).decode(
            'utf-8').split('\n')

        # install apk
        print(f'Getting package name from {apk}')
        ret = subprocess.check_output([adb_path, 'install', '{}\\{}'.format(apk_path, apk)]).decode('utf-8')
        if 'Success' in ret:
            print('Successfully installed')

            installed_after = subprocess.check_output([adb_path, 'shell', 'pm', 'list', 'packages', '-f']).decode(
                'utf-8').split('\n')
            # compare installed packages to get the new one
            package_name = [pack for pack in installed_after if pack not in installed_before]

            if len(package_name) == 1:
                # get the name
                package_name = package_name[0].split('base.apk=')[1].rstrip()
                print(f'Package name is: {package_name}')

                # uninstall package
                ret = subprocess.check_output([adb_path, 'uninstall', package_name]).decode('utf-8')
                if 'Success' in ret:
                    print('Sucessfully uninstalled')

                    apk_packages[apk] = package_name
            else:
                print('Something went wrong while installing')
        else:
            print('{} - Error: {}'.format(apk, ret))

        print('\n')

    # kill env
    kill_emulator()
    return apk_packages


def create_device(method: str) -> None:
    r"""
    Uses the avdmanager to create and AVD
    Needs method to determin correct Android Version
    :param method: method for which the AVD shall be configured
    :return: None
    """

    # Determin Android version
    api = -1
    if method.__eq__('exerciserMonkey') or method.__eq__('package_names'):
        api = 31
    elif method.__eq__('droidBot'):
        api = 23
    elif method.__eq__('curiousMonkey'):
        api = 21
    else:
        print(f'This method is unknown ({method})')
        exit(1)

    # Create command
    create_command = [avdmanager_path, '--verbose', 'create', 'avd', '--name', 'Android', '--package',
                      f'system-images;android-{api};default;x86_64', '--force']

    try:
        # Run command (create Android Virtual Device)
        p = subprocess.Popen(create_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate(input='no'.encode())[0]
    except:
        print(f'You need to install API {api}')
        print(
            f'Try: 1. sdkmanager "platform-tools" "platforms;android-{api}"\n2. sdkmanager "system-images;android-{api};default;x86_64"\n 3. sdkmanager --licenses')


def start_emulator() -> None:
    r"""
    Start a already created Android Virtual Device
    :return: None
    """

    check = threading.Condition()

    # Android Device is started on different thread so the main execution of the python programm can wait for its bootup
    def inner_funct():

        start_command = [emulator_path, '-writable-system', '-avd', 'Android', '-log-nofilter', '-dns-server',
                         '192.168.178.50']
        p = subprocess.Popen(start_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print('Waiting for emulator bootup')
        for line in p.stdout:
            line = line.decode('utf-8')
            if 'boot completed' in line:
                print('Actual Booted (No timeout)')
                check.acquire()
                check.notify()
                # Notify, when Emulator is booted up
                check.release()

    t = threading.Thread(target=inner_funct, name='starting emulator')
    t.daemon = True
    t.start()

    # Wait till thread notifies or 40 seconds have passed
    check.acquire()
    check.wait(timeout=40)
    print('Emulator is booted up')
    time.sleep(3)


def kill_emulator() -> None:
    r"""
    Kills and deleted the running virtual device
    :return: None
    """

    # Kill emulator
    time.sleep(2)
    try:
        subprocess.call([adb_path, '-s', 'emulator-5554', 'emu', 'kill'])
    except Exception as e:
        print(f'Emulator already dead: {e}')

    # Delete virtual device
    time.sleep(2)
    try:
        subprocess.call([avdmanager_path, 'delete', 'avd', '-n', 'Android'])
    except Exception as e:
        print(f'ini file already deleted: {e}')

    # Delete all files that are left
    time.sleep(5)
    try:
        shutil.rmtree(avd_path, ignore_errors=True)
    except Exception as e:
        print(f'Cant delete folder: {e}')


def emulator_is_running() -> bool:
    r"""
    Checks if an AVD is currently running
    :return: True (is running), False (in not running)
    """

    command = [adb_path, 'shell', 'getprop', 'init.svc.bootanim']

    try:
        subprocess.check_call(command, shell=True)
        return True
    except:
        return False


def exerciserMonkey(name: str, package: str) -> None:
    r"""
    Runns the ExerciserMonkey
    :param name: Name of the APK
    :param package: Package of the APK
    :return: None
    """

    # Install APK on system

    print(f'Installing APK')
    install_command = [adb_path, 'install', f'{apk_path}\\{name}.apk']
    subprocess.check_call(install_command, shell=True)

    monkey_command = [adb_path, 'shell', 'monkey', '-p', package, '-v', '1000', '--throttle', '1000',
                      '--ignore-crashes', '-v']

    # Start monkey with 1000 events for 10 times
    for _ in range(0, 10):
        # check if emulator is still running
        if not emulator_is_running():
            time.sleep(3)
            start_emulator()
        try:
            p = subprocess.check_call(monkey_command, shell=True)
        except Exception as e:
            print(f'App crashed :( {e}')


def droidBot(name: str) -> None:
    r"""
    Runns the DroidBot
    :param name: Name of the APK
    :return: None
    """

    output_path_app = f'{output_path}\\droidBot\\{name}'

    droidbot_command = ['python', droidbot_path, '-a', f'{apk_path}\\{name}.apk', '-o', output_path_app, '-policy',
                        'memory_guided', '-is_emulator', '-grant_perm', '-random', '-count', '40',
                        '-accessibility_auto']
    try:
        # Start DroidBot
        print('Starting DroidBot')
        droidbot_process = subprocess.check_call(droidbot_command, shell=True)

        # Print DroidBot Output
        for line in droidbot_process.stdout:
            line = line.decode('utf-8')
            print(line)
    except Exception as e:
        print(f'App crashed :( {e}')


def curiousMonkey(name: str, package: str) -> None:
    r"""
    Runns the curiousMonkey
    :param name: Name of the APK
    :param package: Package of the APK
    :return: None
    """

    # Install APK on system
    print('Installing APK')
    install_command = [adb_path, 'install', f'{apk_path}\\{name}.apk']
    subprocess.check_call(install_command, shell=True)

    anti_vm_files = ['bbuild.prop', 'ccpuinfo', 'ddrivers', 'ttcp', 'hookset.json']
    try:
        # Upload required files
        for file in anti_vm_files:
            file_command = [adb_path, 'push', f'{curiousMonkey_path}\\Anti-Vm\\{file}', '/data/local/tmp']
            subprocess.check_call(file_command, shell=True)

    except Exception as e:
        print(f'Cant push anti-vm files - {e}')

    curiousMonkey_command = ['java', '-classpath',
                             f'{curiousMonkey_path}\\Curious-Monkey\\out\\production\\Curious-Monkey',
                             'com.android.Main.Main']
    try:
        # Run CuriousMonkey
        print('Starting Curious Monkey')
        curiousMonkey_process = subprocess.Popen(curiousMonkey_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 stdin=subprocess.PIPE, shell=True)
        out, err = curiousMonkey_process.communicate(input=f'{package}'.encode())


    except Exception as e:
        print(f'Something crashed - {e}')


def check_execution(method: str, name: str) -> str:
    r"""
    Check weather the implemented trigger is executed or not
    :param method: Currently tested Method
    :param name: Name of the APK
    :return: Documented execution state
    """

    if not emulator_is_running():
        time.sleep(3)
        start_emulator()

    # create method output path if nessesary
    if not os.path.isdir(f'{output_path}\\{method}'):
        print(f'create {method} folder')
        path = os.path.join(output_path, method)
        os.mkdir(path)

    # create trigger output path if nessesary
    if not os.path.isdir(f'{output_path}\\{method}\\{name}'):
        print(f'create {name} folder')
        path = os.path.join(f'{output_path}\\{method}', name)
        os.mkdir(path)

    output_file = open(f'{output_path}\\{method}\\{name}\\tmplog.log', 'a', encoding="utf-8")
    try:
        time.sleep(1)
        p = subprocess.Popen([adb_path, 'logcat', '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in p.stdout:
            line = line.decode('utf-8')
            line = line.strip()

            # Normalize the Log-Output (Android 5)
            pattern = r'[0-9]|[()]'
            line = re.sub(pattern, '', line)
            line = line.replace('/', ' ')
            line = line.replace(' :', ':')

            output_file.write(f'{line}\n')

    except Exception as e:
        # start emulator if it is not running
        start_emulator()
        subprocess.check_call(createlog, shell=True)

    check_command = ['python2', check_path, '-t', test_yml_path, '-l', f'{output_path}\\{method}\\{name}\\tmplog.log',
                     name]
    p = subprocess.Popen(check_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in p.stdout:
        line = line.decode('utf-8')
        if 'Pass!' in line:
            return '\\true'

    return '\\false'


def main():
    results = {}
    times = {}
    for method in trigger_methods:
        print(f'Using method: {method}')
        try:
            for name, package in packages.items():
                print(f'Testing {name}.apk')
                start_time = time.time()

                # setup env
                create_device(method)
                start_emulator()

                # Increase locat buffersize
                subprocess.check_call([adb_path, 'logcat', '-G', '5M'], shell=True)

                # start test
                if method not in results:
                    results[method] = {}

                if method.__eq__('exerciserMonkey'):
                    exerciserMonkey(name, package)
                elif method.__eq__('droidBot'):
                    droidBot(name)
                elif method.__eq__('curiousMonkey'):
                    curiousMonkey(name, package)

                print('Finished testing')

                # check and document execution
                print('Checking execution')

                triggered = check_execution(method, name)
                results[method][name] = f'{triggered} in {time.time() - start_time}'
                res_df = pd.DataFrame(results)
                res_df.to_excel(f'{output_path}\\evaluation.xlsx')
                print(json.dumps(results, sort_keys=True, indent=4))

                # kill env
                kill_emulator()

        except Exception as e:
            print(f'Something crashed :( - {e}, {method}, {name}, {package}')

    print('Thank you for using my script')


if __name__ == "__main__":

    print("""
        ────────────────────────────────────────────       
        ╔════╗────────────╔═══╗─────╔╗──────╔╗                          
        ║╔╗╔╗║────────────║╔══╝─────║║─────╔╝╚╗                        
        ╚╝║║╠╩╦╦══╦══╦══╦═╣╚══╦╗╔╦══╣║╔╗╔╦═╩╗╔╬══╦═╗                            
        ──║║║╔╬╣╔╗║╔╗║║═╣╔╣╔══╣╚╝║╔╗║║║║║║╔╗║║║╔╗║╔╝                    
        ──║║║║║║╚╝║╚╝║║═╣║║╚══╬╗╔╣╔╗║╚╣╚╝║╔╗║╚╣╚╝║║                      
        ──╚╝╚╝╚╩═╗╠═╗╠══╩╝╚═══╝╚╝╚╝╚╩═╩══╩╝╚╩═╩══╩╝                          
        ───────╔═╝╠═╝║                                                  
        ───────╚══╩══╝                                  
        ────────────────────────────────────────────
    """)

    print('Loading configuration')

    packages = {}
    try:
        # Read configuration
        config = configparser.ConfigParser()
        config.read('config.ini')

        adb_path = config['emulator_paths']['adb_path']
        sdkmanager_path = config['emulator_paths']['sdkmanager_path']
        avdmanager_path = config['emulator_paths']['avdmanager_path']
        emulator_path = config['emulator_paths']['emulator_path']
        avd_path = config['emulator_paths']['avd_path']

        output_path = config['test_paths']['output_path']
        apk_path = config['test_paths']['apk_path']
        check_path = config['test_paths']['check_path']
        test_yml_path = config['test_paths']['test_yml_path']

        trigger_methods = config['methods']['methods_to_test'].split(',')
        droidbot_path = config['methods']['droidbot_path']
        curiousMonkey_path = config['methods']['curiousMonkey_path']

        for app in config['app-packages']:
            packages[app] = config['app-packages'][app]

        print('Successfully loaded configuration')
    except:
        print('Failed to load configuration')
        exit(-1)

    parser = OptionParser()
    parser.add_option("-f", "--force", action="store_true", default=False,
                      help="Force program to get new package names")

    # get new package names
    (options, args) = parser.parse_args()
    if options.force:
        print('Forced new package names')
        packages = get_package_names()
    else:
        print('Using packages from config-file')

    main()
