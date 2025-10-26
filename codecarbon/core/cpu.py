"""
Implements tracking Intel CPU Power Consumption on Mac and Windows
using Intel Power Gadget
https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html
"""

import os
import re
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple

import pandas as pd
import psutil
from rapidfuzz import fuzz, process, utils

from codecarbon.core.rapl import RAPLFile
from codecarbon.core.units import Time
from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger
from codecarbon.input import DataSource

# default W value per core for a CPU if no model is found in the ref csv
DEFAULT_POWER_PER_CORE = 4


def is_powergadget_available() -> bool:
    """
    Checks if Intel Power Gadget is available on the system.

    Returns:
        bool: `True` if Intel Power Gadget is available, `False` otherwise.
    """
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            "Not using PowerGadget, an exception occurred while instantiating "
            + "IntelPowerGadget : %s",
            e,
        )
        return False


def is_rapl_available(rapl_dir: Optional[str] = None) -> bool:
    """
    Checks if Intel RAPL is available on the system.

    Returns:
        bool: `True` if Intel RAPL is available, `False` otherwise.
    """
    # Lightweight detection: scan common powercap locations for a readable
    # package/main `energy_uj` file. We avoid instantiating `IntelRAPL` here so
    # that callers can decide to create the full interface only when this
    # pre-check passes. This prevents raising during global initialization and
    # lets callers fall back gracefully.
    if rapl_dir is None:
        rapl_dir = "/sys/class/powercap/intel-rapl/subsystem"

    default_rapl_dir = "/sys/class/powercap/intel-rapl/subsystem"
    is_default_dir = os.path.abspath(rapl_dir) == os.path.abspath(default_rapl_dir)

    if is_default_dir:
        # Production: scan all common RAPL locations
        candidate_bases = [
            rapl_dir,
            os.path.dirname(rapl_dir),
            "/sys/class/powercap",
            "/sys/devices/virtual/powercap",
        ]
    else:
        # Testing or custom directory: only scan the specified location
        candidate_bases = [
            rapl_dir,
            os.path.dirname(rapl_dir),
        ]

    seen = set()
    candidate_bases = [
        p
        for p in candidate_bases
        if p and not (p in seen or seen.add(p)) and os.path.exists(p)
    ]

    try:
        for base in candidate_bases:
            try:
                for entry in os.listdir(base):
                    if not entry.startswith("intel-rapl"):
                        continue
                    entry_path = os.path.join(base, entry)
                    if not os.path.isdir(entry_path):
                        continue

                    # Look for domain directories (contain ':') under provider
                    for sub in os.listdir(entry_path):
                        sub_path = os.path.join(entry_path, sub)
                        if ":" not in sub or not os.path.isdir(sub_path):
                            continue

                        energy_path = os.path.join(sub_path, "energy_uj")
                        name_path = os.path.join(sub_path, "name")

                        # Determine if this domain looks like the main/package domain
                        is_main = False
                        try:
                            if os.path.exists(name_path):
                                with open(name_path, "r") as nf:
                                    name = nf.read().strip().lower()
                                    if "package" in name:
                                        is_main = True
                        except Exception:
                            # If we cannot read the name file, fall back to basename rule
                            pass
                        if sub.endswith(":0"):
                            is_main = True

                        if os.path.exists(energy_path) and os.access(
                            energy_path, os.R_OK
                        ):
                            if is_main:
                                return True

                # Also support trees where `intel-rapl:$i` entries are directly inside `base`
                for item in os.listdir(base):
                    if ":" not in item:
                        continue
                    p = os.path.join(base, item)
                    if not os.path.isdir(p):
                        continue
                    energy_path = os.path.join(p, "energy_uj")
                    name_path = os.path.join(p, "name")

                    is_main = False
                    try:
                        if os.path.exists(name_path):
                            with open(name_path, "r") as nf:
                                name = nf.read().strip().lower()
                                if "package" in name:
                                    is_main = True
                    except Exception:
                        pass
                    if item.endswith(":0"):
                        is_main = True
                    if os.path.exists(energy_path) and os.access(energy_path, os.R_OK):
                        if is_main:
                            return True
            except Exception:
                # Ignore ephemeral errors during detection and continue scanning
                logger.debug(
                    "Error while scanning %s for RAPL domains", base, exc_info=True
                )
                continue
    except Exception:
        logger.debug("Unexpected error while checking RAPL availability", exc_info=True)

    return False


