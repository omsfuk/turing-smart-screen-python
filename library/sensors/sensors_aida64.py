# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file will use AIDA64 shared memory to get hardware sensors
# For Windows platforms only

import ctypes
import math
import xml.etree.ElementTree as ET
from statistics import mean
from typing import Tuple, Dict, Any
from ctypes import wintypes

import psutil

import library.sensors.sensors as sensors
from library.log import logger

# Windows API functions
kernel32 = ctypes.windll.kernel32

# Define Windows API functions
OpenFileMapping = kernel32.OpenFileMappingW
OpenFileMapping.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
OpenFileMapping.restype = wintypes.HANDLE

MapViewOfFile = kernel32.MapViewOfFile
MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
MapViewOfFile.restype = wintypes.LPVOID

UnmapViewOfFile = kernel32.UnmapViewOfFile
UnmapViewOfFile.argtypes = [wintypes.LPVOID]
UnmapViewOfFile.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

# Global cache for sensor data
_sensor_cache = {}
_cache_valid = False

def read_aida64_shared_memory() -> Dict[str, Any]:
    """读取AIDA64共享内存数据"""
    global _sensor_cache, _cache_valid
    
    # 共享内存名称
    mapping_name = "AIDA64_SensorValues"
    
    try:
        # 打开共享内存 (FILE_MAP_READ = 0x0004)
        h_map_file = OpenFileMapping(0x0004, False, mapping_name)
        
        # 检查是否为无效句柄
        if h_map_file == ctypes.c_void_p(-1).value or h_map_file == 0:
            err_code = ctypes.get_last_error()
            if err_code == 5:
                raise Exception("访问被拒绝。请尝试以管理员身份运行脚本，或检查AIDA64共享内存权限设置。")
            elif err_code == 2:
                raise Exception("未找到共享内存。请确保AIDA64已启动且硬件监控模块已启用共享内存功能。")
            else:
                raise ctypes.WinError(err_code)
        
        try:
            # 映射共享内存到进程地址空间
            p_buf = MapViewOfFile(h_map_file, 0x0004, 0, 0, 0)
            if not p_buf:
                raise ctypes.WinError(ctypes.get_last_error())
            
            try:
                # 读取以null结尾的完整字符串
                raw_bytes = ctypes.string_at(p_buf)
                xml_str = raw_bytes.decode("utf-8", errors="ignore")
                
                # 修复XML格式 (添加根节点)
                xml_str = f"<AIDA64>{xml_str}</AIDA64>"
                root = ET.fromstring(xml_str)
                
                # 解析传感器数据
                sensors_data = {}
                
                # 解析系统信息
                for sys_elem in root.findall('sys'):
                    id_elem = sys_elem.find('id')
                    label_elem = sys_elem.find('label')
                    value_elem = sys_elem.find('value')
                    if id_elem is not None and label_elem is not None and value_elem is not None:
                        sensors_data[id_elem.text] = {
                            'type': 'sys',
                            'label': label_elem.text,
                            'value': value_elem.text
                        }
                
                # 解析温度信息
                for temp_elem in root.findall('temp'):
                    id_elem = temp_elem.find('id')
                    label_elem = temp_elem.find('label')
                    value_elem = temp_elem.find('value')
                    if id_elem is not None and label_elem is not None and value_elem is not None:
                        sensors_data[id_elem.text] = {
                            'type': 'temp',
                            'label': label_elem.text,
                            'value': value_elem.text
                        }
                
                # 解析风扇信息
                for fan_elem in root.findall('fan'):
                    id_elem = fan_elem.find('id')
                    label_elem = fan_elem.find('label')
                    value_elem = fan_elem.find('value')
                    if id_elem is not None and label_elem is not None and value_elem is not None:
                        sensors_data[id_elem.text] = {
                            'type': 'fan',
                            'label': label_elem.text,
                            'value': value_elem.text
                        }
                
                # 解析电压信息
                for volt_elem in root.findall('volt'):
                    id_elem = volt_elem.find('id')
                    label_elem = volt_elem.find('label')
                    value_elem = volt_elem.find('value')
                    if id_elem is not None and label_elem is not None and value_elem is not None:
                        sensors_data[id_elem.text] = {
                            'type': 'volt',
                            'label': label_elem.text,
                            'value': value_elem.text
                        }
                
                # 解析功耗信息
                for pwr_elem in root.findall('pwr'):
                    id_elem = pwr_elem.find('id')
                    label_elem = pwr_elem.find('label')
                    value_elem = pwr_elem.find('value')
                    if id_elem is not None and label_elem is not None and value_elem is not None:
                        sensors_data[id_elem.text] = {
                            'type': 'pwr',
                            'label': label_elem.text,
                            'value': value_elem.text
                        }
                
                # 更新缓存
                _sensor_cache = sensors_data
                _cache_valid = True
                
                return sensors_data
                
            finally:
                UnmapViewOfFile(p_buf)
        finally:
            CloseHandle(h_map_file)
            
    except Exception as e:
        logger.error(f"读取AIDA64共享内存失败: {e}")
        _cache_valid = False
        return {}

