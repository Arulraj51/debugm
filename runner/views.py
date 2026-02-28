import subprocess
import tempfile
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .models import Challenge
from django.views.decorators.cache import never_cache


@never_cache
def challenge_view(request, id):
    challenge = get_object_or_404(Challenge, id=id)

    result_message = ""
    master_flag = None

    prev_challenge = Challenge.objects.filter(id__lt=challenge.id).order_by('-id').first()
    next_challenge = Challenge.objects.filter(id__gt=challenge.id).order_by('id').first()

    # Initialize session variables
    if "solved_list" not in request.session:
        request.session["solved_list"] = []

    if "solved_count" not in request.session:
        request.session["solved_count"] = 0



    if request.method == "POST" and "code" in request.POST:
        user_code = request.POST.get("code")

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

            output = result.stdout.strip().splitlines()
            expected = challenge.expected_output.strip().splitlines()

            if output == expected:
                result_message = "Correct! ✅"

                solved_list = request.session["solved_list"]

                # Add only if not already solved
                if challenge.id not in solved_list:
                    solved_list.append(challenge.id)
                    request.session["solved_list"] = solved_list
                    request.session["solved_count"] = len(solved_list)

                # 🎉 MASTER FLAG CONDITION
                if request.session["solved_count"] == 5:
                    master_flag = settings.MASTER_FLAG

            else:
                result_message = "Wrong answer. Try again!"

        except subprocess.TimeoutExpired:
            result_message = "Time limit exceeded!"
        except Exception as e:
            result_message = f"Error: {str(e)}"

    return render(request, "runner/challenge.html", {
        "challenge": challenge,
        "result": result_message,
        "prev_challenge": prev_challenge,
        "next_challenge": next_challenge,
        "master_flag": master_flag,
        "solved_count": request.session["solved_count"],
    })



def index(request):
    # 🔄 Reset progress whenever Start page is opened
    request.session["solved_list"] = []
    request.session["solved_count"] = 0

    return render(request, 'runner/index.html')