def is_psutil_available():
    try:
        nice = psutil.cpu_times().nice
        if nice > 0.0001:
            return True
        else:
            logger.debug(
                f"is_psutil_available() : psutil.cpu_times().nice is too small : {nice} !"
            )
            return False
    except Exception as e:
        logger.debug(
            "Not using the psutil interface, an exception occurred while instantiating "
            + f"psutil.cpu_times : {e}",
        )
        return False


class IntelPowerGadget:
    """
    A class to interface with Intel Power Gadget for monitoring CPU power consumption on Windows and (non-Apple Silicon) macOS.

    This class provides methods to set up and execute Intel Power Gadget's command-line interface (CLI) to
    log power consumption data over a specified duration and resolution. It also includes functionality to
    read and process the logged data to extract CPU power details.

    Methods:
        start():
            Placeholder method for starting the Intel Power Gadget monitoring.

        get_cpu_details() -> Dict:
            Fetches the CPU power details by reading the values from the logged CSV file.

    """

    _osx_exec = "PowerLog"
    _osx_exec_backup = "/Applications/Intel Power Gadget/PowerLog"
    _windows_exec = "PowerLog3.0.exe"

    def __init__(
        self,
        output_dir: str = ".",
        duration=1,
        resolution=100,
        log_file_name="intel_power_gadget_log.csv",
    ):
        self._log_file_path = os.path.join(output_dir, log_file_name)
        self._system = sys.platform.lower()
        self._duration = duration
        self._resolution = resolution
        self._windows_exec_backup = None
        self._setup_cli()

    def _setup_cli(self) -> None:
        """
        Setup cli command to run Intel Power Gadget
        """
        if self._system.startswith("win"):
            self._get_windows_exec_backup()
            if shutil.which(self._windows_exec):
                self._cli = shutil.which(
                    self._windows_exec
                )  # Windows exec is a relative path
            elif shutil.which(self._windows_exec_backup):
                self._cli = self._windows_exec_backup
            else:
                raise FileNotFoundError(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("darwin"):
            if shutil.which(self._osx_exec):
                self._cli = self._osx_exec
            elif shutil.which(self._osx_exec_backup):
                self._cli = self._osx_exec_backup
            else:
                raise FileNotFoundError(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        else:
            raise SystemError("Platform not supported by Intel Power Gadget")

    def _get_windows_exec_backup(self) -> None:
        """
        Find the windows executable for the current version of intel power gadget.
        Example: "C:\\Program Files\\Intel\\Power Gadget 3.5\\PowerLog3.0.exe"
        """
        parent_folder = "C:\\Program Files\\Intel\\"

        # Get a list of all subdirectories in the parent folder
        subfolders = [f.name for f in os.scandir(parent_folder) if f.is_dir()]

        # Look for a folder that contains "Power Gadget" in its name
        desired_folder = next(
            (folder for folder in subfolders if "Power Gadget" in folder), None
        )
        if desired_folder:
            self._windows_exec_backup = os.path.join(
                parent_folder, desired_folder, self._windows_exec
            )
        else:
            self._windows_exec_backup = None

    def _log_values(self) -> None:
        """
        Logs output from Intel Power Gadget command line to a file
        """
        returncode = None
        if self._system.startswith("win"):
            returncode = subprocess.call(
                [
                    self._cli,
                    "-duration",
                    str(self._duration),
                    "-resolution",
                    str(self._resolution),
                    "-file",
                    self._log_file_path,
                ],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        elif self._system.startswith("darwin"):
            returncode = subprocess.call(
                f"'{self._cli}' -duration {self._duration} -resolution {self._resolution} -file {self._log_file_path} > /dev/null",  # noqa: E501
                shell=True,
            )
        else:
            return None

        if returncode != 0:
            logger.warning(
                "Returncode while logging power values using "
                + "Intel Power Gadget: %s",
                returncode,
            )

    def get_cpu_details(self) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file
        in _log_values function
        """
        self._log_values()
        cpu_details = {}
        try:
            cpu_data = pd.read_csv(self._log_file_path).dropna()
            for col_name in cpu_data.columns:
                if col_name in ["System Time", "Elapsed Time (sec)", "RDTSC"]:
                    continue
                if "Cumulative" in col_name:
                    cpu_details[col_name] = cpu_data[col_name].iloc[-1]
                else:
                    cpu_details[col_name] = cpu_data[col_name].mean()
        except Exception as e:
            logger.info(
                f"Unable to read Intel Power Gadget logged file at {self._log_file_path}\n \
                Exception occurred %s",
                e,
                exc_info=True,
            )
        return cpu_details

    def start(self) -> None:
        """
        Placeholder method for starting the Intel Power Gadget monitoring.
        """
        # TODO: Read energy


class IntelRAPL:
    """
    A class to interface Intel's Running Average Power Limit (RAPL) for monitoring CPU power consumption.

    This class provides methods to set up and read energy consumption data from Intel RAPL files,
    which are available on Linux systems.
    It enables the measurement of CPU energy usage over time and provides methods to fetch
    both dynamic and static CPU energy details.

    Attributes:
        _lin_rapl_dir (str): The directory path where Intel RAPL files are located.
        _system (str): The platform of the running system, typically used to ensure compatibility.
        _rapl_files (List[RAPLFile]): A list of RAPLFile objects representing the files to read energy data from.
        _cpu_details (Dict): A dictionary storing the latest CPU energy details.
        _last_mesure (int): Placeholder for storing the last measurement time.

    Methods:
        start():
            Starts monitoring CPU energy consumption.

        get_cpu_details(duration: Time) -> Dict:
            Fetches the CPU energy deltas over a specified duration by reading values from RAPL files.

        get_static_cpu_details() -> Dict:
            Returns the CPU details without recalculating them.

    """

    def __init__(self, rapl_dir="/sys/class/powercap/intel-rapl/subsystem"):
        self._lin_rapl_dir = rapl_dir
        self._system = sys.platform.lower()
        self._rapl_files = []
        self._setup_rapl()
        self._cpu_details: Dict = {}

        self._last_mesure = 0

    def _is_platform_supported(self) -> bool:
        return self._system.startswith("lin")

    def _setup_rapl(self) -> None:
        if self._is_platform_supported():
            if os.path.exists(self._lin_rapl_dir):
                self._fetch_rapl_files()
            else:
                raise FileNotFoundError(
                    f"Intel RAPL files not found at {self._lin_rapl_dir} "
                    + f"on {self._system}"
                )
        else:
            raise SystemError("Platform not supported by Intel RAPL Interface")

    def _fetch_rapl_files(self) -> None:
        """
        Fetches RAPL files from the RAPL directory
        """
        # We'll scan common powercap locations and look for domain directories
        # that expose an `energy_uj` file. We try to be tolerant to permission
        # errors and simply skip unreadable entries instead of failing the whole
        # tracker when one RAPL subtree is not accessible (e.g., intel-rapl-mmio).
        #
        # When using the default RAPL directory, we scan all common system locations
        # to ensure we don't miss any RAPL providers (including intel-rapl-mmio).
        # When a custom rapl_dir is provided (e.g., for testing), we only scan
        # that directory and its parent to avoid interference with system files.
        default_rapl_dir = "/sys/class/powercap/intel-rapl/subsystem"
        is_default_dir = os.path.abspath(self._lin_rapl_dir) == os.path.abspath(
            default_rapl_dir
        )

        if is_default_dir:
            # Production: scan all common RAPL locations
            candidate_bases = [
                self._lin_rapl_dir,
                os.path.dirname(self._lin_rapl_dir),
                "/sys/class/powercap",
                "/sys/devices/virtual/powercap",
            ]
        else:
            # Testing or custom directory: only scan the specified location
            candidate_bases = [
                self._lin_rapl_dir,
                os.path.dirname(self._lin_rapl_dir),
            ]

        # Deduplicate while preserving order and keep only existing paths
        seen = set()
        candidate_bases = [
            p
            for p in candidate_bases
            if p and not (p in seen or seen.add(p)) and os.path.exists(p)
        ]

        domain_dirs = []
        found_main_readable = False
        for base in candidate_bases:
            try:
                for entry in os.listdir(base):
                    # Look for powercap provider directories like 'intel-rapl' or 'intel-rapl-mmio'
                    if not entry.startswith("intel-rapl"):
                        continue
                    entry_path = os.path.join(base, entry)
                    if not os.path.isdir(entry_path):
                        continue
                    # Look for domain directories under the provider that usually contain ':' in their name
                    try:
                        for sub in os.listdir(entry_path):
                            sub_path = os.path.join(entry_path, sub)
                            if ":" in sub and os.path.isdir(sub_path):
                                # Only consider if energy file exists
                                if os.path.exists(os.path.join(sub_path, "energy_uj")):
                                    domain_dirs.append(sub_path)
                    except Exception as e:
                        if isinstance(e, PermissionError):
                            logger.warning(
                                "\tRAPL - Permission denied listing %s: %s",
                                entry_path,
                                e,
                            )
                        else:
                            logger.debug("\tRAPL - Cannot list %s: %s", entry_path, e)
            except Exception as e:
                if isinstance(e, PermissionError):
                    logger.warning(
                        "\tRAPL - Permission denied scanning %s for RAPL domains: %s",
                        base,
                        e,
                    )
                else:
                    logger.debug(
                        "\tRAPL - Cannot scan %s for RAPL domains: %s", base, e
                    )

        # Fallback: if none found and the configured path looks like it directly
        # contains domain entries, try listing it (preserves backward compatibility).
        if not domain_dirs:
            try:
                for item in os.listdir(self._lin_rapl_dir):
                    if ":" in item:
                        path = os.path.join(self._lin_rapl_dir, item)
                        if os.path.isdir(path) and os.path.exists(
                            os.path.join(path, "energy_uj")
                        ):
                            domain_dirs.append(path)
            except Exception:
                # ignore: we'll handle the empty domain_dirs case below
                pass

        # Remove duplicates
        domain_dirs = list(dict.fromkeys(domain_dirs))

        # Build a list of successfully readable domains with their metadata
        # We'll deduplicate at the end, after we know which ones are readable
        readable_domains = (
            []
        )  # List of (name, domain_dir, is_mmio, rapl_file, rapl_file_max)

        i = 0
        for domain_dir in domain_dirs:
            try:
                name_path = os.path.join(domain_dir, "name")
                name = None
                if os.path.exists(name_path):
                    try:
                        with open(name_path) as f:
                            name = f.read().strip()
                    except Exception as e:
                        if isinstance(e, PermissionError):
                            logger.warning(
                                "\tRAPL - Permission denied reading name file %s: %s",
                                name_path,
                                e,
                            )
                        else:
                            logger.debug(
                                "\tRAPL - Unable to read name file %s: %s", name_path, e
                            )
                if not name:
                    # Use the domain directory basename as a fallback
                    name = os.path.basename(domain_dir)

                if "package" in name:
                    name = f"Processor Energy Delta_{i}(kWh)"
                    i += 1

                rapl_file = os.path.join(domain_dir, "energy_uj")
                rapl_file_max = os.path.join(domain_dir, "max_energy_range_uj")

                # Quick sanity check: can we read the energy value? If not,
                # skip gracefully but mark whether we found a readable main
                # domain. We avoid raising here: callers should use
                # `is_rapl_available()` to pre-check availability and decide
                # whether to instantiate the full interface.
                is_required_main = ("package" in name.lower()) or os.path.basename(
                    domain_dir
                ).endswith(":0")
                try:
                    with open(rapl_file, "r") as f:
                        _ = float(f.read())
                    # If the main/package counter is readable, mark availability
                    if is_required_main:
                        found_main_readable = True
                except PermissionError:
                    msg = f"\tRAPL - Permission denied reading RAPL file {rapl_file}."
                    suggestion = "You can grant read permission with: sudo chmod -R a+r /sys/class/powercap/*"
                    logger.warning("%s %s; skipping.", msg, suggestion)
                    # do not raise; skip this domain
                    continue
                except Exception as e:
                    logger.debug(
                        "\tRAPL - Skipping non-numeric or unreadable RAPL file %s: %s",
                        rapl_file,
                        e,
                    )
                    continue

                # This domain is readable, add it to our list
                is_mmio = "intel-rapl-mmio" in domain_dir
                readable_domains.append(
                    (name, domain_dir, is_mmio, rapl_file, rapl_file_max)
                )
            except Exception as e:
                # Log and continue on any per-domain failure; availability is
                # determined from whether a main/package counter was readable.
                logger.warning(
                    "\tRAPL - Error processing RAPL domain %s: %s", domain_dir, e
                )
                continue

        # Deduplicate readable domains with same name, preferring MMIO over MSR-based
        # This prevents double-counting when same domain appears in both
        # intel-rapl and intel-rapl-mmio (e.g., package-0)

        # First, check if we have a psys (platform/system) domain
        # psys provides total platform power and already includes package, core, uncore, etc.
        # Using psys alone is the best way to avoid double-counting on modern Intel systems
        psys_domain = None
        for domain_tuple in readable_domains:
            name, domain_dir, is_mmio, rapl_file, rapl_file_max = domain_tuple

            # Check if this is a psys domain
            try:
                name_path = os.path.join(domain_dir, "name")
                if os.path.exists(name_path):
                    with open(name_path) as f:
                        domain_name = f.read().strip().lower()
                        if domain_name == "psys":
                            psys_domain = domain_tuple
                            logger.info(
                                "\tRAPL - Found psys (platform/system) domain - this provides "
                                "total platform power and avoids double-counting"
                            )
                            break
            except Exception:
                pass

        # If psys is available, use ONLY psys to avoid all double-counting
        if psys_domain:
            logger.info(
                "\tRAPL - Using only psys domain for power measurement to ensure accuracy. "
                "Other domains (package, core, uncore) are subsets of psys."
            )
            domain_map = {"psys": psys_domain}
        else:
            # No psys available, fall back to deduplicating package/core/uncore domains
            logger.warning(
                "\tRAPL - No psys domain found, using individual domains (package, core, uncore)"
            )
            domain_map = (
                {}
            )  # name -> (name, domain_dir, is_mmio, rapl_file, rapl_file_max)
            for domain_tuple in readable_domains:
                name, domain_dir, is_mmio, rapl_file, rapl_file_max = domain_tuple

                # Extract the base name (without "Processor Energy Delta_X" numbering)
                # to properly identify duplicates
                base_name = name
                if "Processor Energy" in name:
                    # This is a package domain, use the original domain name for deduplication
                    try:
                        name_path = os.path.join(domain_dir, "name")
                        if os.path.exists(name_path):
                            with open(name_path) as f:
                                base_name = f.read().strip()
                    except Exception:
                        base_name = os.path.basename(domain_dir)

                # If we haven't seen this base name, or we're replacing MSR with MMIO, keep it
                if base_name not in domain_map or (
                    is_mmio and not domain_map[base_name][2]
                ):
                    domain_map[base_name] = domain_tuple

        logger.debug(
            "\tRAPL - Found %d unique RAPL domains after deduplication (from %d readable domains)",
            len(domain_map),
            len(readable_domains),
        )

        # Now create RAPLFile objects for deduplicated domains
        for name, _, is_mmio, rapl_file, rapl_file_max in domain_map.values():
            try:
                # Determine interface type for logging
                interface_type = "MMIO" if is_mmio else "MSR"
                self._rapl_files.append(
                    RAPLFile(name=name, path=rapl_file, max_path=rapl_file_max)
                )
                logger.debug(
                    "\tRAPL - Reading RAPL domain '%s' via %s interface at %s",
                    name,
                    interface_type,
                    rapl_file,
                )
            except PermissionError as e:
                logger.warning(
                    "\tRAPL - Permission denied while initializing RAPL file %s: %s",
                    rapl_file,
                    e,
                )
                continue
            except Exception as e:
                logger.debug(
                    "\tRAPL - Unable to initialize RAPLFile for %s: %s", rapl_file, e
                )
                continue

        # Save whether we found a readable main/package energy counter so
        # callers can query `intel_rapl._available` if desired.
        try:
            self._available = bool(found_main_readable)
        except Exception:
            self._available = False

    def get_cpu_details(self, duration: Time) -> Dict:
        """
        Fetches the CPU Energy Deltas by fetching values from RAPL files
        """
        cpu_details = {}
        try:
            list(map(lambda rapl_file: rapl_file.delta(duration), self._rapl_files))

            for rapl_file in self._rapl_files:
                logger.debug(rapl_file)
                cpu_details[rapl_file.name] = rapl_file.energy_delta.kWh
                # We fake the name used by Power Gadget when using RAPL
                if "Energy" in rapl_file.name:
                    cpu_details[rapl_file.name.replace("Energy", "Power")] = (
                        rapl_file.power.W
                    )
        except Exception as e:
            logger.info(
                "\tRAPL - Unable to read Intel RAPL files at %s\n \
                Exception occurred %s",
                self._rapl_files,
                e,
                exc_info=True,
            )
        self._cpu_details = cpu_details
        logger.debug("get_cpu_details %s", self._cpu_details)
        return cpu_details

    def get_static_cpu_details(self) -> Dict:
        """
        Return CPU details without computing them.
        """
        return self._cpu_details

    def start(self) -> None:
        """
        Starts monitoring CPU energy consumption.
        """
        for rapl_file in self._rapl_files:
            rapl_file.start()


class TDP:
    """
    Represents Thermal Design Power (TDP) for detecting and estimating
    the power consumption of the CPU on a machine.

    The class provides methods to identify the CPU model, match it with known TDP
    values from a dataset, and return the corresponding power consumption in watts.

    Attributes:
        model (str): The detected CPU model name.
        tdp (int): The TDP value of the detected CPU in watts.

    Methods:
        start():
            Placeholder method to initiate TDP analysis.

    """

    def __init__(self):
        self.model, self.tdp = self._main()

    @staticmethod
    def _get_cpu_constant_power(match: str, cpu_power_df: pd.DataFrame) -> int:
        """Extract constant power from matched CPU"""
        return float(cpu_power_df[cpu_power_df["Name"] == match]["TDP"].values[0])

    def _get_cpu_power_from_registry(self, cpu_model_raw: str) -> Optional[int]:
        cpu_power_df = DataSource().get_cpu_power_data()
        cpu_matching = self._get_matching_cpu(cpu_model_raw, cpu_power_df)
        if cpu_matching:
            power = self._get_cpu_constant_power(cpu_matching, cpu_power_df)
            return power
        return None

    def _get_matching_cpu(
        self, model_raw: str, cpu_df: pd.DataFrame, greedy=False
    ) -> str:
        """
        Get matching cpu name

        :args:
            model_raw (str): raw name of the cpu model detected on the machine

            cpu_df (DataFrame): table containing cpu models along their tdp

            greedy (default False): if multiple cpu models match with an equal
            ratio of similarity, greedy (True) selects the first model,
            following the order of the cpu list provided, while non-greedy
            returns None.

        :return: name of the matching cpu model

        :notes:
            Thanks to the greedy mode, even though the match could be a model
            with a tdp very different from the actual tdp of current cpu, it
            still enables the relative comparison of models emissions running
            on the same machine.

            THRESHOLD_DIRECT defines the similarity ratio value to consider
            almost-exact matches.

            THRESHOLD_TOKEN_SET defines the similarity ratio value to consider
            token_set matches (for more detail see fuzz.token_set_ratio).
        """
        THRESHOLD_DIRECT: int = 100
        THRESHOLD_TOKEN_SET: int = 100

        direct_match = process.extractOne(
            model_raw,
            cpu_df["Name"],
            processor=lambda s: s.lower(),
            scorer=fuzz.ratio,
            score_cutoff=THRESHOLD_DIRECT,
        )

        if direct_match:
            return direct_match[0]

        model_raw = model_raw.replace("(R)", "")
        start_cpu = model_raw.find(" CPU @ ")
        if start_cpu > 0:
            model_raw = model_raw[0:start_cpu]
        model_raw = model_raw.replace(" CPU", "")
        model_raw = re.sub(r" @\s*\d+\.\d+GHz", "", model_raw)
        direct_match = process.extractOne(
            model_raw,
            cpu_df["Name"],
            processor=lambda s: s.lower(),
            scorer=fuzz.ratio,
            score_cutoff=THRESHOLD_DIRECT,
        )

        if direct_match:
            return direct_match[0]
        indirect_matches = process.extract(
            model_raw,
            cpu_df["Name"],
            processor=utils.default_process,
            scorer=fuzz.token_set_ratio,
            score_cutoff=THRESHOLD_TOKEN_SET,
        )

        if indirect_matches:
            if (
                greedy
                or len(indirect_matches) == 1
                or indirect_matches[0][1] != indirect_matches[1][1]
            ):
                return indirect_matches[0][0]

        return None

    def _main(self) -> Tuple[str, int]:
        """
        Get CPU power from constant mode

        :return: model name (str), power in Watt (int)
        """
        cpu_model_detected = detect_cpu_model()

        if cpu_model_detected:
            power = self._get_cpu_power_from_registry(cpu_model_detected)

            if power:
                logger.debug(
                    "CPU : We detect a %s with a TDP of %s W",
                    cpu_model_detected,
                    power,
                )
                return cpu_model_detected, power
            logger.warning(
                "We saw that you have a %s but we don't know it."
                + " Please contact us.",
                cpu_model_detected,
            )
            if is_psutil_available():
                # Count thread of the CPU
                threads = psutil.cpu_count(logical=True)
                estimated_tdp = threads * DEFAULT_POWER_PER_CORE
                logger.warning(
                    f"We will use the default power consumption of {DEFAULT_POWER_PER_CORE} W per thread for your {threads} CPU, so {estimated_tdp}W."
                )
                return cpu_model_detected, estimated_tdp
            return cpu_model_detected, None
        logger.warning(
            "We were unable to detect your CPU using the `cpuinfo` package."
            + " Resorting to a default power consumption."
        )
        return "Unknown", None

    def start(self):
        pass
