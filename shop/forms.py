from django import forms

from .models import Comments
#from snowpenguin.django.recaptcha3.fields import ReCaptchaField

class CommentForm(forms.ModelForm):
    #captcha = ReCaptchaField()
    class Meta:
        model = Comments
        #fields = ("name", "email", "text", "captcha")
        fields = ("id","name", "email", "text", )
        
        
