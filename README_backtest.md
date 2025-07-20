# 通达信选股公式回测系统使用指南

## 系统介绍
这个Python回测系统可以帮您测试底部吸筹启动选股策略的历史表现，验证公式的有效性。

## 安装依赖

首先确保您安装了Python 3.7以上版本，然后安装所需的库：

```bash
pip install pandas numpy akshare
```

## 快速使用

### 1. 基础运行
直接运行脚本：
```bash
python backtest_tdx_formula.py
```

### 2. 自定义股票列表测试
如果您想测试特定的股票：

```python
# 在main()函数中修改
stock_list = ['000001', '000002', '600036', '600519', '002415']
results = backtest.run_backtest(stock_list, hold_days=10)
```

### 3. 调整回测参数

```python
# 修改测试时间段
backtest = TDXBacktest(start_date='20230101', end_date='20241231')

# 修改持股天数
results = backtest.run_backtest(hold_days=15)
```

## 回测结果解读

### 关键指标说明：

- **胜率**: 盈利交易次数 / 总交易次数
- **平均收益率**: 所有交易的平均收益
- **大涨股票比例**: 收益>8%的股票比例
- **最高涨幅**: 持有期间的最高收益

### 成功标准：
- 🏆 **优秀**: 胜率>65%, 平均收益>8%
- ✅ **合格**: 胜率>50%, 平均收益>3%
- ❌ **不合格**: 胜率<45%, 长期收益为负

## 快速测试不同策略

### 测试1：激进策略（5日持股）
```python
results = backtest.run_backtest(hold_days=5)
```

### 测试2：稳健策略（20日持股）
```python
results = backtest.run_backtest(hold_days=20)
```

### 测试3：不同时间段
```python
# 测试牛市表现
backtest_bull = TDXBacktest(start_date='20230101', end_date='20231231')

# 测试熊市表现
backtest_bear = TDXBacktest(start_date='20220101', end_date='20221231')
```

## 输出文件

运行后会生成：
- 控制台统计报告
- CSV详细数据文件（包含每笔交易记录）
- TOP10最佳表现股票列表

## 常见问题

### Q1: 提示"获取数据失败"
**解决方案:**
- 检查网络连接
- 确保akshare库是最新版本
- 股票代码格式正确（6位数字）

### Q2: 回测结果胜率很低
**可能原因:**
- 当前市场环境不适合该策略
- 参数设置过于严格
- 需要结合大盘环境分析

### Q3: 想要测试更多股票
**修改方法:**
```python
# 增加测试股票数量
stock_list = [code for code in stock_list if not code.startswith(('300', '688', '8', '4'))][:100]  # 改为100只
```

## 进阶使用

### 批量参数测试
```python
def parameter_test():
    results = {}
    for hold_days in [5, 10, 15, 20]:
        backtest = TDXBacktest()
        result = backtest.run_backtest(hold_days=hold_days)
        results[f'{hold_days}日'] = backtest.analyze_results(result)
    return results
```

### 分行业测试
```python
# 测试特定行业股票
tech_stocks = ['000858', '002415', '300059', '600036']  # 科技股
finance_stocks = ['000001', '600036', '601318', '600519']  # 金融股
```

## 注意事项

⚠️ **重要提醒:**
1. 历史回测结果不代表未来表现
2. 建议结合多种测试方法验证
3. 实盘操作前请先小资金验证
4. 严格执行风险控制策略

## 技术支持

如果遇到问题，请检查：
1. Python版本 >= 3.7
2. 依赖库版本是否最新
3. 网络连接是否正常
4. 股票代码格式是否正确

开始您的量化回测之旅吧！ 📈 