def get_sensor_value(sensor_id: str, default_value=math.nan) -> float:
    """获取传感器数值"""
    try:
        data = read_aida64_shared_memory()
        if sensor_id in data:
            return float(data[sensor_id]['value'])
    except (ValueError, KeyError, TypeError):
        pass
    return default_value

def get_sensor_string(sensor_id: str, default_value: str = "") -> str:
    """获取传感器字符串值"""
    try:
        data = read_aida64_shared_memory()
        if sensor_id in data:
            return str(data[sensor_id]['value'])
    except (KeyError, TypeError):
        pass
    return default_value

class Cpu(sensors.Cpu):
    @staticmethod
    def percentage(interval: float) -> float:
        """CPU使用率"""
        return get_sensor_value('SCPUUTI')
    
    @staticmethod
    def frequency() -> float:
        """CPU频率 (MHz)"""
        # 尝试获取总体CPU时钟
        cpu_clock = get_sensor_value('SCPUCLK')
        if not math.isnan(cpu_clock):
            return cpu_clock
        
        # 如果没有总体时钟，计算所有核心的平均频率
        frequencies = []
        data = read_aida64_shared_memory()
        for sensor_id, sensor_data in data.items():
            if sensor_id.startswith('SCC-') and 'Clock' in sensor_data.get('label', ''):
                try:
                    freq = float(sensor_data['value'])
                    frequencies.append(freq)
                except (ValueError, TypeError):
                    continue
        
        if frequencies:
            return max(frequencies)  # 返回最高频率
        
        return math.nan
    
    @staticmethod
    def load() -> Tuple[float, float, float]:
        """系统负载 (1/5/15分钟平均值)"""
        # AIDA64不提供系统负载，使用psutil
        try:
            return psutil.getloadavg()
        except AttributeError:
            # Windows上psutil可能没有getloadavg
            cpu_percent = get_sensor_value('SCPUUTI')
            if not math.isnan(cpu_percent):
                load_val = cpu_percent / 100.0
                return (load_val, load_val, load_val)
            return (math.nan, math.nan, math.nan)
    
    @staticmethod
    def temperature() -> float:
        """CPU温度 (°C)"""
        # 优先使用CPU Package温度
        temp = get_sensor_value('TCPUPKG')
        if not math.isnan(temp):
            return temp
        
        # 其次使用CPU IA Cores温度
        temp = get_sensor_value('TCPUIAC')
        if not math.isnan(temp):
            return temp
        
        # 最后使用普通CPU温度
        return get_sensor_value('TCPU')
    
    @staticmethod
    def fan_percent(fan_name: str = None) -> float:
        """CPU风扇转速百分比"""
        # AIDA64提供的是RPM，需要转换为百分比
        # 这里假设最大转速为2000 RPM
        fan_rpm = get_sensor_value('FCPU')
        if not math.isnan(fan_rpm):
            # 简单的转换，假设最大转速2000 RPM
            return min(100.0, (fan_rpm / 2000.0) * 100.0)
        return math.nan
    
    @staticmethod
    def voltage() -> float:
        """CPU电压 (V)"""
        return get_sensor_value('VCPU')
    
    @staticmethod
    def power() -> float:
        """CPU功耗 (W)"""
        return get_sensor_value('PCPUPKG')

