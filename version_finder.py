import requests
from packaging import version
from colorama import Fore, Style
import threading
import time

result_ready = threading.Event()


def compare_packages(package1: str, package2: str, p1_version: str, p2_version: str):
    # Get the dependencies for each package
    # loading_thread = threading.Thread(target=display_loading_animation)

    package1_deps = get_package_dependencies(package1, p1_version)
    package2_deps = get_package_dependencies(package2, p2_version)

    # Find any conflicting dependencies
    conflicting_deps = package1_deps.keys() & package2_deps.keys()
    results = {"message": "Packages are compatible. No dependency conflicts."}


    if not conflicting_deps:
        # print(f"{Fore.GREEN}{Style.BRIGHT}Packages are compatible. No dependency conflicts.{Style.RESET_ALL}")
        results = {"message": "Packages are compatible. No dependency conflicts."}
    else:
        # print(f"{Fore.RED}{Style.BRIGHT}Dependency conflict found:{Style.RESET_ALL}")
        for dependency in conflicting_deps:
            version1 = package1_deps[dependency]
            version2 = package2_deps[dependency]
            conflicting = is_version_conflicting(str(version1), str(version2))

            if conflicting:
                # Determine which package has a higher version
                higher_version_package = package1 if version1 > version2 else package2
                lower_version_package = package2 if higher_version_package == package1 else package1

                results = {
                    "message": f"Dependency conflict found. {str(dependency).title()}: {higher_version_package} uses version {version1} {lower_version_package} satisfies the dependency with version {version2}"}
                # print(f"{str(dependency).title()}:")
                # print(f"{higher_version_package} uses version {version1}")
                # print("{lower_version_package} satisfies the dependency with version {version2}")
                # print(f'Conflicting: {f"{Fore.RED}{Style.BRIGHT}Yes{Style.RESET_ALL}" if conflicting else "No"}')

                # loading_thread.start()
                try:
                    compatible_versions = get_compatible_version(higher_version_package, lower_version_package,
                                                                 p2_version)

                    # print(f'\r\nSolution: {Fore.GREEN}{Style.BRIGHT}Install {higher_version_package} '
                    #       f'({next(iter(compatible_versions))}) since its compatible with '
                    #       f'{lower_version_package} ({p2_version}){Style.RESET_ALL}')

                    results["solution"] = f'Solution: Install {higher_version_package} ({next(iter(compatible_versions))}) since its compatible with {lower_version_package} ({p2_version})'

                    # print(f'All compatible versions: {Fore.BLUE}{Style.BRIGHT}{list(compatible_versions.keys())}'
                    #       f'{Style.RESET_ALL}')
                except Exception as e:
                    result_ready.set()
                    # loading_thread.join()
                    print(f'{Fore.RED}{Style.BRIGHT} Error: {e}{Style.RESET_ALL}')
                    results["error"] = f'Error: {e}'
                
            if not (conflicting_deps): 
                results = {"message": "Packages are compatible. No dependency conflicts."}
    
    # if len(conflicting_deps) == 0: 
    #     results = {"message": "Packages are compatible. No dependency conflicts."}
    # result_ready.set()
    # loading_thread.join()
    return results


def display_loading_animation():
    animation = '⣾⣽⣻⢿⡿⣟⣯⣷'
    idx = 0
    while not result_ready.is_set():
        print(
            f"\r{Fore.YELLOW}{Style.BRIGHT}{animation[idx]} Solving dependency conflicts...{Style.RESET_ALL}", end="")
        idx = (idx + 1) % len(animation)
        time.sleep(0.1)
    print('\r ', end='')


def get_compatible_version(package, control_package, control_version):
    versions = get_package_versions(package)
    versions_dict = {}
    for version in versions:
        # Get the dependencies for each package
        package1_deps = get_package_dependencies(package, version)
        package2_deps = get_package_dependencies(
            control_package, control_version)

        # Find any conflicting dependencies
        conflicting_deps = package1_deps.keys() & package2_deps.keys()
        conflicting = False
        for dep in conflicting_deps:
            version1 = package1_deps[dep]
            version2 = package2_deps[dep]
            conflicting = conflicting or is_version_conflicting(
                str(version1), str(version2))

        versions_dict.setdefault(str(version), conflicting)

    compatible_versions = {ver: is_false for ver,
                           is_false in versions_dict.items() if not is_false}
    return compatible_versions


