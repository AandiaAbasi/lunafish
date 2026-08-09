from rest_framework import serializers


class GuestClassCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    name = serializers.CharField(required=False, allow_blank=False, max_length=120, default='Teacher')


class GuestClassJoinSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    name = serializers.CharField(required=False, allow_blank=False, max_length=120, default='Guest')
