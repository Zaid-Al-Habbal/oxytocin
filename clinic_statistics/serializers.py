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