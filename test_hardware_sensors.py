#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件传感器信息测试脚本
用于探索LibreHardwareMonitor能够获取到的各类硬件设备和传感器信息
"""

import sys
import os

# 添加library路径到sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'library'))

try:
    import clr
    clr.AddReference(os.path.join(os.path.dirname(__file__), 'external', 'LibreHardwareMonitor', 'LibreHardwareMonitorLib.dll'))
    from LibreHardwareMonitor import Hardware
except Exception as e:
    print(f"无法加载LibreHardwareMonitor库: {e}")
    print("请确保LibreHardwareMonitorLib.dll文件存在于external/LibreHardwareMonitor/目录中")
    sys.exit(1)

def explore_hardware_sensors():
    """
    探索所有可用的硬件设备和传感器
    """
    print("=" * 80)
    print("LibreHardwareMonitor 硬件传感器信息探索")
    print("=" * 80)
    
    # 初始化硬件监控
    computer = Hardware.Computer()
    computer.IsCpuEnabled = True
    computer.IsGpuEnabled = True
    computer.IsMemoryEnabled = True
    computer.IsMotherboardEnabled = True
    computer.IsControllerEnabled = True
    computer.IsNetworkEnabled = True
    computer.IsStorageEnabled = True
    computer.Open()
    
    try:
        # 遍历所有硬件设备
        for i, hardware in enumerate(computer.Hardware):
            print(f"\n硬件设备 #{i+1}:")
            print(f"  名称: {hardware.Name}")
            print(f"  类型: {hardware.HardwareType}")
            print(f"  标识符: {hardware.Identifier}")
            
            # 更新硬件信息
            hardware.Update()
            
            # 遍历所有传感器
            if hardware.Sensors:
                print(f"  传感器数量: {len(hardware.Sensors)}")
                print("  传感器详情:")
                
                # 按传感器类型分组
                sensor_groups = {}
                for sensor in hardware.Sensors:
                    sensor_type = str(sensor.SensorType)
                    if sensor_type not in sensor_groups:
                        sensor_groups[sensor_type] = []
                    sensor_groups[sensor_type].append(sensor)
                
                # 显示每种类型的传感器
                for sensor_type, sensors in sensor_groups.items():
                    print(f"    {sensor_type} ({len(sensors)}个):")
                    for sensor in sensors:
                        value = sensor.Value if sensor.Value is not None else "N/A"
                        unit = ""
                        if sensor_type == "Temperature":
                            unit = "°C"
                        elif sensor_type == "Voltage":
                            unit = "V"
                        elif sensor_type == "Power":
                            unit = "W"
                        elif sensor_type == "Fan":
                            unit = "RPM"
                        elif sensor_type == "Clock":
                            unit = "MHz"
                        elif sensor_type == "Load":
                            unit = "%"
                        elif sensor_type == "Data":
                            unit = "GB"
                        elif sensor_type == "SmallData":
                            unit = "MB"
                        elif sensor_type == "Throughput":
                            unit = "MB/s"
                        
                        print(f"      - {sensor.Name}: {value} {unit}")
                        print(f"        标识符: {sensor.Identifier}")
                        if sensor.Min is not None:
                            print(f"        最小值: {sensor.Min} {unit}")
                        if sensor.Max is not None:
                            print(f"        最大值: {sensor.Max} {unit}")
            else:
                print("  无可用传感器")
            
            # 遍历子硬件（如果有）
            if hardware.SubHardware:
                print(f"  子硬件数量: {len(hardware.SubHardware)}")
                for j, sub_hardware in enumerate(hardware.SubHardware):
                    print(f"    子硬件 #{j+1}:")
                    print(f"      名称: {sub_hardware.Name}")
                    print(f"      类型: {sub_hardware.HardwareType}")
                    print(f"      标识符: {sub_hardware.Identifier}")
                    
                    sub_hardware.Update()
                    if sub_hardware.Sensors:
                        print(f"      传感器数量: {len(sub_hardware.Sensors)}")
                        for sensor in sub_hardware.Sensors:
                            value = sensor.Value if sensor.Value is not None else "N/A"
                            print(f"        - {sensor.Name} ({sensor.SensorType}): {value}")
            
            print("-" * 60)
    
    finally:
        computer.Close()
    
    print("\n探索完成！")

def test_gpu_voltage_power():
    """
    专门测试GPU电压和功耗传感器
    """
    print("\n" + "=" * 80)
    print("GPU 电压和功耗传感器专项测试")
    print("=" * 80)
    
    computer = Hardware.Computer()
    computer.IsGpuEnabled = True
    computer.Open()
    
    try:
        gpu_found = False
        for hardware in computer.Hardware:
            if hardware.HardwareType == Hardware.HardwareType.GpuNvidia or \
               hardware.HardwareType == Hardware.HardwareType.GpuAmd or \
               hardware.HardwareType == Hardware.HardwareType.GpuIntel:
                
                gpu_found = True
                print(f"\nGPU设备: {hardware.Name} ({hardware.HardwareType})")
                hardware.Update()
                
                voltage_sensors = []
                power_sensors = []
                
                for sensor in hardware.Sensors:
                    if sensor.SensorType == Hardware.SensorType.Voltage:
                        voltage_sensors.append(sensor)
                    elif sensor.SensorType == Hardware.SensorType.Power:
                        power_sensors.append(sensor)
                
                print(f"\n电压传感器 ({len(voltage_sensors)}个):")
                if voltage_sensors:
                    for sensor in voltage_sensors:
                        value = sensor.Value if sensor.Value is not None else "N/A"
                        print(f"  - {sensor.Name}: {value} V")
                        print(f"    标识符: {sensor.Identifier}")
                else:
                    print("  未找到电压传感器")
                
                print(f"\n功耗传感器 ({len(power_sensors)}个):")
                if power_sensors:
                    for sensor in power_sensors:
                        value = sensor.Value if sensor.Value is not None else "N/A"
                        print(f"  - {sensor.Name}: {value} W")
                        print(f"    标识符: {sensor.Identifier}")
                else:
                    print("  未找到功耗传感器")
                
                # 检查子硬件
                for sub_hardware in hardware.SubHardware:
                    print(f"\n子硬件: {sub_hardware.Name}")
                    sub_hardware.Update()
                    
                    sub_voltage_sensors = []
                    sub_power_sensors = []
                    
                    for sensor in sub_hardware.Sensors:
                        if sensor.SensorType == Hardware.SensorType.Voltage:
                            sub_voltage_sensors.append(sensor)
                        elif sensor.SensorType == Hardware.SensorType.Power:
                            sub_power_sensors.append(sensor)
                    
                    if sub_voltage_sensors:
                        print("  电压传感器:")
                        for sensor in sub_voltage_sensors:
                            value = sensor.Value if sensor.Value is not None else "N/A"
                            print(f"    - {sensor.Name}: {value} V ({sensor.Identifier})")
                    
                    if sub_power_sensors:
                        print("  功耗传感器:")
                        for sensor in sub_power_sensors:
                            value = sensor.Value if sensor.Value is not None else "N/A"
                            print(f"    - {sensor.Name}: {value} W ({sensor.Identifier})")
        
        if not gpu_found:
            print("未找到GPU设备")
    
    finally:
        computer.Close()

def generate_sensor_mapping():
    """
    生成传感器映射建议
    """
    print("\n" + "=" * 80)
    print("传感器映射建议")
    print("=" * 80)
    
    computer = Hardware.Computer()
    computer.IsGpuEnabled = True
    computer.Open()
    
    try:
        for hardware in computer.Hardware:
            if hardware.HardwareType == Hardware.HardwareType.GpuNvidia or \
               hardware.HardwareType == Hardware.HardwareType.GpuAmd or \
               hardware.HardwareType == Hardware.HardwareType.GpuIntel:
                
                print(f"\n{hardware.Name} 传感器映射建议:")
                hardware.Update()
                
                # 查找第一个电压和功耗传感器
                voltage_sensor = None
                power_sensor = None
                
                for sensor in hardware.Sensors:
                    if sensor.SensorType == Hardware.SensorType.Voltage and voltage_sensor is None:
                        voltage_sensor = sensor
                    elif sensor.SensorType == Hardware.SensorType.Power and power_sensor is None:
                        power_sensor = sensor
                
                # 检查子硬件
                for sub_hardware in hardware.SubHardware:
                    sub_hardware.Update()
                    for sensor in sub_hardware.Sensors:
                        if sensor.SensorType == Hardware.SensorType.Voltage and voltage_sensor is None:
                            voltage_sensor = sensor
                        elif sensor.SensorType == Hardware.SensorType.Power and power_sensor is None:
                            power_sensor = sensor
                
                print("\n建议的代码实现:")
                print("```python")
                print("def voltage(self) -> float:")
                if voltage_sensor:
                    print(f'    """获取GPU电压 - 使用传感器: {voltage_sensor.Name}"""')
                    print(f"    hw = get_hw_and_update(Hardware.HardwareType.{hardware.HardwareType})")
                    print("    if hw:")
                    print("        for sensor in hw.Sensors:")
                    print(f'            if sensor.Name == "{voltage_sensor.Name}" and sensor.SensorType == Hardware.SensorType.Voltage:')
                    print("                return float(sensor.Value) if sensor.Value else math.nan")
                    print("    return math.nan")
                else:
                    print('    """获取GPU电压 - 未找到合适的传感器"""')
                    print("    return math.nan")
                
                print("\ndef power(self) -> float:")
                if power_sensor:
                    print(f'    """获取GPU功耗 - 使用传感器: {power_sensor.Name}"""')
                    print(f"    hw = get_hw_and_update(Hardware.HardwareType.{hardware.HardwareType})")
                    print("    if hw:")
                    print("        for sensor in hw.Sensors:")
                    print(f'            if sensor.Name == "{power_sensor.Name}" and sensor.SensorType == Hardware.SensorType.Power:')
                    print("                return float(sensor.Value) if sensor.Value else math.nan")
                    print("    return math.nan")
                else:
                    print('    """获取GPU功耗 - 未找到合适的传感器"""')
                    print("    return math.nan")
                print("```")
    
    finally:
        computer.Close()

if __name__ == "__main__":
    print("LibreHardwareMonitor 硬件传感器探索工具")
    print("请选择要执行的操作:")
    print("1. 探索所有硬件设备和传感器")
    print("2. 专项测试GPU电压和功耗传感器")
    print("3. 生成传感器映射建议")
    print("4. 执行全部测试")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            explore_hardware_sensors()
        elif choice == "2":
            test_gpu_voltage_power()
        elif choice == "3":
            generate_sensor_mapping()
        elif choice == "4":
            explore_hardware_sensors()
            test_gpu_voltage_power()
            generate_sensor_mapping()
        else:
            print("无效选择，执行全部测试...")
            explore_hardware_sensors()
            test_gpu_voltage_power()
            generate_sensor_mapping()
    
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()