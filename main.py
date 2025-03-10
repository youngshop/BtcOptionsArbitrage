from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import datetime
from sqlalchemy.orm import Session
import uvicorn

from models import get_db, ArbitrageOpportunity, create_tables
from utils import get_all_arbitrage_opportunities, group_opportunities_by_expiry

# 创建数据库表
create_tables()

# 创建FastAPI应用
app = FastAPI(title="BTC期权套利监控系统")

# 设置静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 设置模板目录
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, min_rate: float = 0.05, db: Session = Depends(get_db)):
    # 获取所有套利机会
    opportunities = get_all_arbitrage_opportunities(min_annual_rate=min_rate)
    
    # 按到期日分组
    grouped_opportunities = group_opportunities_by_expiry(opportunities)
    
    # 获取已保存的套利机会
    saved_opportunities = db.query(ArbitrageOpportunity).all()
    grouped_saved = {}
    for opp in saved_opportunities:
        if opp.expiry_date not in grouped_saved:
            grouped_saved[opp.expiry_date] = []
        grouped_saved[opp.expiry_date].append(opp)
    
    # 对每个到期日内的机会按执行价格排序
    for expiry in grouped_saved:
        grouped_saved[expiry].sort(key=lambda x: x.strike_price)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "opportunities": grouped_opportunities,
            "saved_opportunities": grouped_saved,
            "min_rate": min_rate,
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "btc_price": opportunities[0]["btc_price"] if opportunities else 0
        }
    )

# 保存套利机会路由
@app.post("/save_opportunity")
async def save_opportunity(
    call_option_id: str = Form(...),
    put_option_id: str = Form(...),
    expiry_date: str = Form(...),
    strike_price: float = Form(...),
    btc_price: float = Form(...),
    synthetic_long_price: float = Form(...),
    synthetic_short_price: float = Form(...),
    long_price_diff: float = Form(...),
    short_price_diff: float = Form(...),
    long_annual_rate: float = Form(...),
    short_annual_rate: float = Form(...),
    days_to_expiry: float = Form(...),
    call_ask: float = Form(...),
    call_bid: float = Form(...),
    put_ask: float = Form(...),
    put_bid: float = Form(...),
    db: Session = Depends(get_db)
):
    # 创建新的套利机会记录
    new_opportunity = ArbitrageOpportunity(
        expiry_date=expiry_date,
        strike_price=strike_price,
        btc_price=btc_price,
        synthetic_long_price=synthetic_long_price,
        synthetic_short_price=synthetic_short_price,
        long_price_diff=long_price_diff,
        short_price_diff=short_price_diff,
        long_annual_rate=long_annual_rate,
        short_annual_rate=short_annual_rate,
        days_to_expiry=days_to_expiry,
        call_option_id=call_option_id,
        call_ask=call_ask,
        call_bid=call_bid,
        put_option_id=put_option_id,
        put_ask=put_ask,
        put_bid=put_bid
    )
    
    # 保存到数据库
    db.add(new_opportunity)
    db.commit()
    
    # 重定向回首页
    return RedirectResponse(url="/", status_code=303)

# 删除保存的套利机会路由
@app.post("/delete_opportunity/{opportunity_id}")
async def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    # 查找并删除套利机会
    opportunity = db.query(ArbitrageOpportunity).filter(ArbitrageOpportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="套利机会未找到")
    
    db.delete(opportunity)
    db.commit()
    
    # 重定向回首页
    return RedirectResponse(url="/", status_code=303)

# 刷新套利机会路由
@app.get("/refresh")
async def refresh(min_rate: float = 0.05):
    return RedirectResponse(url=f"/?min_rate={min_rate}", status_code=303)

# 主函数
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)