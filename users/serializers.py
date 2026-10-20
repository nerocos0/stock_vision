from rest_framework import serializers

from django.contrib.auth.models import User
from .models import FavoriteInstrument

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] == data['password2']:
            return data
        else:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})

    def create(self, validated_data):
        validated_data.pop('password2')

        username = validated_data['username']
        password = validated_data['password']

        return User.objects.create_user(username=username, password=password)


class FavoriteInstrumentSerializer(serializers.ModelSerializer):
    instrument_code = serializers.CharField(source='instrument.code', read_only=True)

    class Meta:
        model = FavoriteInstrument
        fields = ['id', 'instrument', 'instrument_code']
        extra_kwargs = {
            'instrument': {'write_only': True}
        }