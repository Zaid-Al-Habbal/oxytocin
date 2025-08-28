from rest_framework import serializers
from appointments.models import Attachment
from file_validator.models import DjangoFileValidator


class AttachmentUploadSerializer(serializers.Serializer):
    attachments = serializers.ListField(
        child=serializers.FileField(
            validators=[
            DjangoFileValidator(
                libraries=["python_magic", "filetype"],
                acceptable_mimes=[
                    "application/pdf",
                    "image/jpg",
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                    "image/bmp",
                ],
                acceptable_types=["archive", "image"],
                max_upload_file_size=7 * 1024 * 1024,  
            )
        ],
            ),
        max_length=5,
        allow_empty=False,
        write_only=True
    )


    def create(self, validated_data):
        appointment = self.context['appointment']
        files = validated_data['attachments']
        if Attachment.objects.filter(appointment=appointment).count() + len(files) > 5:
          raise serializers.ValidationError("You can upload a maximum of 5 attachments.") 
        for file in files:
            Attachment.objects.create(appointment=appointment, document=file)
        return {"details": "Attachments uploaded successfully"}


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'document', 'created_at']  # Add any other fields if needed