from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# 创建数据库引擎
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'btc_arbitrage.db')
engine = create_engine(f'sqlite:///{DB_PATH}')

# 创建基类
Base = declarative_base()

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 套利机会记录模型
class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    expiry_date = Column(String)  # 期权到期日期
    strike_price = Column(Float)  # 执行价格
    btc_price = Column(Float)     # BTC现货价格
    
    # 合成期货多头信息
    synthetic_long_price = Column(Float)  # 合成期货多头价格
    long_price_diff = Column(Float)       # 多头价差
    long_annual_rate = Column(Float)      # 多头年化收益率
    
    # 合成期货空头信息
    synthetic_short_price = Column(Float)  # 合成期货空头价格
    short_price_diff = Column(Float)       # 空头价差
    short_annual_rate = Column(Float)      # 空头年化收益率
    
    # 期权信息
    call_option_id = Column(String)  # 看涨期权ID
    call_ask = Column(Float)         # 看涨期权卖价
    call_bid = Column(Float)         # 看涨期权买价
    
    put_option_id = Column(String)   # 看跌期权ID
    put_ask = Column(Float)          # 看跌期权卖价
    put_bid = Column(Float)          # 看跌期权买价
    
    # 剩余时间信息
    days_to_expiry = Column(Float)   # 剩余天数
    
    def __repr__(self):
        return f"<ArbitrageOpportunity(id={self.id}, expiry_date={self.expiry_date}, strike_price={self.strike_price})>"

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)