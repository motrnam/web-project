from django.contrib.auth import get_user_model
from rest_framework import serializers

from case.models import Case, RequestCheck, RegisterComplain
UserModel = get_user_model()

class RegisterComplainSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = RegisterComplain
        fields = '__all__'
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at', 'status' , 'TTL']
        

class RequestCheckSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = RequestCheck
        fields = '__all__'
        read_only_fields = ['id' , 'request', 'checked_by','created_at' , 'check_status']
        
class CaseSerializers(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = '__all__'
        read_only_fields = ['id', 'request', 'petrol_creator', 'created_at']