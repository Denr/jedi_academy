from django.core.exceptions import ValidationError
from django.core.validators import (MinValueValidator, MaxValueValidator)
from django.db import models
from django.shortcuts import get_object_or_404


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    planet = models.ForeignKey('Planet', on_delete=models.CASCADE)
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(20), MaxValueValidator(100)])
    email = models.EmailField(unique=True)
    jedi = models.ForeignKey('Jedi', on_delete=models.CASCADE, null=True, related_name='candidates')

    # Переопределяем метод чтобы у Джедая не было больше 3 падаванов
    def save(self, *args, **kwargs):
        padawans_count = Jedi.objects.get(planet=self.planet).candidates.count()
        if padawans_count >= 3:
            raise ValidationError(message='К сожалению в данный момент мы не можем Вас принять.'
                                          'У Джедая с Вашей планеты уже больше 3 падаванов.')
        super(Candidate, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Jedi(models.Model):
    name = models.CharField(max_length=100)
    planet = models.ForeignKey('Planet', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Planet(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    name = models.CharField(max_length=100)
    code = models.PositiveIntegerField(unique=True, default=0)

    def __str__(self):
        return self.name


class Question(models.Model):
    question_text = models.CharField(max_length=200)

    def __str__(self):
        return self.question_text


class Answer(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    answer_text = models.BooleanField()
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE, related_name='answers')


# Создаем дополнительный менеджер для модели Challenge и пишем метод для получения следущего вопроса
class ChallengeManager(models.Manager):
    def get_next_question(self, order_code, question_pk):
        questions_pk = []
        for question in get_object_or_404(Challenge, order__code=order_code).questions.all():
            questions_pk.append(question.pk)
        try:
            next = questions_pk[questions_pk.index(question_pk) + 1]
        except IndexError:
            next = 'done'
        return next


class Challenge(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)
    objects = models.Manager()
    challenge_manager = ChallengeManager()

    def __str__(self):
        return 'Challenge with order code {}.'.format(self.order.code)
