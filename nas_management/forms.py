from django import forms


class LogCSVUploadForm(forms.Form):
    """Form để upload file CSV log từ NAS"""
    nas = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label="NAS",
        help_text="Chọn NAS để gán logs"
    )
    csv_file = forms.FileField(
        required=True,
        label="File CSV",
        help_text="Chọn file CSV log export từ NAS (format: Level,Log,Time,User,Event)",
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import NASConfig
        self.fields['nas'].queryset = NASConfig.objects.filter(is_active=True)

