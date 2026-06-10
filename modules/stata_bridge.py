# -*- coding: utf-8 -*-
"""
Stata桥接模块 - Python调用Stata的接口
用于执行关税价格传导计算
"""

import subprocess
import re
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stata_bridge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StataBridge:
    """
    Python调用Stata的桥接类

    Attributes:
        stata_path: Stata可执行文件路径
        timeout: 超时时间(秒)
        project_root: 项目根目录
    """

    def __init__(self, stata_path: str = None, timeout: int = 30):
        """
        初始化Stata桥接器

        Args:
            stata_path: Stata可执行文件路径，默认为StataMP-64
            timeout: 命令执行超时时间(秒)，默认30秒
        """
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 优先使用传入的路径，否则从配置文件读取，否则使用默认值
        if stata_path is None:
            stata_path = self._get_stata_path_from_config()

        self.stata_path = stata_path
        self.timeout = timeout

        # 确保logs目录存在
        os.makedirs(os.path.join(self.project_root, "logs"), exist_ok=True)

        # 初始化时检查Stata是否可用
        self.stata_available = self._check_stata_availability()

        if self.stata_available:
            logger.info(f"Stata桥接器初始化成功，Stata路径: {stata_path}")
        else:
            logger.warning(f"Stata不可用，请检查安装: {stata_path}")

    def _get_stata_path_from_config(self) -> str:
        """从配置文件读取Stata路径"""
        config_path = os.path.join(self.project_root, "config.yaml")
        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    stata_config = config.get('stata', {})
                    exe = stata_config.get('executable', 'StataMP-64')
                    path = stata_config.get('path', '')
                    if path:
                        return os.path.join(path, exe)
                    return exe
        except:
            pass
        # 默认值
        return "StataMP-64"

    def _check_stata_availability(self) -> bool:
        """
        检查Stata是否可用

        Returns:
            bool: Stata是否可用
        """
        # 首先检查文件是否存在
        if os.path.isfile(self.stata_path):
            logger.info(f"Stata可执行文件存在: {self.stata_path}")
            return True

        # 如果是相对路径，尝试在PATH中查找
        if not os.path.isabs(self.stata_path):
            try:
                result = subprocess.run(
                    ["where", self.stata_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Stata在PATH中找到: {result.stdout.strip()}")
                    return True
            except:
                pass

        # 尝试一些常见的安装路径
        common_paths = [
            "C:/Program Files/Stata17/StataMP-64.exe",
            "C:/Program Files/Stata17/StataSE-64.exe",
            "C:/Program Files/Stata17/StataIC-64.exe",
            "C:/Program Files (x86)/Stata17/StataMP-64.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"在常见路径找到Stata: {path}")
                self.stata_path = path
                return True

        logger.error(f"Stata未找到: {self.stata_path}")
        return False

    def run_do_file(self, do_file: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行Stata .do文件

        Args:
            do_file: .do文件路径（相对于项目根目录）
            params: 参数字典，会被写入临时JSON文件供Stata读取

        Returns:
            dict: 执行结果，包含success、output、error等字段

        Raises:
            StataNotAvailableError: Stata不可用时抛出
            StataExecutionError: 执行出错时抛出
        """
        # 检查Stata可用性
        if not self.stata_available:
            error_msg = "Stata不可用，请先安装Stata"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "STATA_NOT_AVAILABLE"
            }

        # 构建完整路径
        do_file_path = os.path.join(self.project_root, do_file) if not os.path.isabs(do_file) else do_file

        if not os.path.exists(do_file_path):
            error_msg = f"Do文件不存在: {do_file_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "FILE_NOT_FOUND"
            }

        logger.info(f"开始执行Stata脚本: {do_file}")

        try:
            # 如果有参数，先写入临时参数文件
            if params:
                params_file = os.path.join(self.project_root, "temp_params.json")
                with open(params_file, "w", encoding="utf-8") as f:
                    json.dump(params, f, ensure_ascii=False, indent=2)
                logger.info(f"参数已写入: {params_file}")

            # 构建Stata命令
            cmd = [self.stata_path, "do", do_file_path]

            # 执行Stata
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_root
            )
            end_time = datetime.now()

            elapsed_time = (end_time - start_time).total_seconds()

            # 记录日志
            logger.info(f"Stata执行完成，耗时: {elapsed_time:.2f}秒")
            logger.debug(f"Stata输出: {result.stdout}")
            if result.stderr:
                logger.warning(f"Stata错误输出: {result.stderr}")

            # 解析输出
            parsed_output = self._parse_output(result.stdout)

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "stderr": result.stderr,
                "parsed": parsed_output,
                "elapsed_time": elapsed_time,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            error_msg = f"Stata执行超时（{self.timeout}秒）"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "TIMEOUT"
            }

        except FileNotFoundError:
            error_msg = f"Stata可执行文件未找到: {self.stata_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "STATA_NOT_FOUND"
            }

        except Exception as e:
            error_msg = f"Stata执行异常: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "EXECUTION_ERROR"
            }

    def calculate_tariff_impact(
        self,
        tariff_rate: float,
        base_price: float,
        pass_through_1: float = 0.80,
        pass_through_2: float = 0.70,
        elasticity: float = 1.0
    ) -> Dict[str, Any]:
        """
        计算关税冲击影响

        调用Stata脚本计算关税价格传导效应

        Args:
            tariff_rate: 关税税率 (0-1, 如0.25=25%)
            base_price: 基准进口价格 (元)
            pass_through_1: 进口→批发传导率
            pass_through_2: 批发→零售传导率
            elasticity: 需求弹性

        Returns:
            dict: 计算结果，包含价格变化、福利效应等
        """
        # 参数验证
        if not (0 <= tariff_rate <= 1):
            error_msg = f"关税税率必须在0-1之间，当前值: {tariff_rate}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "INVALID_TARIFF_RATE"
            }

        if base_price <= 0:
            error_msg = f"基准价格必须大于0，当前值: {base_price}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "INVALID_BASE_PRICE"
            }

        # 记录输入参数
        input_params = {
            "tariff_rate": tariff_rate,
            "base_price": base_price,
            "pass_through_1": pass_through_1,
            "pass_through_2": pass_through_2,
            "elasticity": elasticity
        }
        logger.info(f"开始计算关税冲击，输入参数: {input_params}")

        # 调用Stata执行计算
        result = self.run_do_file(
            "stata/price_transmission.do",
            params=input_params
        )

        if not result.get("success"):
            logger.error(f"Stata计算失败: {result.get('error')}")
            return result

        # 解析Stata输出
        try:
            parsed_result = self._parse_tariff_result(result["parsed"])
            parsed_result["success"] = True
            parsed_result["input_params"] = input_params
            parsed_result["elapsed_time"] = result.get("elapsed_time", 0)

            logger.info(f"关税冲击计算完成，零售价变化: {parsed_result.get('retail_price_change_rate', 0):.2f}%")
            return parsed_result

        except Exception as e:
            error_msg = f"解析Stata输出失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "PARSE_ERROR",
                "raw_output": result.get("output", "")
            }

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """
        解析Stata文本输出

        Args:
            output: Stata的文本输出

        Returns:
            dict: 解析后的数据
        """
        parsed = {}

        # 提取价格数据
        patterns = {
            "import_price_before": r"进口\s+([\d.]+)\s+([\d.]+)",
            "wholesale_price_before": r"批发\s+([\d.]+)\s+([\d.]+)",
            "retail_price_before": r"零售\s+([\d.]+)\s+([\d.]+)",
            "consumer_surplus": r"消费者剩余变化:\s+¥\s*([-\d.]+)",
            "producer_surplus": r"生产者剩余变化:\s+¥\s*([-\d.]+)",
            "government_revenue": r"政府关税收入:\s+¥\s*([-\d.]+)",
            "deadweight_loss": r"无谓损失 \(DWL\):\s+¥\s*([-\d.]+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                if key in ["import_price_before", "wholesale_price_before", "retail_price_before"]:
                    parsed[key] = float(match.group(1))
                    parsed[key.replace("before", "after")] = float(match.group(2))
                else:
                    parsed[key] = float(match.group(1))

        return parsed

    def _parse_tariff_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        将解析结果转换为标准输出格式

        Args:
            parsed: 初步解析的数据

        Returns:
            dict: 格式化后的结果
        """
        result = {
            "price_changes": {
                "import": {
                    "before": parsed.get("import_price_before", 0),
                    "after": parsed.get("import_price_after", 0),
                    "change": parsed.get("import_price_after", 0) - parsed.get("import_price_before", 0)
                },
                "wholesale": {
                    "before": parsed.get("wholesale_price_before", 0),
                    "after": parsed.get("wholesale_price_after", 0),
                    "change": parsed.get("wholesale_price_after", 0) - parsed.get("wholesale_price_before", 0)
                },
                "retail": {
                    "before": parsed.get("retail_price_before", 0),
                    "after": parsed.get("retail_price_after", 0),
                    "change": parsed.get("retail_price_after", 0) - parsed.get("retail_price_before", 0)
                }
            },
            "welfare_effects": {
                "consumer_surplus_change": parsed.get("consumer_surplus", 0),
                "producer_surplus_change": parsed.get("producer_surplus", 0),
                "government_revenue": parsed.get("government_revenue", 0),
                "deadweight_loss": parsed.get("deadweight_loss", 0)
            }
        }

        # 计算变化率
        for stage in ["import", "wholesale", "retail"]:
            before = result["price_changes"][stage]["before"]
            after = result["price_changes"][stage]["after"]
            if before > 0:
                result["price_changes"][stage]["change_rate"] = (after - before) / before * 100
            else:
                result["price_changes"][stage]["change_rate"] = 0

        return result

    def is_available(self) -> bool:
        """
        检查Stata是否可用

        Returns:
            bool: Stata是否可用
        """
        return self.stata_available


# 测试代码
if __name__ == "__main__":
    # 创建桥接器
    bridge = StataBridge(stata_path="stata-mp")

    # 检查可用性
    print(f"Stata可用: {bridge.is_available()}")

    # 测试计算
    if bridge.is_available():
        result = bridge.calculate_tariff_impact(
            tariff_rate=0.10,
            base_price=50,
            pass_through_1=0.80,
            pass_through_2=0.70
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
