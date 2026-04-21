def generate_insights(analytics: dict, forecast: dict) -> list[dict]:
    insights = []
    summary = analytics["summary"]
    correlations = analytics["correlations"]
    comparisons = analytics["comparisons"]
    gamification = analytics["gamification"]

    if summary["avg_sleep"] < 6:
        insights.append(
            {
                "level": "alert",
                "title": "Sono abaixo do ideal",
                "message": "Voce esta dormindo menos que o ideal. Isso tende a pressionar humor, foco e energia.",
            }
        )

    if correlations["sleep_mood"] is not None and correlations["sleep_mood"] > 0.5:
        insights.append(
            {
                "level": "success",
                "title": "Sono melhora seu humor",
                "message": "Os dados mostram que seu humor sobe quando voce dorme melhor. Priorizar descanso pode render rapido.",
            }
        )

    if correlations["study_progress"] is not None and correlations["study_progress"] > 0.45:
        insights.append(
            {
                "level": "success",
                "title": "Estudo gera progresso",
                "message": "Seu progresso responde bem a dias com mais estudo. Vale proteger esse bloco na rotina.",
            }
        )

    if comparisons["progress"]["delta"] < -5:
        insights.append(
            {
                "level": "warning",
                "title": "Queda recente de execucao",
                "message": "Seu progresso caiu na comparacao com a semana anterior. Ajustes pequenos agora evitam uma sequencia ruim.",
            }
        )

    if summary["current_streak"] >= 3:
        insights.append(
            {
                "level": "success",
                "title": "Consistencia real",
                "message": f"Voce esta ha {summary['current_streak']} dias consistente. Esse e o tipo de sinal que muda resultado no longo prazo.",
            }
        )

    if gamification["days_to_new_record"] == 1 and summary["best_streak"] > 0:
        insights.append(
            {
                "level": "info",
                "title": "Recorde perto",
                "message": "Falta 1 dia para bater seu recorde de consistencia. Vale simplificar o proximo passo e nao quebrar a sequencia.",
            }
        )

    if forecast["predicted_mood"] is not None:
        tone = "success" if forecast["direction"] == "up" else "warning" if forecast["direction"] == "down" else "info"
        insights.append(
            {
                "level": tone,
                "title": "Previsao de humor",
                "message": forecast["message"],
            }
        )

    if not insights:
        insights.append(
            {
                "level": "info",
                "title": "Padrao em formacao",
                "message": "Continue registrando seus dias. O sistema ja esta coletando sinais para ficar cada vez mais preciso.",
            }
        )

    return insights[:6]
