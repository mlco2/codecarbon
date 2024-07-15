import os
import re
import shutil
import sys
from typing import Dict
import os 
import platform 
import numpy as np
import queue

import subprocess as sp
# Threading
from threading import Thread, Event

from codecarbon.core.util import detect_cpu_model
from codecarbon.external.logger import logger
import re
WATT_RE = re.compile(r'\b(\w+) ([0-9.]+)(\w?)W?\/([0-9.]+)(\w?)W?\b')
GPU_WATT_RE = re.compile(r'\b(VDD_GPU_SOC) ([0-9.]+)(\w?)W?\/([0-9.]+)(\w?)W?\b')
CPU_WATT_RE = re.compile(r'\b(VDD_CPU_CV) ([0-9.]+)(\w?)W?\/([0-9.]+)(\w?)W?\b')

def is_tegrametrics_available():
    try:
        if platform.system()=="Linux":
            if "tegra" in platform.release():
               import pynvml
               pynvml.nvmlInit()
               return True
        return False
    except Exception as e:
        logger.debug(
            "Not using Tegrametrics, an exception occurred while instantiating pynvml"
            + f" Tegrametrics : {e}",
        )
        return False

class NvidiaTegrametrics:
    def __init__(
        self,
        n_points=10,
        interval=100,
    ):
        self._interval = interval
        self._n_point=n_points
       
        self._running = Event()
        self.path = "/usr/bin/tegrastats"
        self._error = None
        self._thread = None
       
        self.cpu_queue = queue.Queue()
        self.gpu_queue= queue.Queue()
        self._gpu_power_list=[]
        self._cpu_power_list=[]

    def _decode(self, text):
        name, gpu_cur, gpu_unit_cur, avg, unit_avg = re.findall(GPU_WATT_RE, text)[0]
        name, cpu_cur, cpu_unit_cur, avg, unit_avg = re.findall(CPU_WATT_RE, text)[0]
        if gpu_unit_cur=='m':
           gpu_cur=float(gpu_cur)/1000.0
        if cpu_unit_cur=='m':
           cpu_cur=float(cpu_cur)/1000.0
        self.cpu_queue.put(float(cpu_cur), True, 1)
        self.gpu_queue.put(float(gpu_cur), True, 1)
    
    def _thread_read_tegrastats(self):
        pts = sp.Popen([self.path, '--interval', str(self._interval)], stdout=sp.PIPE)
        try:
            # Reading loop
            while self._running.is_set():
                if pts.poll() is not None:
                    continue
                out = pts.stdout
                if out is not None:
                    # Read line process output
                    line = out.readline().decode("utf-8")
                    stats = self._decode(line)
        except AttributeError:
            pass
        except OSError:
            pass
        except Exception:
            # Write error message
            self._error = sys.exc_info()
            ex_type, ex_value, tb_str = self._error
            logger.info(tb_str)
        finally:
            # Kill process
            try:
                pts.kill()
            except OSError:
                pass

    def get_details(self, **kwargs) -> Dict:
        details = dict()
        if self.gpu_queue.qsize()<self._n_point:
            logger.info("not enough data yet size=%d" % self.gpu_queue.qsize())
            return details
        while(self.gpu_queue.qsize()>self._n_point):
             self._gpu_power_list.append(self.gpu_queue.get(True,1)) 
             self._cpu_power_list.append(self.cpu_queue.get(True,1)) 
        if len(self._gpu_power_list)>0 and len(self._cpu_power_list)>0:
             details["CPU Power"] = np.mean(self._cpu_power_list)
             details["CPU Energy Delta"] = np.sum(self._cpu_power_list)*(float(self._interval) / 1000.0) 
             details["GPU Power"] = np.mean(self._gpu_power_list)
             details["GPU Energy Delta"] = np.sum(self._gpu_power_list)*(float(self._interval) / 1000.0)
        return details

    def start(self):
        if self._thread is not None:
            return False
        logger.info("starting tegrastats thread with %s ms"  % self._interval)
        self._running.set()
        self._thread = Thread(target=self._thread_read_tegrastats, args=())
        self._thread.start()
    def stop(self,timeout=None):
        if self._error:
            # Extract exception and raise
            ex_type, ex_value, tb_str = self._error
            ex_value.__traceback__ = tb_str
            raise ex_value
        # stop thread main loop
        self._running.clear()
        if self._thread is not None:
            logger.info("stopping tegrastats thread")
            self._thread.join(timeout)
            self._thread = None
        return True        
