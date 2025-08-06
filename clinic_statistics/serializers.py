from rest_framework import serializers


class NumOfStarsSerializer(serializers.Serializer):
    num_of_one_stars = serializers.IntegerField()
    num_of_two_stars = serializers.IntegerField()
    num_of_three_stars = serializers.IntegerField()
    num_of_four_stars = serializers.IntegerField()
    num_of_five_stars = serializers.IntegerField()
    

class IncomesDetailSerializer(serializers.Serializer):
    date = serializers.DateField()
    income_value = serializers.FloatField()
    
    
class PatientAgesRanges(serializers.Serializer):
    baby = serializers.IntegerField()
    child = serializers.IntegerField()
    young_adult = serializers.IntegerField()
    adult = serializers.IntegerField()
    elderly = serializers.IntegerField()
    
    
class StatisticsSerializer(serializers.Serializer):
    age_groups = PatientAgesRanges()
    
    most_common_visit_time_this_month = serializers.TimeField()
    num_of_new_patients_this_month = serializers.IntegerField()
    num_of_indebted_patients = serializers.IntegerField()
    total_dept = serializers.FloatField()