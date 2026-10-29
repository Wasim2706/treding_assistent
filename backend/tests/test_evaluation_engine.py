import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.signal import Signal
from app.models.prediction import PredictionResult
from app.services.evaluation.service import evaluation_service


@pytest.mark.asyncio
async def test_register_prediction_for_signal(db_session):
    sig = Signal(
        symbol="TCS",
        direction="BUY",
        entry_zone="₹3940 - ₹3960",
        entry_price=3950.0,
        stop_loss=3890.0,
        target_1=4040.0,
        target_2=4100.0,
        risk_reward="1:2.0",
        confidence=80,
        entry_time_window="Post 09:30",
        exit_time_window="Before 15:15",
        composite_score=78.5,
        reasoning="Technical breakout above 20 EMA.",
        invalidated_if="Drop below 3890",
        technical_confirmation="CONFIRMED",
        status="PENDING",
    )
    db_session.add(sig)
    await db_session.commit()
    await db_session.refresh(sig)

    pred = await evaluation_service.register_prediction_for_signal(sig, db_session, horizon="1_DAY")
    assert pred.id is not None
    assert pred.signal_id == sig.id
    assert pred.symbol == "TCS"
    assert pred.predicted_direction == "BUY"
    assert pred.predicted_confidence == 80
    assert pred.price_at_prediction == 3950.0
    assert pred.is_evaluated is False

    # Calling register again is idempotent
    pred2 = await evaluation_service.register_prediction_for_signal(sig, db_session, horizon="1_DAY")
    assert pred2.id == pred.id


def test_evaluate_single_prediction_correct_buy():
    pred = PredictionResult(
        signal_id=1,
        symbol="INFY",
        predicted_direction="BUY",
        predicted_confidence=75,
        price_at_prediction=1800.0,
        evaluation_horizon="INTRADAY",
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=False,
    )
    evaluated = evaluation_service.evaluate_single_prediction(pred, current_price=1836.0)
    assert evaluated.is_evaluated is True
    assert evaluated.actual_price_at_eval == 1836.0
    assert evaluated.actual_price_change_pct == 2.0
    assert evaluated.actual_direction == "BULLISH"
    assert evaluated.is_direction_correct is True
    assert "CORRECT" in evaluated.evaluation_notes


def test_evaluate_single_prediction_incorrect_buy():
    pred = PredictionResult(
        signal_id=2,
        symbol="INFY",
        predicted_direction="BUY",
        predicted_confidence=80,
        price_at_prediction=1800.0,
        evaluation_horizon="INTRADAY",
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=False,
    )
    evaluated = evaluation_service.evaluate_single_prediction(pred, current_price=1764.0)
    assert evaluated.is_evaluated is True
    assert evaluated.actual_price_change_pct == -2.0
    assert evaluated.actual_direction == "BEARISH"
    assert evaluated.is_direction_correct is False
    assert "INCORRECT" in evaluated.evaluation_notes


def test_evaluate_single_prediction_correct_sell():
    pred = PredictionResult(
        signal_id=3,
        symbol="TATAMOTORS",
        predicted_direction="SELL",
        predicted_confidence=70,
        price_at_prediction=980.0,
        evaluation_horizon="1_DAY",
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=False,
    )
    evaluated = evaluation_service.evaluate_single_prediction(pred, current_price=960.0)
    assert evaluated.is_evaluated is True
    assert evaluated.actual_direction == "BEARISH"
    assert evaluated.is_direction_correct is True


def test_evaluate_single_prediction_neutral_stayed_flat():
    pred = PredictionResult(
        signal_id=4,
        symbol="ITC",
        predicted_direction="NO_TRADE",
        predicted_confidence=50,
        price_at_prediction=490.0,
        evaluation_horizon="INTRADAY",
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=False,
    )
    evaluated = evaluation_service.evaluate_single_prediction(pred, current_price=491.5)
    assert evaluated.is_evaluated is True
    assert evaluated.is_direction_correct is True


