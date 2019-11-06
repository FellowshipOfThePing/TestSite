from django.views.generic import DetailView, FormView
from django.views.generic.list import MultipleObjectMixin
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, HttpResponseRedirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from users.models import Profile
from users.forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import Question, QuestionCopy, Choice, ChoiceCopy



def startpage(request):
    """Display the Startpage of the site.
    
    If user is already logged in, redirect to profile view.
    """
    if request.user.is_authenticated:
        return redirect('profile', test_type='ALL')
    return render(request, 'home/startpage.html')


def about(request):
    """Display the About page"""
    return render(request, 'home/about.html')


def study(request, test_type):
    """Display the Study page.
    
    Describes study options for user. Links to Quiz Questions, Practice Tests, and Stats page.
    """

    # Stores queryset of all previously answered questions
    questionsAnswered = request.user.profile.questions_answered.filter(test_type=test_type).all()

    # Stores orderIds of last question user answered, and next question user has not answered,
    # so study links will only send the user to new questions.
    lastQuestionId = questionsAnswered.last()
    if lastQuestionId:
        lastQuestionId = lastQuestionId.originalOrderId
        newQuestionId = questionsAnswered.last().originalOrderId + 1
    else:
        newQuestionId = 1

    # If user has already answered all questions within the given category, study links will redirect to profile page.
    lastPossibleQuestionId = Question.objects.filter(test_type=test_type).last().orderId
    if newQuestionId is None:
        newQuestionId = 1

    # Stores user/test_type information to be rendered in template.
    context = {
        'test_type': test_type,
        'newQuestionId': newQuestionId,
        'lastQuestionId': lastQuestionId,
        'lastPossibleQuestionId': lastPossibleQuestionId
    }
    return render(request, 'home/study.html', context)



def stats(request, test_type, subject):
    """Displays the Stats page.
    
    Filters user history by given test_type and subject values.

    Stats filtered by Test:
        Total Answer Accuracy (Number Answered Correct/Wrong)
        Question Subject Distribution (Number of Question Answered)
        Accuracy Over Time (Percentage)
        Study Recommendations (Percentage)

    Stats filtered by Subject:
        Total Answer Accuracy (Number Answered Correct/Wrong)
        Accuracy Over Time (Percentage)
    """

    # Default Iterables
    TEST_TYPES = ['ALL', 'SAT', 'ACT', 'GRE']
    SUBJECTS = ['Math', 'Reading', 'Science', 'English', 'Quantitative', 'Verbal']


    # Modify iterables based on given test_type
    if test_type == 'ALL':
        questions = request.user.profile.questions_answered.all()
    elif test_type == 'SAT':
        questions = request.user.profile.questions_answered.filter(test_type=test_type).all()
        SUBJECTS = ['Math', 'Reading']
    elif test_type == 'ACT':
        questions = request.user.profile.questions_answered.filter(test_type=test_type).all()
        SUBJECTS = ['Science', 'English']
    else:
        questions = request.user.profile.questions_answered.filter(test_type=test_type).all()
        SUBJECTS = ['Quantitative', 'Verbal']


    # ------- Stats Filtered by Test ------- #


    # Truncate Improvement Line Chart Dates
    testImprovementDates = []
    for i in range(len(questions)):
        if i == 0 or i == len(questions) - 1:
            testImprovementDates.append(str(questions[i].date_answered)[5:10])
        else:
            testImprovementDates.append("")


    # Create Improvement Line Chart List
    if test_type == 'ALL':
        testAccuracyList = [question.currentGeneralAccuracy for question in questions]
    else:
        testAccuracyList = [question.currentTestAccuracy for question in questions]


    # Dictionary for Context
    by_test = {
        # Total Answer Accuracy (Pie Chart)
        'questionsCorrect': len(questions.filter(answeredCorrectly=True).all()),
        'questionsWrong': len(questions.filter(answeredCorrectly=False).all()),

        # Subject Distribution (Bar Chart)
        'subjectDistribution': [len(questions.filter(subject=s).all()) for s in SUBJECTS],

        # Accuracy Over Time (Line Chart)
        'improvementDates': testImprovementDates,
        'improvementNodes': testAccuracyList
    }


    # ------- Stats Filtered by Subject ------- #


    # Questions Filtered By Subject
    questionsBySubject = questions.filter(subject=subject).all()


    # Build list of dates for question answers (Rethink so these values are stored in submit view)
    subjectImprovementDates = []
    for i in range(len(questionsBySubject)):
        if i == 0 or i == len(questionsBySubject) - 1:
            subjectImprovementDates.append(str(questionsBySubject[i].date_answered)[5:10])
        else:
            subjectImprovementDates.append("")


    by_subject = {
        # Total Accuracy (Pie Chart)
        'questionsCorrect': len(questionsBySubject.filter(answeredCorrectly=True).all()),
        'questionsWrong': len(questionsBySubject.filter(answeredCorrectly=False).all()),

        # Accuracy Over Time (Line Chart)
        'improvementDates': subjectImprovementDates,
        'improvementNodes': [question.currentSubjectAccuracy for question in questionsBySubject],

        # Recommendations (Placeholder for Now) (Bar Chart)
    }


    # Iterables for displaying test/subject tabs
    test_dict = {
        'ALL': ['Math', 'Reading', 'Science', 'English', 'Quantitative', 'Verbal'],
        'SAT': ['Math', 'Reading'],
        'ACT': ['Science', 'English'],
        'GRE': ['Quantitative', 'Verbal']
    }


    question_info = {
        "all_subjects": SUBJECTS
    }


    # Store user/test_type/subject information to be rendered in template.
    context = {
        "test_type": test_type,
        "subject": subject,
        "by_test": by_test,
        "by_subject": by_subject,
        "all_subjects": SUBJECTS,
        "test_dict": test_dict
    }


    return render(request, 'home/stats.html', context)



