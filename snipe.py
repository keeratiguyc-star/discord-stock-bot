import os
import discord
import datetime
import yfinance as yf
from discord.ext import commands
from alpha_vantage.timeseries import TimeSeries

# Bot setting
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# API Keys
ALPHA_VANTAGE_API_KEY = os.getenv("API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.command(name='snipe')
async def snipe_stock(ctx, symbol: str):
    symbol = symbol.upper()
    embed = discord.Embed(title=f"📈 ข้อมูลหุ้น {symbol}", color=0x00ff00)
    embed.set_thumbnail(url=f"https://finance.yahoo.com/quote/{symbol}/profile?p={symbol}")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")
        
        if not info or info.get('symbol') != symbol:
            embed.description = f"❌ ไม่พบข้อมูลหุ้น {symbol}"
            await ctx.send(embed=embed)
            return
        
        company_name = info.get('longName', 'N/A')
        exchange = info.get('exchange', 'N/A')
        embed.description = f"{company_name} ({exchange})"
        
        current_price = info.get('currentPrice', 'N/A')
        previous_close = info.get('previousClose', 'N/A')
        open_price = info.get('open', 'N/A')
        day_high = info.get('dayHigh', 'N/A')
        day_low = info.get('dayLow', 'N/A')

        change = current_price - previous_close if current_price != 'N/A' else 0
        change_percent = (change / previous_close * 100) if previous_close not in ['N/A', 0] else 0
        
        price_field = (
            f"ราคาปัจจุบัน: ${current_price:.4f}\n"
            f"เปลี่ยนแปลง: {change:+.4f} ({change_percent:+.4f}%)\n"
            f"ราคาเปิด: ${open_price:.4f}\n"
            f"สูงสุดวันนี้: ${day_high:.4f}\n"
            f"ต่ำสุดวันนี้: ${day_low:.4f}"
        )
        embed.add_field(name="💰 ราคาและการเคลื่อนไหว", value=price_field, inline=False)
        
        volume = hist['Volume'].iloc[-1] if not hist.empty else 'N/A'
        try:
            ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
            quote_data, _ = ts.get_quote_endpoint(symbol=symbol)
            if not quote_data.empty:
                volume = quote_data['05. volume'].iloc[0]
        except:
            pass
        
        trading_field = (
            f"ปริมาณซื้อขาย: {volume:,}\n"
            f"วันที่ล่าสุด: {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
            f"ราคาปิดก่อนหน้า: ${previous_close:.4f}"
        )
        embed.add_field(name="📊 การซื้อขาย", value=trading_field, inline=False)
        
        # Company Stats
        industry = info.get('industry', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        market_cap = f"${market_cap:,.0f}" if market_cap != 'N/A' else 'N/A'
        pe_ratio = info.get('trailingPE', 'None')
        eps = info.get('trailingEps', 0)
        dividend_yield = info.get('dividendYield', None)
        dividend_yield = f"{dividend_yield*100:.2f}%" if dividend_yield else "None"
        
        company_field = (
            f"อุตสาหกรรม: {industry}\n"
            f"มูลค่าตลาด: {market_cap}\n"
            f"P/E Ratio: {pe_ratio}\n"
            f"EPS: ${eps:.2f}\n"
            f"Dividend Yield: {dividend_yield}"
        )
        embed.add_field(name="🏢 ข้อมูลบริษัท", value=company_field, inline=False)
        
        # 52W HIGH/LOW
        week52_high = info.get('fiftyTwoWeekHigh', 'N/A')
        week52_low = info.get('fiftyTwoWeekLow', 'N/A')
        
        week52_field = (
            f"สูงสุด 52 สัปดาห์: ${week52_high:.2f}\n"
            f"ต่ำสุด 52 สัปดาห์: ${week52_low:.2f}"
        )
        embed.add_field(name="📅 ช่วง 52 สัปดาห์", value=week52_field, inline=False)
        
        # Analyst Recommendation
        rating = info.get('recommendationMean', 'N/A')
        rating_text = "ไม่มีคำแนะนำ"

        if rating != 'N/A':
            rv = float(rating)

            inverted_rating = 6 - rv

            rounded_rating = round(inverted_rating, 1)

            if rounded_rating >= 4.0:
                rating_text = "ซื้อ"
            elif rounded_rating >= 3.0:
                rating_text = "ถือ"
            else:
                rating_text = "ขาย"


        try:
            targets = ticker.analyst_price_targets
            if targets.get('mean'):
                analyst_field = (
                    f"การให้คะแนนโดยรวม: {rating_text} ({rounded_rating}/5)\n"
                    f"ราคาเฉลี่ย: ${targets['mean']:.3f}\n"
                    f"ต่ำสุด: ${targets['low']:.3f}\n"
                    f"สูงสุด: ${targets['high']:.3f}"
                )
            else:
                analyst_field = (
                    f"การให้คะแนนโดยรวม: {rating_text} ({rounded_rating}/5)\n"
                )
        except:
            analyst_field = (
                f"การให้คะแนนโดยรวม: {rating_text} ({rounded_rating}/5)\n"
            )


        embed.add_field(name="🔮 การคาดการณ์นักวิเคราะห์", value=analyst_field, inline=False)
        
        embed.set_footer(text=f"ข้อมูลจาก Yahoo Finance & Alpha Vantage | อัพเดทล่าสุด: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        embed.description = f"❌ เกิดข้อผิดพลาด: {str(e)}"
        await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
