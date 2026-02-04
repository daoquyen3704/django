from rest_framework import serializers
from django.contrib.auth import get_user_model # lấy model user tùy chỉnh 

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'bio', 'facebook', 'youtube', 'instagram', 'profile_picture')
        extra_kwargs = {'password': {'write_only': True}} # chỉ cho phép ghi mật khẩu, không đọc, không trả về trong response
    
    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        first_name = validated_data.get("first_name", "")        
        last_name = validated_data.get("last_name", "")
        password = validated_data["password"]

        user = get_user_model() # lấy ra user
        new_user = user.objects.create(email=email, username=username, first_name=first_name, last_name=last_name)
        new_user.set_password(password) # mã hóa mật khẩu
        new_user.save() # lưu user mới vào database
        return new_user
    

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'bio', 'facebook', 'youtube', 'instagram', 'profile_picture')
        read_only_fields = ('id', 'username', 'email') # chỉ cho phép đọc các trường này, không được sửa đổi



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
