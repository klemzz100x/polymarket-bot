from dataclasses import dataclass

from polybot.research.obsidian_mining.strategy_candidate import EdgeFamily


@dataclass(frozen=True, slots=True)
class HypothesisTemplate:
    hypothesis: str
    required_data: list[str]
    metrics_to_measure: list[str]
    testable_signal: str
    backtest_design: str
    main_risk: str
    implementation_difficulty: str
    priority: str
    next_action: str


TEMPLATES: dict[EdgeFamily, HypothesisTemplate] = {
    EdgeFamily.SPREAD_CAPTURE: HypothesisTemplate(
        hypothesis="Persistent wide spreads may allow passive entries and exits after spread normalization.",
        required_data=["orderbook snapshots", "visible depth", "trades", "fees", "latency assumptions"],
        metrics_to_measure=["spread_pct", "spread_duration", "fill_rate", "slippage", "depth_at_touch"],
        testable_signal="spread_pct above threshold for N consecutive snapshots with sufficient depth.",
        backtest_design="Simulate passive orders at or inside the touch, include latency, partial fills, and exit on spread normalization.",
        main_risk="Queue priority and stale books can make apparent passive fills unrealistic.",
        implementation_difficulty="medium",
        priority="high",
        next_action="Run wide-spread backtests on markets with clean data and stable collection cadence.",
    ),
    EdgeFamily.MARKET_MAKING: HypothesisTemplate(
        hypothesis="Markets with stable mid price and recurring two-sided flow may support controlled inventory market making.",
        required_data=["orderbooks", "trades", "inventory curve", "fees", "market metadata"],
        metrics_to_measure=["spread", "depth", "trade arrival rate", "inventory exposure", "adverse selection"],
        testable_signal="stable mid price, nonzero trade flow, and sufficient bid/ask depth.",
        backtest_design="Quote both sides with inventory caps and cancel rules, then measure fill quality and adverse selection.",
        main_risk="Inventory accumulation and adverse selection during news or resolution events.",
        implementation_difficulty="high",
        priority="medium",
        next_action="Prototype in backtesting only with strict inventory and stale-data rules.",
    ),
    EdgeFamily.ORDERBOOK_IMBALANCE: HypothesisTemplate(
        hypothesis="Extreme orderbook imbalance may predict short-term repricing toward the heavy side.",
        required_data=["orderbook snapshots", "price ticks", "trades"],
        metrics_to_measure=["imbalance", "future_mid_change", "depth_change", "fill_rate"],
        testable_signal="absolute imbalance above threshold with stable spread and recent updates.",
        backtest_design="Enter in the direction of pressure after latency delay and exit after fixed horizon or mid-price move.",
        main_risk="Displayed depth can be spoofed or vanish before execution.",
        implementation_difficulty="medium",
        priority="high",
        next_action="Measure forward returns after imbalance events by market category.",
    ),
    EdgeFamily.LIQUIDITY_VACUUM: HypothesisTemplate(
        hypothesis="Thin books with abrupt price movement may overreact and partially revert.",
        required_data=["orderbooks", "trades", "price ticks"],
        metrics_to_measure=["total_depth", "spread_pct", "price_jump", "reversion_rate", "slippage"],
        testable_signal="low total depth plus rapid mid-price jump and elevated spread.",
        backtest_design="Simulate conservative fade orders sized below visible depth with stop and exposure caps.",
        main_risk="Thin liquidity can continue moving and make fills very expensive.",
        implementation_difficulty="medium",
        priority="medium",
        next_action="Scan liquidity vacuum signals and compare realized slippage before backtesting size.",
    ),
    EdgeFamily.STALE_ORDERBOOK: HypothesisTemplate(
        hypothesis="Markets with stale visible books may contain delayed prices relative to trades or related markets.",
        required_data=["orderbook timestamps", "trades", "price ticks", "related market prices"],
        metrics_to_measure=["snapshot_age", "update_frequency", "trade_book_divergence", "cross_market_gap"],
        testable_signal="orderbook update age above threshold while trades or correlated markets move.",
        backtest_design="Replay stale intervals and require executable depth after simulated latency.",
        main_risk="The book may be stale because it is not actually executable.",
        implementation_difficulty="high",
        priority="high",
        next_action="Add stale-book scans to data validation and compare with trades.",
    ),
    EdgeFamily.DELAYED_REPRICING: HypothesisTemplate(
        hypothesis="Some markets may reprice slowly after related market or signal movement.",
        required_data=["orderbooks", "related market mapping", "price ticks", "news/event timestamps"],
        metrics_to_measure=["lead_lag", "repricing_delay", "cross_market_gap", "execution_slippage"],
        testable_signal="related market moves while target market mid price remains unchanged.",
        backtest_design="Create paired-market replay and trade only when target book remains executable after latency.",
        main_risk="Mapping related markets incorrectly creates false edges.",
        implementation_difficulty="high",
        priority="medium",
        next_action="Build related-market metadata before productionizing this hypothesis.",
    ),
    EdgeFamily.CROSS_MARKET_ARBITRAGE: HypothesisTemplate(
        hypothesis="Equivalent outcomes across venues or related Polymarket markets may occasionally diverge enough to cover costs.",
        required_data=["cross-venue prices", "fees", "withdrawal/settlement constraints", "orderbook depth"],
        metrics_to_measure=["price_gap", "net_gap_after_fees", "hedge_fill_rate", "leg_slippage"],
        testable_signal="net price gap above threshold on both executable legs.",
        backtest_design="Simulate both legs with partial fill handling and unhedged exposure penalties.",
        main_risk="One leg can fill while the hedge leg fails or reprices.",
        implementation_difficulty="high",
        priority="high",
        next_action="Start with read-only gap monitoring before any execution design.",
    ),
    EdgeFamily.NEWS_LATENCY: HypothesisTemplate(
        hypothesis="Markets may underreact for a short time after credible news hits public feeds.",
        required_data=["news timestamps", "orderbooks", "trades", "market metadata"],
        metrics_to_measure=["news_to_price_delay", "spread_change", "volume_spike", "slippage"],
        testable_signal="credible news event with delayed orderbook repricing and executable depth.",
        backtest_design="Replay event windows using external timestamps and strict latency penalties.",
        main_risk="News quality and timestamp accuracy can dominate results.",
        implementation_difficulty="high",
        priority="medium",
        next_action="Define approved news sources and timestamp capture first.",
    ),
    EdgeFamily.EVENT_DRIVEN_REPRICING: HypothesisTemplate(
        hypothesis="Scheduled events may create predictable repricing phases around start, halftime, close, or resolution windows.",
        required_data=["event schedule", "market metadata", "orderbooks", "trades"],
        metrics_to_measure=["pre_event_spread", "post_event_jump", "volume_spike", "fill_quality"],
        testable_signal="event timestamp proximity plus widening spread or sudden depth shift.",
        backtest_design="Segment replay around event windows and compare strategy behavior by phase.",
        main_risk="Resolution rules and event timing ambiguity can invalidate signals.",
        implementation_difficulty="medium",
        priority="medium",
        next_action="Tag markets with event calendars before broad testing.",
    ),
    EdgeFamily.BEHAVIORAL_OVERREACTION: HypothesisTemplate(
        hypothesis="Retail flow may overreact to visible narratives, creating short-lived mispricings.",
        required_data=["trades", "orderbooks", "social/news signals", "price ticks"],
        metrics_to_measure=["price_jump", "volume_spike", "reversion", "orderbook_imbalance"],
        testable_signal="large price jump plus volume spike followed by weakening depth support.",
        backtest_design="Fade only after confirmation of spread stabilization and adequate depth.",
        main_risk="Overreaction can be correct information arrival.",
        implementation_difficulty="medium",
        priority="low",
        next_action="Label candidate events manually before quantitative testing.",
    ),
    EdgeFamily.RESOLUTION_EDGE: HypothesisTemplate(
        hypothesis="Markets near resolution may be mispriced when rules, source-of-truth, or settlement timing are misunderstood.",
        required_data=["market rules", "resolution source", "orderbooks", "trades", "event outcome data"],
        metrics_to_measure=["time_to_resolution", "spread", "liquidity", "rule_uncertainty", "settlement_gap"],
        testable_signal="market close to resolution with rule clarity advantage and executable price gap.",
        backtest_design="Research-only replay with manual labels for true resolution state.",
        main_risk="Rule interpretation errors and disputed outcomes can dominate edge.",
        implementation_difficulty="high",
        priority="medium",
        next_action="Create a resolution research checklist before automated testing.",
    ),
}


def template_for(edge_family: EdgeFamily) -> HypothesisTemplate:
    return TEMPLATES[edge_family]
