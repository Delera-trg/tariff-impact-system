*===============================================================================
* 关税冲击测算模型 - price_transmission.do
* 用于计算关税从进口环节向国内各环节的传导效应
*
* 输入参数:
*   tariff_rate: 关税税率 (0-1, 如 0.25 = 25%)
*   base_price: 基准进口价格 (元)
*   pass_through_1: 进口→批发传导率 (0-1)
*   pass_through_2: 批发→零售传导率 (0-1)
*   elasticity: 需求弹性
*
* 输出:
*   - 屏幕打印计算结果
*   - price_results.dta 数据集 (可用于绘图)
*===============================================================================

clear all
set more off
set seed 12345

*===============================================================================
* 第零部分：设置工作目录
*===============================================================================
* 获取脚本所在目录的父目录（项目根目录）
local script_dir : pwd
* 切换到项目根目录
cd ".."

*===============================================================================
* 第一部分：参数设置
*===============================================================================

* 默认参数值 (可通过外部传入覆盖)
local tariff_rate = 0.10      // 关税税率 (10%)
local base_price = 50           // 基准进口价格 (元)
local pass_through_1 = 0.80    // 进口→批发传导率
local pass_through_2 = 0.70    // 批发→零售传导率
local elasticity = 1.0          // 需求弹性

* 假设的批发/零售加价率 (基于基准价格)
local wholesale_markup = 0.30  // 批发环节加价30%
local retail_markup = 0.60     // 零售环节加价60%

* 假设的需求量
local base_quantity = 1000

*===============================================================================
* 第二部分：价格计算
*===============================================================================

* 税前各环节价格
local import_price_before = `base_price'
local wholesale_price_before = `base_price' * (1 + `wholesale_markup')
local retail_price_before = `base_price' * (1 + `retail_markup')

* 税后进口价格 = 基准价格 × (1 + 关税税率)
local import_price_after = `base_price' * (1 + `tariff_rate')

* 关税增加额
local tariff_increase = `import_price_after' - `import_price_before'

