from rest_framework import serializers
from recommendation.models import PsychologicalTest

class PsychologicalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PsychologicalTest
        fields = '__all__'   # یا لیست فیلدهای مورد نیاز