class Gpu(sensors.Gpu):
    @staticmethod
    def stats() -> Tuple[float, float, float, float, float]:
        """GPU统计信息: 负载(%), 已用显存(%), 已用显存(MB), 总显存(MB), 温度(°C)"""
        # GPU负载 - AIDA64可能没有直接的GPU负载，返回NaN
        load = math.nan
        
        # GPU温度
        temp = get_sensor_value('TGPU1')
        
        # 显存信息
        used_mem = get_sensor_value('SUSEDVMEM')  # MB
        free_mem = get_sensor_value('SFREEVMEM')  # MB
        
        if not math.isnan(used_mem) and not math.isnan(free_mem):
            total_mem = used_mem + free_mem
            used_percent = (used_mem / total_mem) * 100.0
            return load, used_percent, used_mem, total_mem, temp
        
        return load, math.nan, used_mem, math.nan, temp
    
    @staticmethod
    def fps() -> int:
        """FPS - AIDA64通常不提供FPS信息"""
        return -1
    
    @staticmethod
    def fan_percent() -> float:
        """GPU风扇转速百分比"""
        fan_rpm = get_sensor_value('FGPU1')
        if not math.isnan(fan_rpm):
            # 简单的转换，假设最大转速3000 RPM
            return min(100.0, (fan_rpm / 3000.0) * 100.0)
        return math.nan
    
    @staticmethod
    def frequency() -> float:
        """GPU频率 - AIDA64可能不提供GPU频率"""
        return math.nan
    
    @staticmethod
    def voltage() -> float:
        """GPU电压 (V)"""
        return get_sensor_value('VGPU1')
    
    @staticmethod
    def power() -> float:
        """GPU功耗 (W)"""
        return get_sensor_value('PGPU1')
    
    @staticmethod
    def is_available() -> bool:
        """检查GPU是否可用"""
        temp = get_sensor_value('TGPU1')
        return not math.isnan(temp)

class Memory(sensors.Memory):
    @staticmethod
    def swap_percent() -> float:
        """交换文件使用百分比"""
        # 使用虚拟内存使用率作为交换文件使用率
        return get_sensor_value('SVIRTMEMUTI')
    
    @staticmethod
    def virtual_percent() -> float:
        """虚拟内存使用百分比"""
        return get_sensor_value('SMEMUTI')
    
    @staticmethod
    def virtual_used() -> int:
        """已用内存 (字节)"""
        used_mb = get_sensor_value('SUSEDMEM')
        if not math.isnan(used_mb):
            return int(used_mb * 1024 * 1024)  # 转换为字节
        return 0
    
    @staticmethod
    def virtual_free() -> int:
        """可用内存 (字节)"""
        free_mb = get_sensor_value('SFREEMEM')
        if not math.isnan(free_mb):
            return int(free_mb * 1024 * 1024)  # 转换为字节
        return 0

class Disk(sensors.Disk):
    @staticmethod
    def disk_usage_percent() -> float:
        """磁盘使用百分比 - AIDA64不直接提供，使用psutil"""
        try:
            return psutil.disk_usage('/').percent
        except:
            return math.nan
    
    @staticmethod
    def disk_used() -> int:
        """已用磁盘空间 (字节)"""
        try:
            return psutil.disk_usage('/').used
        except:
            return 0
    
    @staticmethod
    def disk_free() -> int:
        """可用磁盘空间 (字节)"""
        try:
            return psutil.disk_usage('/').free
        except:
            return 0

class Net(sensors.Net):
    @staticmethod
    def stats(if_name, interval) -> Tuple[int, int, int, int]:
        """网络统计信息 - AIDA64不提供网络统计，使用psutil"""
        try:
            # 获取网络接口统计信息
            net_io = psutil.net_io_counters(pernic=True)
            if if_name in net_io:
                stats = net_io[if_name]
                # 简单返回累计值，速率计算需要在调用方实现
                return 0, stats.bytes_sent, 0, stats.bytes_recv
            return 0, 0, 0, 0
        except:
            return 0, 0, 0, 0

# 初始化日志
logger.info("AIDA64传感器模块已加载")

# 测试连接
try:
    test_data = read_aida64_shared_memory()
    if test_data:
        logger.info(f"成功连接到AIDA64共享内存，找到 {len(test_data)} 个传感器")
    else:
        logger.warning("无法从AIDA64共享内存读取数据")
except Exception as e:
    logger.error(f"AIDA64传感器初始化失败: {e}")