def test_calculate_brier_score():
    # Empty list defaults to baseline 0.25
    assert evaluation_service.calculate_brier_score([]) == 0.25

    # Prediction 1: 80% confidence, correct -> (0.8 - 1.0)^2 = 0.04
    # Prediction 2: 70% confidence, incorrect -> (0.7 - 0.0)^2 = 0.49
    # Expected mean = (0.04 + 0.49) / 2 = 0.265
    p1 = PredictionResult(
        signal_id=10,
        symbol="SBIN",
        predicted_direction="BUY",
        predicted_confidence=80,
        price_at_prediction=800.0,
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=True,
        is_direction_correct=True,
    )
    p2 = PredictionResult(
        signal_id=11,
        symbol="RELIANCE",
        predicted_direction="BUY",
        predicted_confidence=70,
        price_at_prediction=2900.0,
        evaluation_due_at=datetime.now(timezone.utc),
        is_evaluated=True,
        is_direction_correct=False,
    )
    score = evaluation_service.calculate_brier_score([p1, p2])
    assert abs(score - 0.265) < 0.001


@pytest.mark.asyncio
async def test_evaluate_pending_predictions_batch(db_session):
    sig = Signal(
        symbol="HDFCBANK",
        direction="BUY",
        entry_zone="₹1670 - ₹1690",
        entry_price=1680.0,
        stop_loss=1650.0,
        target_1=1730.0,
        confidence=75,
        entry_time_window="09:30 - 14:30",
        exit_time_window="15:15",
        status="PENDING",
        reasoning="Test signal",
        invalidated_if="None",
        technical_confirmation="CONFIRMED",
    )
    db_session.add(sig)
    await db_session.commit()
    await db_session.refresh(sig)

    # Register prediction due in the past
    pred = PredictionResult(
        signal_id=sig.id,
        symbol="HDFCBANK",
        predicted_direction="BUY",
        predicted_confidence=75,
        price_at_prediction=1680.0,
        evaluation_horizon="INTRADAY",
        evaluation_due_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        is_evaluated=False,
    )
    db_session.add(pred)
    await db_session.commit()

    # Run batch evaluation
    result = await evaluation_service.evaluate_pending_predictions(db_session, force_all=False)
    assert result["status"] == "success"
    assert result["evaluated_count"] >= 1

    # Verify prediction is now evaluated in db
    await db_session.refresh(pred)
    assert pred.is_evaluated is True
    assert pred.actual_price_at_eval is not None
    assert pred.evaluated_at is not None


@pytest.mark.asyncio
async def test_get_performance_summary_metrics(db_session):
    summary = await evaluation_service.get_performance_summary(db_session)
    assert "total_evaluated_predictions" in summary
    assert "directional_accuracy_pct" in summary
    assert "brier_score" in summary
    assert "profit_factor" in summary
    assert "confidence_calibration_tiers" in summary
    assert "sector_accuracy" in summary


@pytest.mark.asyncio
async def test_run_historical_backtest(db_session):
    result = await evaluation_service.run_historical_backtest(
        db=db_session,
        symbols=["RELIANCE", "TCS", "INFY"],
        period_days=60
    )
    assert result["status"] == "success"
    assert result["total_trades_simulated"] >= 0
    assert "win_rate_pct" in result
    assert "profit_factor" in result
    assert "max_drawdown_pct" in result
    assert "brier_score" in result
    assert "disclaimer" in result


@pytest.mark.asyncio
async def test_performance_api_endpoints(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger evaluation endpoint
        eval_resp = await client.post("/api/v1/performance/evaluate?force_all=true")
        assert eval_resp.status_code == 200
        eval_data = eval_resp.json()
        assert eval_data["success"] is True

        # 2. Get summary endpoint
        sum_resp = await client.get("/api/v1/performance/summary")
        assert sum_resp.status_code == 200
        sum_data = sum_resp.json()
        assert sum_data["success"] is True
        assert "directional_accuracy_pct" in sum_data["data"]
        assert "brier_score" in sum_data["data"]

        # 3. List predictions endpoint
        list_resp = await client.get("/api/v1/performance/predictions?page=1&page_size=10")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["success"] is True
        assert "items" in list_data

        # 4. Trigger backtest endpoint
        bt_resp = await client.post("/api/v1/performance/backtest?period_days=45&symbols=RELIANCE,TCS")
        assert bt_resp.status_code == 200
        bt_data = bt_resp.json()
        assert bt_data["success"] is True
        assert bt_data["data"]["status"] == "success"
        assert "win_rate_pct" in bt_data["data"]