def is_version_conflicting(version1: str, version2: str):
    v1min = get_version(version1, 'min')
    v2min = get_version(version2, 'min')
    v1max = get_version(version1, 'max')
    v2max = get_version(version2, 'max')
    status = False
    if v2min[1] and v1min[1]:
        if v1min[1] > v2min[1]:
            status = is_conflicting(v2min, v1min)
            status = status or is_conflicting(v2max, v1max)
            status = status or is_conflicting(v2min, v1max)
            status = status or is_conflicting(v2max, v1min)
            return status
        else:
            status = is_conflicting(v1min, v2min)
            status = status or is_conflicting(v1max, v2max)
            status = status or is_conflicting(v1min, v2max)
            status = status or is_conflicting(v1max, v2min)
            return status
    else:
        return False


def is_conflicting(lower: list, higher: list):
    if lower[0] == '>=':
        if lower[1] <= higher[1] or (lower[1] >= higher[1] and (higher[0] == '>=' or higher[0] == '!=' or higher[0] == '>')):
            if higher[1] == lower[1] and (higher[0] == '<' or higher[0] == '<='):
                return True
            return False
        elif lower[1] >= higher[1] and higher[0] == '~=':
            if is_range_same(lower, higher):
                return False

    if lower[0] == '<=':
        if lower[1] >= higher[1] or (lower[1] <= higher[1] and (higher[0] == '<=' or higher[0] == '!=' or higher[0] == '<')):
            if higher[1] == lower[1] and (higher[0] == '>' or higher[0] == '>='):
                return True
            return False
        elif lower[1] <= higher[1] and higher[0] == '~=':
            if is_range_same(lower, higher):
                return False

    if lower[0] == '>':
        if lower[1] <= higher[1] or (lower[1] > higher[1] and (higher[0] == '>=' or higher[0] == '!=' or higher[0] == '>')):
            if higher[1] == lower[1] and (higher[0] == '<' or higher[0] == '<=' or higher[0] == '=='):
                return True

            return False

    if lower[0] == '<':
        if higher[1] <= lower[1] or (lower[1] < higher[1] and (higher[0] == '<=' or higher[0] == '!=' or higher[0] == '<')):
            if higher[1] == lower[1] and (higher[0] == '>' or higher[0] == '>=' or higher[0] == '=='):
                return True

            return False

    if lower[0] == '==':
        if higher[1] <= lower[1] or (lower[1] < higher[1] and (higher[0] == '<=' or higher[0] == '<')):
            return False
        elif higher[0] == '~=' and is_range_same(lower, higher):
            return False

    if lower[0] == '!=':
        if higher[1] != lower[1]:
            return False

    if lower[0] == '~=':
        if is_range_same(lower, higher):
            return False
        elif (higher[0] == '>' or higher[0] == '>=') and (higher[1] > lower[1]):
            return False
        elif (higher[0] == '<' or higher[0] == '<=') and (higher[1] > lower[1]):
            return False

    return True


def is_range_same(lower: list, higher: list):
    h_numbers = str(higher[1]).split('.')
    l_numbers = str(lower[1]).split('.')

    if len(h_numbers) >= len(l_numbers):
        if len(l_numbers) < 3:
            size = len(l_numbers)
        else:
            size = len(l_numbers) - 1
    else:
        if len(h_numbers) < 3:
            size = len(h_numbers)
        else:
            size = len(h_numbers) - 1

    status = True
    for i in range(size):
        status = status and h_numbers[i] == l_numbers[i]

    return status


def get_version(version: str, version_type: str):
    v_constrains = version.strip().split(
        ' ')[-1].replace('(', '').replace(')', '').split(',')
    if version_type == 'min':
        return separate_operator_and_number(v_constrains[-1])
    if version_type == 'max':
        return separate_operator_and_number(v_constrains[0])


def get_package_dependencies(package_name, package_version):
    url = f"https://pypi.org/pypi/{package_name}/{package_version}/json"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        package_info = response.json()

        info = package_info.get("info")
        if info:
            dependencies = info.get("requires_dist")
            if dependencies:
                return parse_dependencies(dependencies)

    return {}


def parse_dependencies(dependencies):
    parsed_deps = {}

    for dependency in dependencies:
        parts = dependency.strip().split(";")
        dependency_name = parts[0].split()[0]
        parsed_deps[dependency_name] = parts[0]

    return parsed_deps


def separate_operator_and_number(input_string):
    operators = ['>=', '>', '<=', '<', '==', '!=', '~=']
    operator = None
    number = None

    for op in operators:
        if input_string.startswith(op):
            operator = op
            number = version.parse(input_string[len(op):].replace("'", ""))
            break

    return [operator, number]


def get_package_versions(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        package_info = response.json()
        releases = package_info.get("releases")
        if releases:
            return sorted(list(releases.keys()), key=version.parse, reverse=True)

    return []
