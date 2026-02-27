import subprocess
import tempfile
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .models import Challenge
from django.views.decorators.cache import never_cache
@never_cache
def challenge_view(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    master_flag = None

    prev_challenge = Challenge.objects.filter(id__lt=challenge.id).order_by('-id').first()
    next_challenge = Challenge.objects.filter(id__gt=challenge.id).order_by('id').first()

    solved_list = request.session.get("solved_challenges", [])

    if request.method == "POST":
        user_code = request.POST.get("code")
        result_message = ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
            temp.write(user_code.encode())
            temp.close()

        try:
            result = subprocess.run(
                ["python", temp.name],
                capture_output=True,
                text=True,
                timeout=3
            )

            output = result.stdout.strip()
            expected = challenge.expected_output.strip()

            output_lines = [line.strip() for line in output.splitlines()]
            expected_lines = [line.strip() for line in expected.splitlines()]

            if output_lines == expected_lines:
                result_message = "Correct! ✅"

                if challenge.id not in solved_list:
                    solved_list.append(challenge.id)
                    request.session["solved_challenges"] = solved_list
            else:
                result_message = "Wrong answer. Try again!"

        except subprocess.TimeoutExpired:
            result_message = "Time limit exceeded!"
        except Exception as e:
            result_message = f"Error: {str(e)}"

        # ✅ Store result temporarily in session
        request.session["result_message"] = result_message

        # 🔥 Redirect to same page (this clears POST on refresh)
        return redirect("challenge", id=challenge.id)

    # GET request
    result_message = request.session.pop("result_message", "")

    total_challenges = Challenge.objects.count()
    if total_challenges > 0 and len(solved_list) == total_challenges:
        master_flag = settings.MASTER_FLAG

    return render(request, "runner/challenge.html", {
        "challenge": challenge,
        "result": result_message,
        "prev_challenge": prev_challenge,
        "next_challenge": next_challenge,
        "master_flag": master_flag,
    })


def index(request):
    return render(request, 'runner/index.html')