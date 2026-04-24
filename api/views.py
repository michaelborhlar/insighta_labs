import requests
from datetime import datetime, timezone
from django.http import JsonResponse
from django.views import View

GENDERIZE_URL = "https://api.genderize.io/"


def error_response(status, message):
    return JsonResponse({"status": "error", "message": message}, status=status)


class ClassifyView(View):
    def get(self, request):
        name = request.GET.get("name")

        # 400 – missing or empty
        if name is None or name == "":
            return error_response(400, "Missing or empty name parameter")

        # 422 – query params are always strings in Django, but guard against
        # someone passing a list-style param e.g. ?name[]=foo
        if not isinstance(name, str):
            return error_response(422, "name must be a string")

        try:
            upstream = requests.get(
                GENDERIZE_URL,
                params={"name": name},
                timeout=5,
            )
        except requests.exceptions.Timeout:
            return error_response(502, "Upstream API timed out")
        except requests.exceptions.RequestException:
            return error_response(502, "Upstream API returned an error")

        if not upstream.ok:
            return error_response(502, "Upstream API returned an error")

        try:
            data = upstream.json()
        except ValueError:
            return error_response(500, "Internal server error")

        # Edge case: no prediction available
        if data.get("gender") is None or data.get("count") == 0:
            return error_response(
                200,
                "No prediction available for the provided name",
            )

        gender = data["gender"]
        probability = data["probability"]
        sample_size = data["count"]           # rename count → sample_size
        is_confident = probability >= 0.7 and sample_size >= 100
        processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        return JsonResponse({
            "status": "success",
            "data": {
                "name": data["name"],
                "gender": gender,
                "probability": probability,
                "sample_size": sample_size,
                "is_confident": is_confident,
                "processed_at": processed_at,
            },
        }, status=200)
