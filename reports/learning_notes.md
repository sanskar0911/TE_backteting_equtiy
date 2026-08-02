# Learning Notes — Week 1

## Part A: Equity Market Basics (Day 1)

### 1. What is a stock?

A stock (or "share") is a unit of ownership in a company. If a company has
issued 1,000,000 shares and you own 1,000 of them, you own 0.1% of that
company. As a shareholder you get:

- A claim on the company's profits (via dividends, if the company pays them)
- Voting rights on major company decisions (usually 1 vote per share)
- A claim on assets if the company is liquidated (after debt holders are paid)

The **price** of a stock is simply what buyers and sellers currently agree
it's worth — it moves constantly based on supply and demand, which in turn
is driven by earnings, news, macroeconomic conditions, and sentiment.

### 2. NSE and BSE

India has two major stock exchanges:

- **NSE (National Stock Exchange)** — the larger exchange by trading volume,
  home of the Nifty indices. Ticker suffix in Yahoo Finance: `.NS`
  (e.g. `RELIANCE.NS`).
- **BSE (Bombay Stock Exchange)** — Asia's oldest stock exchange, home of the
  Sensex index. Ticker suffix in Yahoo Finance: `.BO`.

Most large Indian companies are listed on **both**. Prices are extremely
close between the two (arbitrage keeps them in sync), but not always
identical to the paisa. For backtesting, pick one exchange and stick with it
consistently — mixing sources mid-analysis introduces subtle errors.

### 3. Nifty 50

The **Nifty 50** is a stock market index representing the weighted average
performance of the 50 largest, most liquid companies listed on the NSE. It's
used as:

- A benchmark ("did my portfolio beat the Nifty 50?")
- The basis for index funds and ETFs
- A general gauge of Indian large-cap market health

Important nuance for backtesting: the 50 companies **change over time** as
companies grow, shrink, get delisted, or get replaced. The "Nifty 50 today"
is not the "Nifty 50 of 2015." This becomes directly relevant to
**survivorship bias**, covered below.

### 4. OHLCV Data

For any stock, on any trading day, you get five core numbers:

| Field | Meaning |
|---|---|
| **Open** | Price at which the stock first traded when the market opened that day |
| **High** | Highest price the stock touched during the day |
| **Low** | Lowest price the stock touched during the day |
| **Close** | Price at which the stock last traded before the market closed |
| **Volume** | Total number of shares that changed hands that day |

This is the fundamental unit of data for almost all technical and
quantitative analysis. A "daily bar" of OHLCV compresses an entire day of
continuous price movement into 5 numbers.

**Why Volume matters**: A price move on high volume is generally considered
more meaningful/reliable than the same move on low volume, because it
reflects broader participation rather than a few small trades.

### 5. Adjusted Close

The **Adjusted Close** is the closing price modified to account for
corporate actions (splits, dividends, bonuses) that happened *after* that
date, so that historical prices remain comparable over time.

Example: if a stock closed at ₹200 yesterday and does a 2-for-1 split today,
the raw closing price drops to ~₹100 — but that's not a real loss in value.
The adjusted close retroactively halves all *historical* closing prices so
the chart shows a smooth, continuous line instead of a fake 50% crash.

**Rule of thumb: always use Adjusted Close for return calculations and
backtesting.** Use raw Close/Open/High/Low only when you specifically care
about the literal traded price on that day (e.g., simulating an actual order
that would have executed at the market).

### 6. Corporate Actions

These are events initiated by the company that change the share structure
or return cash to shareholders — and they all distort raw price data if not
handled correctly.

#### Stock Split
The company divides each existing share into multiple shares (e.g. 1-for-2
split: each share becomes 2 shares), proportionally reducing the price so
total value is unchanged.
- Increases number of shares outstanding
- Reduces price per share proportionally
- **No change in market cap or in your actual investment value**
- Usually done to make shares more affordable/liquid for retail investors

#### Bonus Issue
The company issues *additional free shares* to existing shareholders in a
fixed ratio (e.g. 1:1 bonus = you get 1 free share for every share you own).
Economically very similar to a split — more shares, proportionally lower
price, same total value — but done differently from an accounting
perspective (bonus shares come from reserves, not from subdividing existing
shares).

