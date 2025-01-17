from django.contrib import admin

from .models import (
    AlbumAuto,
    AlbumDate,
    AlbumPlace,
    AlbumThing,
    AlbumUser,
    Cluster,
    Face,
    File,
    LongRunningJob,
    Person,
    Photo,
    User,
)


class FaceDeduplication(admin.ModelAdmin):
    actions = ["deduplicate_faces"]

    def deduplicate_faces(self, request, queryset):
        for photo in queryset:
            # Get all faces in the photo
            faces = Face.objects.filter(photo=photo)
            # Check if there are any faces which have similar bounding boxes
            for face in faces:
                margin = int((face.location_right - face.location_left) * 0.05)
                similar_faces = Face.objects.filter(
                    photo=self,
                    location_top__lte=face.location_top + margin,
                    location_top__gte=face.location_top - margin,
                    location_right__lte=face.location_right + margin,
                    location_right__gte=face.location_right - margin,
                    location_bottom__lte=face.location_bottom + margin,
                    location_bottom__gte=face.location_bottom - margin,
                    location_left__lte=face.location_left + margin,
                    location_left__gte=face.location_left - margin,
                )
                if len(similar_faces) > 1:
                    # Divide between faces with a person label and faces without
                    faces_with_person_label = []
                    faces_without_person_label = []
                    for similar_face in similar_faces:
                        if similar_face.person:
                            faces_with_person_label.append(similar_face)
                        else:
                            faces_without_person_label.append(similar_face)
                    # If there are faces with a person label, keep the first one and delete the rest
                    for similar_face in faces_with_person_label[1:]:
                        similar_face.delete()
                    # If there are faces with a person label, delete all of them
                    if len(faces_with_person_label) > 0:
                        for similar_face in faces_without_person_label:
                            similar_face.delete()
                    # Otherwise, keep the first face and delete the rest
                    else:
                        for similar_face in faces_without_person_label[1:]:
                            similar_face.delete()


# Register your models here.
admin.site.register(Photo, FaceDeduplication)
admin.site.register(Person)
admin.site.register(Face)
admin.site.register(AlbumAuto)
admin.site.register(AlbumUser)
admin.site.register(AlbumThing)
admin.site.register(AlbumDate)
admin.site.register(AlbumPlace)
admin.site.register(Cluster)
admin.site.register(LongRunningJob)
admin.site.register(File)
admin.site.register(User)