* 传导后的批发价格
* 税后批发价 = 原批发价 + 关税增加额 × 传导率
local wholesale_price_after = `wholesale_price_before' + ///
    (`import_price_after' - `import_price_before') * `pass_through_1'

* 传导后的零售价格
local retail_price_after = `retail_price_before' + ///
    (`wholesale_price_after' - `wholesale_price_before') * `pass_through_2'

*===============================================================================
* 第三部分：价格变化率计算
*===============================================================================

local import_change_rate = (`import_price_after' - `import_price_before') / `import_price_before' * 100
local wholesale_change_rate = (`wholesale_price_after' - `wholesale_price_before') / `wholesale_price_before' * 100
local retail_change_rate = (`retail_price_after' - `retail_price_before') / `retail_price_before' * 100

*===============================================================================
* 第四部分：福利效应计算
*===============================================================================

* 消费者剩余变化 (简化计算: 三角形面积)
* 假设需求曲线为线性，价格上涨导致消费者剩余减少
local consumer_surplus_change = - `tariff_increase' * `base_quantity' * 0.5 * (1 + `elasticity')

* 政府关税收入 = 关税 × 进口数量
local government_revenue = `tariff_increase' * `base_quantity'

* 生产者剩余变化 (假设生产者承担部分关税成本)
local producer_surplus_change = - `tariff_increase' * `base_quantity' * 0.3

* 无谓损失 (Deadweight Loss)
* 由于关税导致的市场扭曲造成的效率损失
local deadweight_loss = `tariff_increase' * `base_quantity' * `tariff_rate' * 0.5

* 总福利变化 = 消费者剩余变化 + 生产者剩余变化 + 政府收入
local total_welfare_change = `consumer_surplus_change' + `producer_surplus_change' + `government_revenue'

*===============================================================================
* 第五部分：输出结果到屏幕
*===============================================================================

clear
display ""
display "================================================================================"
display "                  关税冲击测算结果 - 价格传导模型"
display "================================================================================"
display ""
display "【输入参数】"
display "  关税税率: " %4.2f `tariff_rate' * 100 "%"
display "  基准进口价格: ¥" `base_price'
display "  进口→批发传导率: " %4.2f `pass_through_1'
display "  批发→零售传导率: " %4.2f `pass_through_2'
display "  需求弹性: " %4.2f `elasticity'
display ""
display "================================================================================"
display "【价格变化】"
display "--------------------------------------------------------------------------------"
display "环节          税前价格      税后价格      变化额       变化率"
display "--------------------------------------------------------------------------------"
display "进口         " %9.2f `import_price_before' "   " %9.2f `import_price_after' "   " %9.2f (`import_price_after'-`import_price_before') "    " %6.2f `import_change_rate' "%"
display "批发         " %9.2f `wholesale_price_before' "   " %9.2f `wholesale_price_after' "   " %9.2f (`wholesale_price_after'-`wholesale_price_before') "    " %6.2f `wholesale_change_rate' "%"
display "零售         " %9.2f `retail_price_before' "   " %9.2f `retail_price_after' "   " %9.2f (`retail_price_after'-`retail_price_before') "    " %6.2f `retail_change_rate' "%"
display "--------------------------------------------------------------------------------"
display ""
display "================================================================================"
display "【福利效应分析】"
display "--------------------------------------------------------------------------------"
display "消费者剩余变化:     ¥" %12.2f `consumer_surplus_change'
display "生产者剩余变化:     ¥" %12.2f `producer_surplus_change'
display "政府关税收入:       ¥" %12.2f `government_revenue'
display "无谓损失 (DWL):     ¥" %12.2f `deadweight_loss'
display "--------------------------------------------------------------------------------"
display "总福利变化:         ¥" %12.2f `total_welfare_change'
display "================================================================================"
display ""
display "【传导路径示意】"
display ""
display "   进口:  ¥" `base_price' "  --(+关税" %3.0f `tariff_rate'*100 "%)-->  ¥" `import_price_after'
display "     |"
display "     | 传导率 " %3.0f `pass_through_1'*100 "%"
display "     v"
display "   批发:  ¥" `wholesale_price_before' "  ---------------->  ¥" `wholesale_price_after'
display "     |"
display "     | 传导率 " %3.0f `pass_through_2'*100 "%"
display "     v"
display "   零售:  ¥" `retail_price_before' "  ---------------->  ¥" `retail_price_after'
display ""
display "================================================================================"

*===============================================================================
* 第六部分：生成数据集 (用于绘图)
*===============================================================================

* 方法1: 创建价格对比数据集
clear
set obs 3
gen stage = ""
gen price_before = .
gen price_after = .
gen change_rate = .

replace stage = "进口" in 1
replace price_before = `import_price_before' in 1
replace price_after = `import_price_after' in 1
replace change_rate = `import_change_rate' in 1

replace stage = "批发" in 2
replace price_before = `wholesale_price_before' in 2
replace price_after = `wholesale_price_after' in 2
replace change_rate = `wholesale_change_rate' in 2

replace stage = "零售" in 3
replace price_before = `retail_price_before' in 3
replace price_after = `retail_price_after' in 3
replace change_rate = `retail_change_rate' in 3

* 添加关税传导路径数据
gen tariff_rate = `tariff_rate'
gen base_price = `base_price'
gen pass_through_1 = `pass_through_1'
gen pass_through_2 = `pass_through_2'

* 保存数据集
save "data/price_results.dta", replace

* 方法2: 创建敏感性分析数据集 (不同关税税率下的价格)
clear

* 首先定义变量结构
gen tariff_rate = .
gen import_price = .
gen wholesale_price = .
gen retail_price = .

* 设置观察数 (0%, 5%, 10%, ..., 50%)
set obs 11

* 生成关税税率序列
replace tariff_rate = 0 in 1
replace tariff_rate = 0.05 in 2
replace tariff_rate = 0.10 in 3
replace tariff_rate = 0.15 in 4
replace tariff_rate = 0.20 in 5
replace tariff_rate = 0.25 in 6
replace tariff_rate = 0.30 in 7
replace tariff_rate = 0.35 in 8
replace tariff_rate = 0.40 in 9
replace tariff_rate = 0.45 in 10
replace tariff_rate = 0.50 in 11

* 计算各环节价格
replace import_price = `base_price' * (1 + tariff_rate)
replace wholesale_price = `wholesale_price_before' + (import_price - `base_price') * `pass_through_1'
replace retail_price = `retail_price_before' + (wholesale_price - `wholesale_price_before') * `pass_through_2'

* 添加基础参数
gen base_price = `base_price'
gen pass_through_1 = `pass_through_1'
gen pass_through_2 = `pass_through_2'

save "data/sensitivity_analysis.dta", replace

* 返回主数据集
clear
use "data/price_results.dta"

display ""
display "[数据集已保存]"
display "  - data/price_results.dta (价格对比数据)"
display "  - data/sensitivity_analysis.dta (敏感性分析数据)"
display ""

*===============================================================================
* 使用说明
*===============================================================================
*
* 运行方式:
*   do price_transmission.do
*
* 自定义参数:
*   local tariff_rate = 0.25    // 设置关税税率为25%
*   local base_price = 100      // 设置基准价格为100元
*   do price_transmission.do
*
*===============================================================================