#### Dividend
A cash payment from company profits, paid per share, to shareholders. On the
"ex-dividend date," the stock price typically drops by roughly the dividend
amount, because that cash has now left the company. This is why Adjusted
Close matters — without adjustment, every dividend payout looks like a tiny
price crash.

---

## Part B: Backtesting Pitfalls (Day 6)

These three biases are the most common ways beginners (and even
professionals) fool themselves into thinking a trading strategy works when
it actually wouldn't have worked in real life.

### 1. Look-Ahead Bias

**Definition**: Using information in your simulation that would **not
actually have been available** at that point in time.

```python
# WRONG — this peeks into the future
today_signal = tomorrow_price > today_price
```

This is wrong because on "today," you cannot possibly know "tomorrow's"
price yet. Any backtest using this signal will look magically profitable,
because it's cheating — it's not simulating a real decision process.

**Subtler real-world examples:**
- Using a company's *full-year* revenue (reported months later) to decide a
  trade *during* that year.
- Using a stock's 50-day moving average calculated with `.rolling(50)` but
  accidentally computed on a dataframe that wasn't sorted by date, so
  "future" rows leak into "past" windows.
- Using adjusted close prices that were adjusted for a stock split that
  hadn't happened yet on that historical date (this happens if you download
  data once and don't re-download after a split).

**Fix**: at each simulated point in time `t`, your strategy should only ever
see data from `t` and earlier — never `t+1` onward.

### 2. Survivorship Bias

**Definition**: Building or testing a strategy using only companies that
*still exist and succeeded* today, ignoring the companies that went bankrupt,
got delisted, or were removed from the index.

```python
# WRONG
# Using today's Nifty 50 constituent list to backtest strategy performance
# over the last 15 years.
```

This is wrong because the Nifty 50 of 2010 was a *different set of 50
companies* than the Nifty 50 of today. Some of those older companies
underperformed so badly they were removed from the index (or delisted
entirely) — and by only testing on "today's winners," your backtest
silently excludes all the losers, making the strategy look much better than
it would have performed in real time.

**Fix**: use point-in-time index membership data (which lists showed which
companies were in the Nifty 50 on any given historical date), not the
current list projected backward.

### 3. Overfitting

**Definition**: Tuning a strategy's parameters so extensively against
historical data that it starts fitting the **noise** of that specific
dataset rather than any real, repeatable market pattern.

```python
# WRONG
# Trying moving-average windows of 5, 6, 7, ... 200 days, and every possible
# stop-loss/take-profit percentage, until you find the one combination that
# produced the best historical returns.
```

This is wrong because with enough parameter combinations, you will
*eventually* find something that happened to work on that historical data
purely by chance — the same way flipping enough coins will eventually
produce a run of 10 heads in a row. That combination has no real predictive
power going forward.

**Warning signs of overfitting:**
- A strategy needs oddly specific parameters to work (e.g., a 37-day moving
  average, not 20 or 50)
- Performance looks great in backtesting but the "logic" of why it should
  work is vague or absent
- You tested hundreds of parameter combinations and picked the single best one

**Fix**: 
- Use simple, few parameters with clear economic/behavioral rationale
- Split data into training and out-of-sample test periods — a strategy
  should still work reasonably well on data it wasn't tuned on
- Be suspicious of "too good to be true" backtest results

---

## Quick Reference Table

| Term | Meaning |
|---|---|
| OHLCV | Daily Open, High, Low, Close, Volume trading data |
| Volume | Number of shares traded in a session |
| Adjusted Close | Close price retroactively corrected for splits/dividends |
| Split | Increases share count, proportionally reduces price — no value change |
| Bonus | Free extra shares issued to existing holders in a fixed ratio |
| Dividend | Cash payout to shareholders from profits |
| Market Cap | Share price × shares outstanding = company's total market value |
| Look-Ahead Bias | Using future information in a past decision |
| Survivorship Bias | Testing only on companies/stocks that "survived" to today |
| Overfitting | Tuning parameters until they fit historical noise, not real signal |
