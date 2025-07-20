#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股公式回测系统
测试底部吸筹启动策略的历史表现
"""

import pandas as pd
import numpy as np
import akshare as ak
import warnings
from datetime import datetime, timedelta
import time

warnings.filterwarnings('ignore')

class TDXBacktest:
    def __init__(self, start_date='20230101', end_date='20241231'):
        self.start_date = start_date
        self.end_date = end_date
        self.results = []
        
    def get_stock_data(self, symbol):
        """获取股票历史数据"""
        try:
            # 获取日线数据
            stock_data = ak.stock_zh_a_hist(symbol=symbol, 
                                           start_date=self.start_date, 
                                           end_date=self.end_date)
            if stock_data is not None and len(stock_data) > 0:
                stock_data.columns = ['date', 'open', 'high', 'low', 'close', 
                                    'volume', 'amount', 'amplitude', 'change_pct', 
                                    'change_amount', 'turnover']
                stock_data['date'] = pd.to_datetime(stock_data['date'])
                stock_data = stock_data.set_index('date').sort_index()
                return stock_data
            return None
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            return None
    
    def check_volume_conditions(self, data):
        """检查量价条件（核心选股逻辑）"""
        if len(data) < 120:
            return pd.Series(False, index=data.index)
        
        # 计算各种均线
        ma5 = data['close'].rolling(5).mean()
        ma20 = data['close'].rolling(20).mean()
        vol5 = data['volume'].rolling(5).mean()
        vol20 = data['volume'].rolling(20).mean()
        vol60 = data['volume'].rolling(60).mean()
        vol120 = data['volume'].rolling(120).mean()
        
        # 关键特征1：前期地量洗盘 + 当前量堆出现  
        # 统一检查30天前的地量洗盘阶段
        past_vol_20 = data['volume'].rolling(20).mean().shift(30)  # 30天前的20日均量
        past_vol_120 = vol120.shift(30)  # 30天前的120日均量
        前期地量洗盘 = past_vol_20 < past_vol_120 * 0.4
        
        当前量比 = vol20 / vol60.shift(20)
        量堆出现 = (当前量比 > 1.2) & (当前量比 < 3)
        
        # 关键特征2：前期小阴小阳线充分
        # 检查同一时期（30天前）的小阴小阳线
        daily_change = abs(data['change_pct'])
        小波动天数 = (daily_change < 3).rolling(20).sum()
        前期小阴小阳充分 = 小波动天数.shift(30) >= 12  # 30天前的小波动统计
        
        # 关键特征3：前期价格窄幅震荡
        # 检查同一时期（30天前）的价格震荡幅度
        high_20 = data['high'].rolling(20).max()
        low_20 = data['low'].rolling(20).min()
        震荡幅度 = (high_20 - low_20) / low_20
        前期窄幅震荡 = 震荡幅度.shift(30) < 0.3  # 30天前的震荡幅度
        
        # 关键特征4：底部区域确认
        底部价位 = data['low'].rolling(60).min()
        底部区域 = data['close'] < 底部价位 * 1.2
        
        # 启动信号
        量比 = data['volume'] / vol20
        开始放量 = (量比 > 1.5) & (量比 < 10)
        价格上攻 = (data['close'] > ma20) & (data['close'] > data['close'].shift(1))
        均线转强 = ma5 > ma5.shift(2)
        涨幅适中 = (data['change_pct'] > 0) & (data['change_pct'] < 9)
        
        # 综合选股条件
        底部吸筹 = 前期地量洗盘 & 量堆出现 & 前期小阴小阳充分 & 前期窄幅震荡 & 底部区域
        启动确认 = 开始放量 & 价格上攻 & 均线转强 & 涨幅适中
        
        选股信号 = 底部吸筹 & 启动确认
        
        return 选股信号
    
    def calculate_returns(self, data, signal_dates, hold_days=10):
        """计算持有收益率"""
        returns = []
        
        for signal_date in signal_dates:
            try:
                signal_idx = data.index.get_loc(signal_date)
                if signal_idx + hold_days < len(data):
                    buy_price = data.iloc[signal_idx]['close']
                    sell_price = data.iloc[signal_idx + hold_days]['close']
                    ret = (sell_price - buy_price) / buy_price * 100
                    
                    # 计算期间最高涨幅
                    period_data = data.iloc[signal_idx:signal_idx + hold_days + 1]
                    max_return = ((period_data['high'].max() - buy_price) / buy_price) * 100
                    
                    returns.append({
                        'signal_date': signal_date,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'return_pct': ret,
                        'max_return': max_return,
                        'hold_days': hold_days
                    })
            except Exception as e:
                continue
                
        return returns
    
    def backtest_stock(self, symbol, hold_days=10):
        """回测单只股票"""
        print(f"正在回测 {symbol}...")
        
        data = self.get_stock_data(symbol)
        if data is None:
            return None
        
        # 应用选股条件
        signals = self.check_volume_conditions(data)
        signal_dates = data.index[signals].tolist()
        
        if len(signal_dates) == 0:
            return None
        
        # 计算收益率
        returns = self.calculate_returns(data, signal_dates, hold_days)
        
        if len(returns) > 0:
            result = {
                'symbol': symbol,
                'signal_count': len(signal_dates),
                'valid_trades': len(returns),
                'returns': returns
            }
            return result
        
        return None
    
    def run_backtest(self, stock_list=None, hold_days=10):
        """运行回测"""
        if stock_list is None:
            # 获取A股主要股票列表
            try:
                stock_list = ak.stock_zh_a_spot_em()['代码'].head(100).tolist()
                # 过滤掉ST股票和指数
                stock_list = [code for code in stock_list if not code.startswith(('300', '688', '8', '4'))][:50]
            except:
                stock_list = ['000001', '000002', '000858', '002415', '600036', '600519', '000858']
        
        print(f"开始回测 {len(stock_list)} 只股票...")
        
        all_results = []
        successful_stocks = 0
        
        for i, symbol in enumerate(stock_list):
            try:
                result = self.backtest_stock(symbol, hold_days)
                if result:
                    all_results.append(result)
                    successful_stocks += 1
                    
                # 避免请求过频
                time.sleep(0.5)
                
                if i % 10 == 0:
                    print(f"已完成 {i}/{len(stock_list)} 只股票回测")
                    
            except Exception as e:
                print(f"股票 {symbol} 回测出错: {e}")
                continue
        
        print(f"回测完成！成功回测了 {successful_stocks} 只股票")
        return all_results
    
    def analyze_results(self, results):
        """分析回测结果"""
        if not results:
            print("没有有效的回测结果")
            return
        
        # 收集所有交易记录
        all_trades = []
        for result in results:
            for trade in result['returns']:
                trade['symbol'] = result['symbol']
                all_trades.append(trade)
        
        if not all_trades:
            print("没有有效的交易记录")
            return
        
        trades_df = pd.DataFrame(all_trades)
        
        # 计算统计指标
        total_trades = len(trades_df)
        win_trades = len(trades_df[trades_df['return_pct'] > 0])
        win_rate = win_trades / total_trades * 100
        
        avg_return = trades_df['return_pct'].mean()
        avg_win = trades_df[trades_df['return_pct'] > 0]['return_pct'].mean()
        avg_loss = trades_df[trades_df['return_pct'] <= 0]['return_pct'].mean()
        
        max_return = trades_df['return_pct'].max()
        min_return = trades_df['return_pct'].min()
        max_max_return = trades_df['max_return'].max()
        
        # 计算大涨股票比例（收益>8%）
        big_win_count = len(trades_df[trades_df['return_pct'] > 8])
        big_win_rate = big_win_count / total_trades * 100
        
        # 打印结果
        print("\n" + "="*50)
        print("回测结果统计")
        print("="*50)
        print(f"总交易次数: {total_trades}")
        print(f"胜率: {win_rate:.2f}%")
        print(f"平均收益率: {avg_return:.2f}%")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均亏损: {avg_loss:.2f}%")
        print(f"最大收益: {max_return:.2f}%")
        print(f"最小收益: {min_return:.2f}%")
        print(f"期间最高涨幅: {max_max_return:.2f}%")
        print(f"大涨股票数(>8%): {big_win_count} 只")
        print(f"大涨股票比例: {big_win_rate:.2f}%")
        
        # 收益分布
        print("\n收益分布:")
        bins = [-100, -10, -5, 0, 5, 10, 15, 20, 100]
        labels = ['<-10%', '-10%~-5%', '-5%~0%', '0%~5%', '5%~10%', '10%~15%', '15%~20%', '>20%']
        distribution = pd.cut(trades_df['return_pct'], bins=bins, labels=labels).value_counts()
        for label, count in distribution.items():
            percentage = count / total_trades * 100
            print(f"{label}: {count} 次 ({percentage:.1f}%)")
        
        # 按月份统计
        trades_df['signal_date'] = pd.to_datetime(trades_df['signal_date'])
        trades_df['month'] = trades_df['signal_date'].dt.to_period('M')
        monthly_stats = trades_df.groupby('month').agg({
            'return_pct': ['count', 'mean'],
            'symbol': 'count'
        }).round(2)
        
        print("\n月度统计:")
        print(monthly_stats.head(10))
        
        return trades_df

def main():
    """主函数"""
    print("通达信选股公式回测系统")
    print("测试底部吸筹启动策略")
    
    # 创建回测实例
    backtest = TDXBacktest(start_date='20230101', end_date='20241231')
    
    # 运行回测
    results = backtest.run_backtest(hold_days=10)
    
    # 分析结果
    trades_df = backtest.analyze_results(results)
    
    if trades_df is not None:
        # 保存结果到CSV
        filename = f"tdx_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        trades_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n详细结果已保存到: {filename}")
        
        # 输出表现最好的股票
        print("\n表现最好的股票TOP10:")
        top_stocks = trades_df.nlargest(10, 'return_pct')[['symbol', 'signal_date', 'return_pct', 'max_return']]
        print(top_stocks.to_string(index=False))

if __name__ == "__main__":
    main() 