@login_required
def QuestionDetailView(request, test_type, orderId):
    """Display Question prompt/choices. Serves as primary interface for answering quiz/test questions."""

    # If user runs out of Questions, return 404. Should rarely happen, given redirection logic in view template.
    try:
        question = Question.objects.get(test_type=test_type, orderId=orderId)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")

    # Store question information to be rendered in template.
    context = {
        'question': Question.objects.filter(test_type=test_type, orderId=orderId).first(),
        'nextQuestion': Question.objects.filter(test_type=test_type, orderId=orderId).first().orderId + 1
    }

    return render(request, 'home/question_detail.html', context)



@login_required
def SubmitAnswer(request, test_type, orderId):
    """Processes user answer and copies Question info be stored in profile history."""

    # Get Instance of Question Answered
    question = get_object_or_404(Question, test_type=test_type, orderId=orderId)

    # Retrieve answer submitted, if none, return 404 with error message
    try:
        selected_choice = question.choices.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'home/question_detail.html', 
        {
            'question': question,
            'error_message': 'You didn\'t selection an answer',
        })

    
    # If submission is successful:
    else:
        student = request.user.profile

        # Store original Question & Question-Choices to reference later in function
        newChoiceList = question.choices.all()

        # Create new QuestionCopy instance based on attributes of current Question instance
        questionCopy = QuestionCopy.create(request.user.profile, question.test_type, question.subject, question.title, question.title, question.image, question.hint,
            question.orderId)
        questionCopy.save()

        # Modify Profile and new QuestionCopy fields to reflect question submission.
        # If user answered correctly:
        if selected_choice.correct:
            student.correctAnswers += 1
            student.save()
            questionCopy.answeredCorrectly = True
            questionCopy.numberCorrectGeneral += 1
            questionCopy.numberCorrectOfTestType += 1
            questionCopy.numberCorrectOfSubjectType += 1

        # If user answered incorrectly:
        else:
            student.wrongAnswers += 1
            student.save()
            questionCopy.answeredCorrectly = False
            questionCopy.numberWrongGeneral += 1
            questionCopy.numberWrongOfTestType += 1
            questionCopy.numberWrongOfSubjectType += 1

        # Copy choices to store in new QuestionCopy instance.
        for i, choice in enumerate(newChoiceList):
            if choice == selected_choice:
                answerIndex = i + 1
            newChoice = ChoiceCopy.create(choice.choice_text, questionCopy, choice.correct)
            newChoice.save()

        # Modify questionCopy userAccuracy fields to reflect question submission.
        questionCopy.userAnswer = answerIndex

        numberRight = questionCopy.numberCorrectGeneral
        numberWrong = questionCopy.numberWrongGeneral

        numberRightTest = questionCopy.numberCorrectOfTestType
        numberWrongTest = questionCopy.numberWrongOfTestType

        numberRightSubject = questionCopy.numberCorrectOfSubjectType
        numberWrongSubject = questionCopy.numberWrongOfSubjectType

        questionCopy.currentGeneralAccuracy = 100 * (numberRight / (numberRight + numberWrong))
        questionCopy.currentTestAccuracy = 100 * (numberRightTest / (numberRightTest + numberWrongTest))
        questionCopy.currentSubjectAccuracy = 100 * (numberRightSubject / (numberRightSubject + numberWrongSubject))

        questionCopy.save()

        # Add to profile history
        student.questions_answered.add(questionCopy)

        # Redirect to Question Result view
        return HttpResponseRedirect(reverse('question-result', kwargs={'test_type': question.test_type, 'orderId': questionCopy.originalOrderId}))



@login_required
def QuestionResultView(request, test_type, orderId):
    """Display Question prompt/choices with user feedback. 

    Serves as primary interface for immediate user feedback.
    
    Feedback includes:
        Result: Whether the user answered the question correctly or not.
        Advice: Suggested learning strategies for the question. (Only displays when user is incorrect).
    """

    # Get Instance of Question Answered
    question = get_object_or_404(Question, test_type=test_type, orderId=orderId)

    # Retrieve last answered question from profile history
    answer = request.user.profile.questions_answered.last().userAnswer

    # Track if user was correct or not
    solved = False

    # Determine user correctness
    for i, choice in enumerate(question.choices.all()):
        if choice.correct and (i == answer - 1):
            solved = True

    # Store question/answer information to be rendered in template.
    context = {
        'question': question,
        'nextQuestion': question.orderId + 1,
        'lastQuestionId': Question.objects.filter(test_type=test_type).last().orderId,
        'answer': answer,
        'solved': solved
    }

    return render(request, 'home/question_result.html', context)


@login_required
def QuestionReview(request, username, copyId):
    """Display Question Review Page.
    
    Contains QuestionCopy information:
        Original Question Information (Image, Prompt, Choices, etc)
        Selected Choice
        User Correctness

    Links to previous/next questions in history, and to original Question to retry.
    """
    # Store reference to profile object
    userProfile = User.objects.filter(username=username).first().profile

    # Store reference to QuestionCopy object
    questionCopy = get_object_or_404(QuestionCopy, profile=userProfile, copyId=copyId)

    # Store question information to be rendered in template.
    context = {
        'question': questionCopy,
        'nextQuestion': questionCopy.copyId + 1,
        'lastQuestion': questionCopy.copyId - 1
    }
    return render(request, 'home/question_review.html', context)