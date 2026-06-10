# -*- coding: utf-8 -*-
"""
数据库管理模块 - SQLite数据库操作
用于管理行业数据、关税税率、用户配置等
"""

import sqlite3
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "industries.db")


class DatabaseManager:
    """
    数据库管理类

    Attributes:
        db_path: 数据库文件路径
    """

    def __init__(self, db_path: str = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认使用项目配置
        """
        self.db_path = db_path or DB_PATH
        self._ensure_database()

    def _ensure_database(self):
        """确保数据库存在"""
        if not os.path.exists(self.db_path):
            # 如果数据库不存在，尝试运行初始化脚本
            init_script = os.path.join(PROJECT_ROOT, "init_db.py")
            if os.path.exists(init_script):
                import subprocess
                subprocess.run(["python", init_script], cwd=PROJECT_ROOT)

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接

        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        return conn

    # =========================================================================
    # 行业数据操作
    # =========================================================================

    def get_industry_list(self, category: str = None) -> List[Dict[str, Any]]:
        """
        获取行业列表

        Args:
            category: 可选，按大类筛选

        Returns:
            list: 行业列表，每项包含HS编码、名称、分类
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if category:
                cursor.execute("""
                    SELECT id, hs_code, name, category, sub_category, unit
                    FROM industries
                    WHERE category = ?
                    ORDER BY hs_code
                """, (category,))
            else:
                cursor.execute("""
                    SELECT id, hs_code, name, category, sub_category, unit
                    FROM industries
                    ORDER BY hs_code
                """)

            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "hs_code": row["hs_code"],
                    "name": row["name"],
                    "category": row["category"],
                    "sub_category": row["sub_category"],
                    "unit": row["unit"]
                })

            return result

        finally:
            conn.close()

    def get_industry_by_hs(self, hs_code: str) -> Optional[Dict[str, Any]]:
        """
        根据HS编码获取行业信息

        Args:
            hs_code: HS编码

        Returns:
            dict: 行业信息，不存在返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM industries
                WHERE hs_code = ?
            """, (hs_code,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    def get_industry_detail(self, industry_id: int = None, hs_code: str = None) -> Optional[Dict[str, Any]]:
        """
        获取行业详细信息，包含价格和税率

        Args:
            industry_id: 行业ID
            hs_code: HS编码（与id二选一）

        Returns:
            dict: 包含基准价格和当前税率的详细信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 获取行业基本信息
            if industry_id:
                cursor.execute("SELECT * FROM industries WHERE id = ?", (industry_id,))
            elif hs_code:
                cursor.execute("SELECT * FROM industries WHERE hs_code = ?", (hs_code,))
            else:
                raise ValueError("必须提供industry_id或hs_code")

            industry = cursor.fetchone()
            if not industry:
                return None

            industry_dict = dict(industry)

            # 获取当前关税税率
            cursor.execute("""
                SELECT current_rate, mfn_rate, preferential_rate
                FROM tariff_rates
                WHERE hs_code = ? AND year = 2024
                ORDER BY year DESC
                LIMIT 1
            """, (industry_dict["hs_code"],))

            tariff = cursor.fetchone()
            if tariff:
                industry_dict["current_tariff_rate"] = tariff["current_rate"] / 100  # 转为小数
                industry_dict["mfn_rate"] = tariff["mfn_rate"] / 100
                industry_dict["preferential_rate"] = tariff["preferential_rate"] / 100 if tariff["preferential_rate"] else None
            else:
                industry_dict["current_tariff_rate"] = 0

            # 获取传导参数
            cursor.execute("""
                SELECT stage, pass_through_rate, elasticity, time_lag_months
                FROM transmission_params
                WHERE hs_code = ?
            """, (industry_dict["hs_code"],))

            params = cursor.fetchall()
            transmission_params = {}
            for param in params:
                transmission_params[param["stage"]] = {
                    "pass_through_rate": param["pass_through_rate"],
                    "elasticity": param["elasticity"],
                    "time_lag_months": param["time_lag_months"]
                }

            industry_dict["transmission_params"] = transmission_params

            return industry_dict

        finally:
            conn.close()

    def get_categories(self) -> List[str]:
        """
        获取所有行业分类

        Returns:
            list: 分类列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT category
                FROM industries
                ORDER BY category
            """)
            return [row["category"] for row in cursor.fetchall()]

        finally:
            conn.close()

    # =========================================================================
    # 关税税率操作
    # =========================================================================

    def get_tariff_rate(self, hs_code: str, year: int = 2024) -> Optional[Dict[str, Any]]:
        """
        查询关税税率

        Args:
            hs_code: HS编码
            year: 年份，默认2024

        Returns:
            dict: 税率信息，包含最惠国税率、优惠税率、当前税率
        """
        # 验证HS编码格式
        if not self._validate_hs_code(hs_code):
            raise ValueError(f"无效的HS编码格式: {hs_code}")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT *
                FROM tariff_rates
                WHERE hs_code = ? AND year = ?
            """, (hs_code, year))

            row = cursor.fetchone()
            if row:
                return {
                    "hs_code": row["hs_code"],
                    "year": row["year"],
                    "mfn_rate": row["mfn_rate"] / 100,
                    "preferential_rate": row["preferential_rate"] / 100 if row["preferential_rate"] else None,
                    "current_rate": row["current_rate"] / 100,
                    "notes": row["notes"]
                }
            return None

        finally:
            conn.close()

    def get_tariff_history(self, hs_code: str) -> List[Dict[str, Any]]:
        """
        查询历史关税税率

        Args:
            hs_code: HS编码

        Returns:
            list: 历史税率列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT year, mfn_rate, current_rate, notes
                FROM tariff_rates
                WHERE hs_code = ?
                ORDER BY year DESC
            """, (hs_code,))

            return [
                {
                    "year": row["year"],
                    "mfn_rate": row["mfn_rate"] / 100,
                    "current_rate": row["current_rate"] / 100,
                    "notes": row["notes"]
                }
                for row in cursor.fetchall()
            ]

        finally:
            conn.close()

    # =========================================================================
    # 用户配置操作
    # =========================================================================

    def save_user_config(
        self,
        session_id: str,
        industry_id: str,
        tariff_rate: float,
        custom_params: dict = None,
        result_data: dict = None
    ) -> int:
        """
        保存用户配置和计算结果

        Args:
            session_id: 会话ID
            industry_id: 行业ID
            tariff_rate: 关税税率
            custom_params: 自定义参数
            result_data: 计算结果

        Returns:
            int: 保存的记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO user_configs
                (session_id, industry_id, tariff_rate, custom_params, result_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                industry_id,
                tariff_rate,
                json.dumps(custom_params, ensure_ascii=False) if custom_params else None,
                json.dumps(result_data, ensure_ascii=False) if result_data else None,
                datetime.now().isoformat()
            ))

            conn.commit()
            return cursor.lastrowid

        finally:
            conn.close()

    def get_user_configs(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户的历史配置

        Args:
            session_id: 会话ID
            limit: 返回数量限制

        Returns:
            list: 配置列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM user_configs
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, limit))

            results = []
            for row in cursor.fetchall():
                item = {
                    "id": row["id"],
                    "industry_id": row["industry_id"],
                    "tariff_rate": row["tariff_rate"],
                    "created_at": row["created_at"]
                }

                # 解析JSON字段
                if row["custom_params"]:
                    item["custom_params"] = json.loads(row["custom_params"])
                if row["result_data"]:
                    item["result_data"] = json.loads(row["result_data"])

                results.append(item)

            return results

        finally:
            conn.close()

    # =========================================================================
    # 数据验证
    # =========================================================================

    def _validate_hs_code(self, hs_code: str) -> bool:
        """
        验证HS编码格式

        Args:
            hs_code: HS编码

        Returns:
            bool: 是否有效
        """
        # 简单验证：数字和点号的组合
        pattern = r'^\d{2,6}(\.\d{2,4})?$'
        return bool(re.match(pattern, hs_code))

    def validate_tariff_rate(self, rate: float) -> Tuple[bool, str]:
        """
        验证关税税率

        Args:
            rate: 税率（0-1或0-100）

        Returns:
            tuple: (是否有效, 错误信息)
        """
        if rate < 0:
            return False, "税率不能为负数"

        # 自动识别是百分比还是小数
        if rate > 1:
            rate = rate / 100

        if rate > 1:
            return False, "税率不能超过100%"

        return True, ""

    def validate_price(self, price: float) -> Tuple[bool, str]:
        """
        验证价格

        Args:
            price: 价格

        Returns:
            tuple: (是否有效, 错误信息)
        """
        if price < 0:
            return False, "价格不能为负数"

        if price > 1e10:
            return False, "价格超出合理范围"

        return True, ""

    # =========================================================================
    # 历史记录操作
    # =========================================================================

    def save_calculation_history(self, result: Dict[str, Any], session_id: str = "default") -> int:
        """
        保存计算历史记录

        Args:
            result: 计算结果
            session_id: 会话ID

        Returns:
            int: 记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 创建历史记录表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    hs_code TEXT NOT NULL,
                    industry_name TEXT,
                    category TEXT,
                    tariff_rate REAL,
                    base_price REAL,
                    pass_through_1 REAL,
                    pass_through_2 REAL,
                    elasticity REAL,
                    import_before REAL,
                    import_after REAL,
                    wholesale_before REAL,
                    wholesale_after REAL,
                    retail_before REAL,
                    retail_after REAL,
                    consumer_surplus REAL,
                    producer_surplus REAL,
                    government_revenue REAL,
                    deadweight_loss REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 提取数据
            industry = result.get("industry", {})
            params = result.get("params", {})
            price = result.get("price_changes", {})
            welfare = result.get("welfare_effects", {})

            cursor.execute("""
                INSERT INTO calculation_history (
                    session_id, hs_code, industry_name, category,
                    tariff_rate, base_price, pass_through_1, pass_through_2, elasticity,
                    import_before, import_after, wholesale_before, wholesale_after,
                    retail_before, retail_after,
                    consumer_surplus, producer_surplus, government_revenue, deadweight_loss
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                industry.get("hs_code", ""),
                industry.get("name", ""),
                industry.get("category", ""),
                params.get("tariff_rate", 0),
                params.get("base_price", 0),
                params.get("pass_through_1", 0),
                params.get("pass_through_2", 0),
                params.get("elasticity", 0),
                price.get("import", {}).get("before", 0),
                price.get("import", {}).get("after", 0),
                price.get("wholesale", {}).get("before", 0),
                price.get("wholesale", {}).get("after", 0),
                price.get("retail", {}).get("before", 0),
                price.get("retail", {}).get("after", 0),
                welfare.get("consumer_surplus_change", 0),
                welfare.get("producer_surplus_change", 0),
                welfare.get("government_revenue", 0),
                welfare.get("deadweight_loss", 0)
            ))

            conn.commit()
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            print(f"保存历史记录失败: {e}")
            return -1
        finally:
            conn.close()

    def get_calculation_history(self, session_id: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取计算历史记录

        Args:
            session_id: 会话ID
            limit: 返回记录数量

        Returns:
            list: 历史记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM calculation_history
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return []
        finally:
            conn.close()

    def delete_calculation_history(self, record_id: int, session_id: str = "default") -> bool:
        """
        删除指定历史记录

        Args:
            record_id: 记录ID
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM calculation_history
                WHERE id = ? AND session_id = ?
            """, (record_id, session_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"删除历史记录失败: {e}")
            return False
        finally:
            conn.close()

    def clear_calculation_history(self, session_id: str = "default") -> bool:
        """
        清空指定会话的所有历史记录

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否清空成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM calculation_history
                WHERE session_id = ?
            """, (session_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"清空历史记录失败: {e}")
            return False
        finally:
            conn.close()

    # =========================================================================
    # 工具方法
    # =========================================================================

    def close(self):
        """关闭数据库连接（实际上SQLite不需要显式关闭）"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 测试代码
if __name__ == "__main__":
    db = DatabaseManager()

    # 测试获取行业列表
    print("=== 行业列表 ===")
    industries = db.get_industry_list()
    for ind in industries[:3]:
        print(f"{ind['hs_code']} - {ind['name']} ({ind['category']})")

    # 测试获取行业详情
    print("\n=== 行业详情 ===")
    detail = db.get_industry_detail(hs_code="0101.10")
    if detail:
        print(f"名称: {detail['name']}")
        print(f"基准进口价: {detail['base_price']}")
        print(f"当前税率: {detail.get('current_tariff_rate', 0)}")

    # 测试关税税率
    print("\n=== 关税税率 ===")
    tariff = db.get_tariff_rate("1201.90", 2024)
    if tariff:
        print(f"最惠国税率: {tariff['mfn_rate']*100}%")
        print(f"当前税率: {tariff['current_rate']*100}%")

    # 测试数据验证
    print("\n=== 数据验证 ===")
    valid, msg = db.validate_tariff_rate(0.25)
    print(f"税率验证(0.25): {valid}, {msg}")

    valid, msg = db.validate_tariff_rate(1.5)
    print(f"税率验证(1.5): {valid}, {msg}")
