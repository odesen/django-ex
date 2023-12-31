from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .forms import PollsAuthenticationForm
from .models import Choice, Question, Vote


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by(
            "-pub_date"
        )[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= Choice.objects.filter(question=self.kwargs.get("pk")).aggregate(
            vote_count=Count("vote")
        )
        counts = (
            Choice.objects.filter(question=self.kwargs.get("pk"))
            .values("choice_text")
            .annotate(
                choice_count=Count("vote"),
            )
            .order_by("-choice_count")
        )
        for count in counts:
            count["choice_percent"] = (
                count["choice_count"] / context["vote_count"]
            ) * 100
        context["choice_count"] = counts
        return context


@login_required(login_url="/polls/login/")
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        Vote.objects.create(
            user=request.user, choice=selected_choice, vote_date=timezone.now()
        )
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class PollsLoginView(LoginView):
    template_name = "polls/login.html"
    authentication_form = PollsAuthenticationForm
    redirect_authenticated_user = True


class PollsLogoutView(LogoutView):
    template_name = "polls/logout.html"
