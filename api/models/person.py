import datetime

import pytz
from django.db import models
from django.db.models import Prefetch

from api.models.photo import Photo
from api.models.user import User

utc = pytz.UTC


class Person(models.Model):
    UNKNOWN_PERSON_NAME = "Unknown - Other"
    KIND_USER = "USER"
    KIND_CLUSTER = "CLUSTER"
    KIND_UNKNOWN = "UNKNOWN"
    KIND_CHOICES = (
        (KIND_USER, "User Labelled"),
        (KIND_CLUSTER, "Cluster ID"),
        (KIND_UNKNOWN, "Unknown Person"),
    )
    name = models.CharField(blank=False, max_length=128)
    kind = models.CharField(choices=KIND_CHOICES, max_length=10)
    cover_photo = models.ForeignKey(
        Photo, related_name="person", on_delete=models.SET_NULL, blank=False, null=True
    )
    face_count = models.IntegerField(default=0)
    cluster_owner = models.ForeignKey(
        User,
        related_name="owner",
        on_delete=models.SET_NULL,
        default=None,
        null=True,
    )

    def __str__(self):
        return "%d" % self.id

    def _calculate_face_count(self):
        confidence_person = (
            User.objects.filter(id=self.cluster_owner.id).first().confidence_person
        )
        self.face_count = self.faces.filter(
            photo__hidden=False,
            photo__deleted=False,
            photo__owner=self.cluster_owner.id,
            person_label_probability__gte=confidence_person,
        ).count()
        self.save()

    def _set_default_cover_photo(self):
        if not self.cover_photo:
            self.cover_photo = self.faces.first().photo
            self.save()

    def get_photos(self, owner):
        faces = list(
            self.faces.prefetch_related(
                Prefetch(
                    "photo",
                    queryset=Photo.objects.exclude(image_hash=None)
                    .filter(hidden=False, owner=owner)
                    .order_by("-exif_timestamp")
                    .only(
                        "image_hash",
                        "exif_timestamp",
                        "rating",
                        "owner__id",
                        "public",
                        "hidden",
                    )
                    .prefetch_related("owner"),
                )
            )
        )

        photos = [face.photo for face in faces if hasattr(face.photo, "owner")]
        photos.sort(
            key=lambda x: x.exif_timestamp or utc.localize(datetime.datetime.min),
            reverse=True,
        )
        return photos


def get_unknown_person(owner: User = None):
    unknown_person: Person = Person.objects.get_or_create(
        name=Person.UNKNOWN_PERSON_NAME, cluster_owner=owner, kind=Person.KIND_UNKNOWN
    )[0]
    if unknown_person.kind != Person.KIND_UNKNOWN:
        unknown_person.kind = Person.KIND_UNKNOWN
        unknown_person.save()
    return unknown_person


def get_or_create_person(name, owner: User = None, kind: str = Person.KIND_UNKNOWN):
    return Person.objects.get_or_create(name=name, cluster_owner=owner, kind=kind)[0]
