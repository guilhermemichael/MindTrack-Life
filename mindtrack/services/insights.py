from ..database import db
from ..models.insight import Insight


def generate_insights(analytics: dict, forecast: dict) -> list[dict]:
    insights = []
    summary = analytics["summary"]
    correlations = analytics["correlations"]
    comparisons = analytics["comparisons"]
    gamification = analytics["gamification"]
    db_architecture = analytics["database_architecture"]

    if summary["avg_sleep"] < 6:
        insights.append(
            {
                "level": "alert",
                "title": "Sono abaixo do ideal",
                "message": "Voce esta dormindo menos do que o ideal e isso esta puxando humor, energia e produtividade para baixo.",
                "insight_type": "system:sleep-risk",
                "metric_key": "avg_sleep",
                "metric_value": summary["avg_sleep"],
            }
        )

    if correlations["sleep_mood"] is not None and correlations["sleep_mood"] > 0.5:
        insights.append(
            {
                "level": "success",
                "title": "Seu humor responde ao sono",
                "message": "Existe uma relacao clara entre dormir melhor e se sentir melhor. Proteger 7h ou mais deve trazer retorno real.",
                "insight_type": "system:sleep-mood-correlation",
                "metric_key": "sleep_mood",
                "metric_value": correlations["sleep_mood"],
            }
        )

    if comparisons["productivity"]["delta"] > 5:
        insights.append(
            {
                "level": "success",
                "title": "Produtividade em alta",
                "message": f"Voce melhorou {comparisons['productivity']['delta']} pontos na produtividade em relacao a semana anterior.",
                "insight_type": "system:productivity-improvement",
                "metric_key": "productivity_delta",
                "metric_value": comparisons["productivity"]["delta"],
            }
        )

    if comparisons["progress"]["delta"] < -5:
        insights.append(
            {
                "level": "warning",
                "title": "Queda recente de progresso",
                "message": "Seu progresso caiu em relacao a semana anterior. Talvez seja hora de diminuir friccao e reduzir a carga por alguns dias.",
                "insight_type": "system:progress-drop",
                "metric_key": "progress_delta",
                "metric_value": comparisons["progress"]["delta"],
            }
        )

    if summary["current_streak"] >= 3:
        insights.append(
            {
                "level": "success",
                "title": "Consistencia visivel",
                "message": f"Voce esta ha {summary['current_streak']} dias consistente. Esse e o tipo de ritmo que construi resultado de verdade.",
                "insight_type": "system:streak",
                "metric_key": "current_streak",
                "metric_value": summary["current_streak"],
            }
        )

    if gamification["days_to_new_record"] == 1 and summary["best_streak"] > 0:
        insights.append(
            {
                "level": "info",
                "title": "Recorde ao alcance",
                "message": "Falta 1 dia para bater seu recorde. Vale simplificar o proximo dia e proteger a sequencia.",
                "insight_type": "system:record-close",
                "metric_key": "days_to_new_record",
                "metric_value": gamification["days_to_new_record"],
            }
        )

    if forecast["predicted_mood"] is not None:
        tone = "success" if forecast["direction"] == "up" else "warning" if forecast["direction"] == "down" else "info"
        insights.append(
            {
                "level": tone,
                "title": "Previsao de humor",
                "message": forecast["message"],
                "insight_type": "system:forecast",
                "metric_key": "predicted_mood",
                "metric_value": forecast["predicted_mood"],
            }
        )

    if db_architecture["weekly_summary_view"] is not None:
        insights.append(
            {
                "level": "info",
                "title": "Camada analitica ativa",
                "message": "Seu dashboard ja esta lendo resumo semanal orientado por banco, com snapshots e views analiticas prontos para escalar.",
                "insight_type": "system:database-summary",
                "metric_key": "total_entries",
                "metric_value": db_architecture["weekly_summary_view"].get("total_entries"),
            }
        )

    if not insights:
        insights.append(
            {
                "level": "info",
                "title": "Padrao em formacao",
                "message": "Continue registrando. O sistema ja esta montando uma base robusta para previsao e comparacoes mais fortes.",
                "insight_type": "system:baseline",
                "metric_key": None,
                "metric_value": None,
            }
        )

    return insights[:6]


def sync_persisted_insights(user_id: str, analytics: dict, forecast: dict) -> list[dict]:
    generated = generate_insights(analytics, forecast)
    Insight.query.filter_by(user_id=user_id).filter(Insight.insight_type.like("system:%")).delete(synchronize_session=False)
    for item in generated:
        db.session.add(
            Insight(
                user_id=user_id,
                insight_type=item["insight_type"],
                severity=item["level"],
                title=item["title"],
                message=item["message"],
                metric_key=item["metric_key"],
                metric_value=item["metric_value"],
            )
        )
    db.session.commit()
    return generated


def list_persisted_insights(user_id: str, limit: int = 20) -> list[Insight]:
    return (
        Insight.query.filter_by(user_id=user_id)
        .order_by(Insight.generated_at.desc())
        .limit(limit)
        .all()
    )
