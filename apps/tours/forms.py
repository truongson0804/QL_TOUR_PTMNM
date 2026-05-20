from django import forms
from .models.tours import Tour

class TourAdminForm(forms.ModelForm):
    # Định nghĩa 2 ô nhập số thủ công
    lat_input = forms.FloatField(label="Vĩ độ", required=False)
    lon_input = forms.FloatField(label="Kinh độ", required=False)

    class Meta:
        model = Tour
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure description textarea gets the CKEditor class and bootstrap form-control
        if 'description' in self.fields:
            widget = self.fields['description'].widget
            existing = widget.attrs.get('class', '')
            classes = ' '.join(filter(None, [existing, 'form-control', 'ckeditor']))
            widget.attrs['class'] = classes

# Note: TourStop model and its admin form have been removed.