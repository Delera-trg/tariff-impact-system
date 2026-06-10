# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建SQLite数据库和表结构
"""

import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = "data/industries.db"

def init_database():
    """初始化数据库"""

    # 确保data目录存在
    os.makedirs("data", exist_ok=True)

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"正在创建数据库: {DB_PATH}")

    # ========== 创建行业/商品表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL UNIQUE,
            hs_code_full TEXT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            sub_category TEXT,
            unit TEXT NOT NULL,
            base_price REAL DEFAULT 0,
            wholesale_price REAL DEFAULT 0,
            retail_price REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Table industries created")

    # ========== 创建关税税率表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tariff_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            mfn_rate REAL NOT NULL,
            preferential_rate REAL,
            current_rate REAL NOT NULL,
            tariff_quota REAL,
            notes TEXT,
            source TEXT DEFAULT '海关总署',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, year)
        )
    """)
    print("[OK] Table tariff_rates created")

    # ========== 创建传导参数表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transmission_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL,
            stage TEXT NOT NULL,
            pass_through_rate REAL DEFAULT 0.8,
            elasticity REAL DEFAULT 1.0,
            time_lag_months INTEGER DEFAULT 0,
            data_source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, stage)
        )
    """)
    print("[OK] Table transmission_params created")

    # ========== 创建用户配置表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            industry_id TEXT NOT NULL,
            tariff_rate REAL NOT NULL,
            custom_params TEXT,
            result_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Table user_configs created")

    # ========== 插入示例数据 ==========
    insert_sample_data(cursor)

    # 提交并关闭
    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print("数据库初始化完成!")
    print("="*50)


def insert_sample_data(cursor):
    """插入示例数据"""

    # 示例行业数据
    industries = [
        ("0101.10", "01011000", "活动物", "第一类 动物产品", "种马", "头", 8000, 9500, 12000),
        ("0101.90", "01019000", "其他马", "第一类 动物产品", "非种用马", "头", 5000, 6500, 8500),
        ("0102.90", "01029000", "其他牛", "第一类 动物产品", "非种用牛", "头", 4500, 5800, 7500),
        ("0201.00", "02010000", "肉及食用杂碎", "第二类 肉及食用杂碎", "鲜或冷藏牛肉", "千克", 45, 55, 70),
        ("0202.00", "02020000", "冻牛肉", "第二类 肉及食用杂碎", "冻牛肉", "千克", 38, 48, 62),
        ("1201.90", "12019000", "大豆", "第五类 植物产品", "黄大豆", "吨", 3500, 4200, 5000),
        ("8703.23", "87032300", "小汽车", "第十七类 车辆", "排量1.5-2.5L", "辆", 180000, 220000, 280000),
        ("8703.33", "87033300", "越野车", "第十七类 车辆", "排量2.5-3.0L", "辆", 350000, 420000, 520000),
        ("3303.00", "33030000", "香水", "第三十三类 化妆品", "香水", "千克", 300, 450, 650),
        ("3304.99", "33049900", "美容品", "第三十三类 化妆品", "其他美容品", "千克", 150, 250, 380),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO industries
        (hs_code, hs_code_full, name, category, sub_category, unit, base_price, wholesale_price, retail_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, industries)
    print(f"[OK] Inserted {len(industries)} industry records")

    # 示例关税税率数据
    tariff_rates = [
        ("0101.10", 2024, 10, 0, 10, "中国-新西兰自贸区"),
        ("0101.90", 2024, 10, 0, 10, "中国-澳大利亚自贸区"),
        ("0102.90", 2024, 10, 0, 10, "最惠国"),
        ("0201.00", 2024, 20, 12, 20, "最惠国"),
        ("0202.00", 2024, 20, 12, 20, "最惠国"),
        ("1201.90", 2024, 3, 0, 3, "最惠国"),
        ("8703.23", 2024, 25, 15, 25, "整车进口关税"),
        ("8703.33", 2024, 25, 15, 25, "整车进口关税"),
        ("3303.00", 2024, 10, 5, 10, "最惠国"),
        ("3304.99", 2024, 5, 0, 5, "最惠国"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO tariff_rates
        (hs_code, year, mfn_rate, preferential_rate, current_rate, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, tariff_rates)
    print(f"[OK] Inserted {len(tariff_rates)} tariff rate records")

    # 示例传导参数
    transmission_params = [
        ("0101.10", "import_to_wholesale", 0.85, 0.9, 1, "行业平均"),
        ("0101.10", "wholesale_to_retail", 0.75, 1.2, 0, "行业平均"),
        ("1201.90", "import_to_wholesale", 0.90, 0.5, 1, "大豆市场特点"),
        ("1201.90", "wholesale_to_retail", 0.80, 0.6, 0, "大豆市场特点"),
        ("8703.23", "import_to_wholesale", 0.70, 1.5, 2, "汽车市场"),
        ("8703.23", "wholesale_to_retail", 0.60, 1.8, 1, "汽车市场"),
        ("3303.00", "import_to_wholesale", 0.95, 2.0, 0, "化妆品高端"),
        ("3303.00", "wholesale_to_retail", 0.85, 2.5, 0, "化妆品高端"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO transmission_params
        (hs_code, stage, pass_through_rate, elasticity, time_lag_months, data_source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, transmission_params)
    print(f"[OK] Inserted {len(transmission_params)} transmission param records")


if __name__ == "__main__":
    init_database()
