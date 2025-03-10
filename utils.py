import requests
import datetime
import math
import numpy as np
from scipy.stats import norm
from typing import List, Dict, Tuple, Optional

# 计算隐含波动率
def calculate_implied_volatility(option_price, underlying_price, strike_price, time_to_maturity, option_type='call'):
    # 定义 Black-Scholes 模型的参数
    S = underlying_price
    K = strike_price
    T = time_to_maturity
    # 无风险收益率
    r = 0.045

    sigma = 0.3  # 假设的初始波动率
    # 调整波动率，使得计算的期权价格等于给定的期权价格
    for i in range(2000):
        sigma = sigma + 0.0005
        d1 = (np.log(S / K) + (r + sigma ** 2/2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        if np.isclose(price, option_price, atol=5):
            break

    return round(sigma, 5)

# 获取BTC现货价格
def get_btc_spot_price():
    try:
        response = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USD")
        response.raise_for_status()
        data = response.json()
        if data.get('code') == '0' and data.get('data'):
            return float(data['data'][0]['bidPx'])
        else:
            raise Exception(f"获取BTC价格失败: {data.get('msg', '未知错误')}")
    except Exception as e:
        print(f"获取BTC价格出错: {str(e)}")
        return None

# 获取所有BTC期权数据
def get_all_btc_options():
    try:
        response = requests.get("https://www.okx.com/api/v5/market/tickers?instType=OPTION&instFamily=BTC-USD")
        response.raise_for_status()
        data = response.json()
        if data.get('code') == '0' and data.get('data'):
            return data['data']
        else:
            raise Exception(f"获取期权数据失败: {data.get('msg', '未知错误')}")
    except Exception as e:
        print(f"获取期权数据出错: {str(e)}")
        return []

# 获取特定期权数据
def get_option_data(inst_id):
    try:
        response = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}")
        response.raise_for_status()
        data = response.json()
        if data.get('code') == '0' and data.get('data'):
            return data['data'][0]
        else:
            raise Exception(f"获取期权数据失败: {data.get('msg', '未知错误')}")
    except Exception as e:
        print(f"获取期权数据出错: {str(e)}")
        return None

# 解析期权ID，返回到期日期、执行价格和期权类型
def parse_option_id(option_id):
    parts = option_id.split('-')
    if len(parts) != 5:
        return None, None, None
    
    expiry_date = parts[2]  # 格式如: 250628
    strike_price = float(parts[3])
    option_type = parts[4]  # C 或 P
    
    return expiry_date, strike_price, option_type

# 计算到期剩余时间（以年为单位）
def calculate_time_to_expiry(expiry_date):
    try:
        # 将日期格式从YYMMDD转换为完整日期时间
        expiry_datetime = datetime.datetime.strptime(f"20{expiry_date} 16:00", "%Y%m%d %H:%M")
        current_datetime = datetime.datetime.now()
        
        # 计算剩余时间（秒）
        time_diff = expiry_datetime - current_datetime
        seconds_to_expiry = max(0, time_diff.total_seconds())
        
        # 转换为年
        years_to_expiry = seconds_to_expiry / (365 * 24 * 60 * 60)
        
        return years_to_expiry, seconds_to_expiry
    except Exception as e:
        print(f"计算到期时间出错: {str(e)}")
        return 0, 0

# 计算期权的时间价值
def calculate_time_value(option_price, btc_price, strike_price, option_type):
    intrinsic_value = 0
    
    if option_type == 'C':  # 看涨期权
        if btc_price > strike_price:
            intrinsic_value = btc_price - strike_price
    else:  # 看跌期权
        if strike_price > btc_price:
            intrinsic_value = strike_price - btc_price
    
    time_value = option_price - intrinsic_value
    return max(0, time_value)

# 计算合成期货价格和套利机会
def calculate_arbitrage_opportunity(call_option, put_option, btc_price, min_annual_rate=0.05):
    # 解析期权ID
    call_id = call_option['instId']
    put_id = put_option['instId']
    
    expiry_date, strike_price, _ = parse_option_id(call_id)
    if not expiry_date:
        return None
    
    # 计算到期时间
    years_to_expiry, seconds_to_expiry = calculate_time_to_expiry(expiry_date)
    days_to_expiry = seconds_to_expiry / (24 * 60 * 60)
    
    # 获取期权价格
    call_ask = float(call_option.get('askPx', 0)) * btc_price  # 看涨期权卖价（美元）
    call_bid = float(call_option.get('bidPx', 0)) * btc_price  # 看涨期权买价（美元）
    put_ask = float(put_option.get('askPx', 0)) * btc_price   # 看跌期权卖价（美元）
    put_bid = float(put_option.get('bidPx', 0)) * btc_price   # 看跌期权买价（美元）
    
    # 计算合成期货价格
    # 合成多头 = 买入看涨期权 + 卖出看跌期权 + 存入执行价格的现金
    synthetic_long_price = strike_price + call_ask - put_bid
    
    # 合成空头 = 卖出看涨期权 + 买入看跌期权 + 借入执行价格的现金
    synthetic_short_price = strike_price + call_bid - put_ask
    
    # 计算价差
    long_price_diff = btc_price - synthetic_long_price
    short_price_diff = synthetic_short_price - btc_price
    
    # 计算年化收益率
    long_annual_rate = long_price_diff / btc_price / years_to_expiry if years_to_expiry > 0 else 0
    short_annual_rate = short_price_diff / btc_price / years_to_expiry if years_to_expiry > 0 else 0
    
    # 机会成本（年化5%）
    opportunity_cost = btc_price * years_to_expiry * min_annual_rate
    
    # 创建套利机会对象
    opportunity = {
        'expiry_date': f"20{expiry_date}",
        'strike_price': strike_price,
        'btc_price': btc_price,
        'days_to_expiry': days_to_expiry,
        'years_to_expiry': years_to_expiry,
        
        # 合成多头信息
        'synthetic_long_price': synthetic_long_price,
        'long_price_diff': long_price_diff,
        'long_annual_rate': long_annual_rate,
        
        # 合成空头信息
        'synthetic_short_price': synthetic_short_price,
        'short_price_diff': short_price_diff,
        'short_annual_rate': short_annual_rate,
        
        # 期权信息
        'call_option_id': call_id,
        'call_ask': call_ask / btc_price,  # 转回BTC单位
        'call_bid': call_bid / btc_price,
        
        'put_option_id': put_id,
        'put_ask': put_ask / btc_price,
        'put_bid': put_bid / btc_price,
        
        # 机会成本
        'opportunity_cost': opportunity_cost
    }
    
    # 检查是否满足最低年化收益率要求
    if (short_annual_rate >= min_annual_rate or long_annual_rate >= min_annual_rate):
        return opportunity
    else:
        return None

# 获取所有可能的套利机会
def get_all_arbitrage_opportunities(min_annual_rate=0.05):
    # 获取BTC现货价格
    btc_price = get_btc_spot_price()
    if not btc_price:
        return []
    
    # 获取所有期权数据
    all_options = get_all_btc_options()
    if not all_options:
        return []
    
    # 按期权ID排序
    all_options.sort(key=lambda x: x['instId'])
    
    # 将看涨和看跌期权配对
    paired_options = []
    i = 0
    while i < len(all_options) - 1:
        current_id = all_options[i]['instId']
        next_id = all_options[i + 1]['instId']
        
        # 检查是否为同一执行价格和到期日的看涨和看跌期权
        if current_id[:-1] == next_id[:-1] and current_id[-1] != next_id[-1]:
            # 确保第一个是看涨，第二个是看跌
            if current_id[-1] == 'C' and next_id[-1] == 'P':
                paired_options.append((all_options[i], all_options[i + 1]))
            elif current_id[-1] == 'P' and next_id[-1] == 'C':
                paired_options.append((all_options[i + 1], all_options[i]))
            i += 2
        else:
            i += 1
    
    # 计算每对期权的套利机会
    opportunities = []
    for call_option, put_option in paired_options:
        # 检查期权是否有有效报价
        if (call_option.get('askPx') and call_option.get('bidPx') and 
            put_option.get('askPx') and put_option.get('bidPx')):
            opportunity = calculate_arbitrage_opportunity(
                call_option, put_option, btc_price, min_annual_rate
            )
            if opportunity:
                opportunities.append(opportunity)
    
    return opportunities

# 按到期日期对套利机会进行分组
def group_opportunities_by_expiry(opportunities):
    grouped = {}
    for opp in opportunities:
        expiry = opp['expiry_date']
        if expiry not in grouped:
            grouped[expiry] = []
        grouped[expiry].append(opp)
    
    # 对每个到期日内的机会按执行价格排序
    for expiry in grouped:
        grouped[expiry].sort(key=lambda x: x['strike_price'])
    
    return grouped