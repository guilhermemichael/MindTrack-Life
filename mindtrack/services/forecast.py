def predict_mood(values: list[float], horizon_days: int = 7):
    if len(values) < 3:
        return {
            "predicted_mood": None,
            "horizon_days": horizon_days,
            "message": "Registre pelo menos 3 dias para liberar a previsao.",
            "direction": "stable",
        }

    trend = (values[-1] - values[0]) / max(len(values) - 1, 1)
    predicted = round(max(1, min(10, values[-1] + trend * horizon_days)), 2)

    if predicted > values[-1] + 0.2:
        direction = "up"
    elif predicted < values[-1] - 0.2:
        direction = "down"
    else:
        direction = "stable"

    return {
        "predicted_mood": predicted,
        "horizon_days": horizon_days,
        "message": f"Se continuar assim, seu humor medio pode chegar a {predicted} em {horizon_days} dias.",
        "direction": direction,
    }
