from recommendation.models import PsychologicalTest, TestScale

def get_test_by_id(test_id: int):
    return PsychologicalTest.objects.filter(id=test_id).first()

def get_scale_by_id(scale_id: int, test):
    return TestScale.objects.filter(id=scale_id, test=test).first()